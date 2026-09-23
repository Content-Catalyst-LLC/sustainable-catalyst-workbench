import os
from fastapi.testclient import TestClient
from app.main import app
from app.v720 import SCHEMA, ROUTE_SCHEMA, CORE_WORKFLOW_CONTRACT, RUNTIME_ADAPTERS


def client(): return TestClient(app)


def test_manifest_catalog_status_and_capabilities_current_identity():
    c=client(); m=c.get('/execution/orchestrator/manifest'); assert m.status_code==200
    d=m.json(); assert d['schema']==SCHEMA and d['version']=='8.5.0'
    assert d['operationCount']>=60 and d['adapterCount']==len(RUNTIME_ADAPTERS)
    assert d['localAdapterCount']==10 and d['handoffPlanAdapterCount']==3
    assert d['coreWorkflowContract']==CORE_WORKFLOW_CONTRACT
    assert d['boundaries']['arbitraryRExecutionAuthorized'] is False
    cat=c.get('/execution/orchestrator/runtimes').json(); assert cat['adapterCount']==13
    assert any(x['key']=='external.julia' and x['mode']=='handoff_plan' and not x['available'] for x in cat['adapters'])
    s=c.get('/v720/status').json(); assert s['ok'] and s['version']=='8.5.0' and s['deterministicRouting'] is True
    caps=c.get('/capabilities').json(); assert caps['version']=='8.5.0'
    assert caps['coreIntegration']['scientificRuntimeOrchestrator'] is True
    assert 'scientific-runtime-orchestrator' in caps['capabilities']


def test_deterministic_routing_selects_specialist_adapters():
    c=client()
    cases={
        'math.compute':'workbench.symbolic',
        'numerical.integrate':'workbench.numerical',
        'simulation.dynamic':'workbench.simulation',
        'controls.pid':'workbench.controls',
        'measurement.calibrate':'workbench.measurement',
        'electronics.resistor-network':'workbench.electronics',
        'uncertainty.ensemble':'workbench.uncertainty',
        'predictive.forecast':'workbench.predictive',
        'forensics.trajectory':'workbench.forensics',
        'energy.execute-handoff':'workbench.energy',
    }
    for op,adapter in cases.items():
        a=c.post('/execution/orchestrator/route',json={'operation':op}).json()
        b=c.post('/execution/orchestrator/route',json={'operation':op}).json()
        assert a['schema']==ROUTE_SCHEMA and a['adapter']['key']==adapter and a['executable'] is True
        assert a['routeHash']==b['routeHash']


def test_preferred_runtime_must_support_category_and_plan_only_never_executes():
    c=client()
    bad=c.post('/execution/orchestrator/route',json={'operation':'math.compute','preferredRuntime':'workbench.numerical'})
    assert bad.status_code==422
    plan=c.post('/execution/orchestrator/route',json={'operation':'math.compute','preferredRuntime':'external.r','allowHandoffPlan':True})
    assert plan.status_code==200 and plan.json()['executable'] is False and plan.json()['handoffRequired'] is True
    blocked=c.post('/execution/orchestrator/execute',json={'operation':'math.compute','payload':{'expression':'2+2'},'preferredRuntime':'external.r','allowHandoffPlan':True})
    assert blocked.status_code==409


def test_orchestrated_execution_runs_v700_and_projects_v710_object():
    c=client(); r=c.post('/execution/orchestrator/execute',json={
        'operation':'math.compute','payload':{'expression':'6*7'},'projectRef':'project:v720','coreSessionId':'session:v720',
        'requestKey':'route-math','label':'Routed math','datasetRefs':['dataset:a'],'tags':['orchestrated']})
    assert r.status_code==200,r.text
    d=r.json(); assert d['route']['adapter']['key']=='workbench.symbolic'
    assert d['executionResult']['result']['result']['exactText']=='42'
    obj=d['executionObject']; assert obj['version']=='8.5.0' and obj['objectKind']=='single_execution'
    assert obj['inputs']['declaredPayload']=={'expression':'6*7'}
    assert obj['outputs'][0]['contentHash']==d['executionResult']['resultHash']
    assert obj['metadata']['orchestratorRoute']['routeHash']==d['route']['routeHash']
    assert d['automaticExternalDispatchPerformed'] is False


def test_orchestrated_workflow_preserves_routes_dependencies_and_object_graph():
    c=client(); r=c.post('/execution/orchestrator/workflow/run',json={
        'workflowKey':'route-flow','projectRef':'project:flow','steps':[
            {'stepId':'b','operation':'electronics.resistor-network','dependsOn':['a'],'payload':{'topology':'series','resistancesOhm':[10,20],'sourceVoltageV':3}},
            {'stepId':'a','operation':'math.compute','payload':{'expression':'10+5'}},
        ]})
    assert r.status_code==200,r.text
    d=r.json(); assert d['ok'] is True
    assert d['routes']['a']['adapter']['key']=='workbench.symbolic'
    assert d['routes']['b']['adapter']['key']=='workbench.electronics'
    assert d['workflowResult']['dependencyOrder']==['a','b']
    assert len(d['executionObject']['children'])==2 and len(d['executionObject']['dependencies']['edges'])==1
    assert d['externalRuntimeDispatchPerformed'] is False


def test_external_r_julia_ml_are_explicit_handoff_plans_only():
    c=client()
    for runtime in ('external.r','external.julia','external.ml'):
        r=c.post('/execution/orchestrator/external/plan',json={'runtime':runtime,'taskKey':'future-task','inputRefs':['dataset:x']})
        assert r.status_code==200
        d=r.json(); assert d['adapter']['key']==runtime and d['executionPerformed'] is False
        assert d['automaticExternalDispatchAuthorized'] is False and d['arbitraryCodeExecutionAuthorized'] is False


def _orchestrated(c):
    return c.post('/execution/orchestrator/execute',json={'operation':'math.compute','payload':{'expression':'1+2'},'projectRef':'project:core-plan','requestKey':'core-math'}).json()


def test_core_workflow_plan_two_phase_exact_contract_and_non_dispatching():
    c=client(); result=_orchestrated(c)
    first=c.post('/integration/core/runtime-orchestrator/workflow/plan',json={'orchestrationResult':result})
    assert first.status_code==200,first.text
    d=first.json(); assert d['coreWorkflowContract']==CORE_WORKFLOW_CONTRACT
    assert d['workflowRegistration']['path']=='/v1/research/workflows'
    assert d['workflowRegistration']['data']['workflow_type']=='engineering_analysis'
    assert d['coreWorkflowIdMustComeFromCore'] is True
    assert d['stageRegistrations']==[] and d['contextBindings']==[]
    assert d['automaticCoreDispatchAuthorized'] is False
    second=c.post('/integration/core/runtime-orchestrator/workflow/plan',json={'orchestrationResult':result,'coreWorkflowId':'core-workflow-1'})
    assert second.status_code==200,second.text
    p=second.json(); assert p['coreWorkflowIdProvided'] is True
    assert p['stageRegistrations'][0]['path']=='/v1/research/workflows/core-workflow-1/stages'
    assert p['stageRegistrations'][0]['data']['responsible_product']=='workbench'
    assert p['contextBindings'][0]['path']=='/v1/research/workflows/core-workflow-1/context-bindings'
    assert p['contextBindings'][0]['data']['object_type']=='execution'
    assert p['eventRegistrations'][0]['path']=='/v1/research/workflows/core-workflow-1/events'
    assert p['coreExecutesSpecialistWork'] is False and p['coreInfersStageCompletion'] is False


def test_core_route_token_boundary(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret720')
    c=client(); result=_orchestrated(c)
    denied=c.post('/integration/core/runtime-orchestrator/workflow/plan',json={'orchestrationResult':result}); assert denied.status_code==401
    ok=c.post('/integration/core/runtime-orchestrator/workflow/plan',headers={'X-SC-Service-Token':'secret720'},json={'orchestrationResult':result})
    assert ok.status_code==200 and ok.json()['version']=='8.5.0'

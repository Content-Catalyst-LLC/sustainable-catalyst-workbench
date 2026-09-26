from fastapi.testclient import TestClient
from app.main import app
from app.v770 import SCHEMA, RESULT_SCHEMA_V770, CORE_COMPUTATION_LINEAGE_CONTRACT


def c(): return TestClient(app)


def space():
    return {
        'designSpaceKey':'beam-design',
        'variables':[
            {'variableKey':'x','lowerBound':0,'upperBound':4,'initial':1,'gridPoints':5},
            {'variableKey':'y','lowerBound':0,'upperBound':4,'initial':1,'gridPoints':5},
        ],
        'objectives':[
            {'objectiveKey':'cost','expression':'x**2 + y**2','goal':'minimize','weight':1},
            {'objectiveKey':'performance','expression':'x + 2*y','goal':'maximize','weight':0.2},
        ],
        'constraints':[{'constraintKey':'minimum-performance','expression':'x+y','relation':'>=','rhs':1}],
    }


def test_manifest_status_capabilities():
    cl=c(); m=cl.get('/design-space/manifest'); assert m.status_code==200
    d=m.json(); assert d['schema']==SCHEMA and d['version']=='9.9.0' and d['capabilities']['paretoFrontierExtraction']
    s=cl.get('/v770/status').json(); assert s['ok'] and s['paretoFrontier'] and s['automaticWinnerSelection'] is False
    caps=cl.get('/capabilities').json(); assert caps['version']=='9.9.0' and caps['coreIntegration']['optimizationDesignSpaceRuntime'] is True


def test_point_evaluation_and_constraint_feasibility():
    r=c().post('/design-space/evaluate',json={'designSpace':space(),'point':{'x':1,'y':1}}); assert r.status_code==200,r.text
    d=r.json(); assert d['feasible'] and len(d['objectives'])==2 and d['evaluationHash']
    bad=c().post('/design-space/evaluate',json={'designSpace':space(),'point':{'x':0,'y':0}}).json(); assert bad['feasible'] is False


def test_full_factorial_and_pareto_frontier():
    cl=c(); r=cl.post('/design-space/explore',json={'designSpace':space(),'maxPoints':100}); assert r.status_code==200,r.text
    e=r.json(); assert e['pointCount']==25 and e['feasibleCount']<25 and e['automaticBestDesignSelected'] is False
    p=cl.post('/design-space/pareto',json=e); assert p.status_code==200,p.text; d=p.json(); assert d['frontierPointCount']>=1 and d['automaticWinnerSelected'] is False


def test_constrained_multiobjective_optimization_execution_object():
    r=c().post('/design-space/optimize',json={'designSpace':space(),'requestKey':'opt-demo'}); assert r.status_code==200,r.text
    d=r.json(); assert d['schema']==RESULT_SCHEMA_V770 and d['executionObject']['objectKind']=='single_execution'
    assert d['result']['method']=='SLSQP' and d['result']['evaluation']['feasible'] is True and d['designRunHash']
    assert d['automaticObjectivePreferenceInferred'] is False and d['engineeringSafetyCertified'] is False


def test_validation_detects_tamper():
    cl=c(); d=cl.post('/design-space/optimize',json={'designSpace':space()}).json(); assert cl.post('/design-space/validate',json=d).json()['valid'] is True
    d['result']['weightedObjectiveValue']=999
    bad=cl.post('/design-space/validate',json=d).json(); assert bad['valid'] is False and 'design-run-hash-mismatch' in bad['reasons']


def test_workspace_binding_and_candidate_handoff_are_nonexecuting():
    cl=c(); ws=cl.post('/data-workspace/build',json={'workspaceKey':'dse-ws','variables':[],'parameterSets':[{'parameterSetKey':'bounds','parameters':[{'parameterKey':'initial-x','value':2.5,'unit':'m'}]}],'datasets':[],'assumptions':[]}).json()
    r=cl.post('/design-space/workspace-binding/plan',json={'workspace':ws,'designSpace':space(),'bindings':[{'sourceKind':'parameter','parameterSetKey':'bounds','sourceKey':'initial-x','designVariableKey':'x','bindField':'initial'}]}); assert r.status_code==200,r.text
    d=r.json(); assert d['designSpace']['variables'][0]['initial']==2.5 and d['executionPerformed'] is False
    h=cl.post('/design-space/candidate-handoff/plan',json={'candidatePoint':{'x':1.2,'y':2.0},'targetKind':'engineering','targetRequest':{'analysisKey':'mechanical.axial-member','inputs':{'force_n':1000,'area_m2':0.1}},'bindings':[{'variableKey':'x','targetField':'inputs.area_m2'}]}); assert h.status_code==200,h.text
    hp=h.json(); assert hp['preparedRequest']['inputs']['area_m2']==1.2 and hp['executionPerformed'] is False and hp['targetPath']=='/engineering/analyze'


def test_core_lineage_plan_is_two_phase(monkeypatch):
    cl=c(); result=cl.post('/design-space/optimize',json={'designSpace':space()}).json()
    first=cl.post('/integration/core/design-space-lineage/plan',json={'designResult':result}); assert first.status_code==200,first.text
    d=first.json(); assert d['coreComputationLineageContract']==CORE_COMPUTATION_LINEAGE_CONTRACT and d['coreExecutionIdMustComeFromCore'] and d['outputRegistrations']==[]
    second=cl.post('/integration/core/design-space-lineage/plan',json={'designResult':result,'coreExecutionId':'core-exec-770'}); assert second.status_code==200 and second.json()['outputRegistrations'][0]['path'].endswith('/outputs')
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret770')
    assert cl.post('/integration/core/design-space-lineage/plan',json={'designResult':result}).status_code==401
    ok=cl.post('/integration/core/design-space-lineage/plan',headers={'X-SC-Service-Token':'secret770'},json={'designResult':result}); assert ok.status_code==200 and ok.json()['automaticCoreDispatchAuthorized'] is False


def test_grid_limit_and_bounds_are_enforced():
    s=space(); s['variables'][0]['gridPoints']=31; s['variables'][1]['gridPoints']=31
    assert c().post('/design-space/explore',json={'designSpace':s,'maxPoints':100}).status_code==422
    assert c().post('/design-space/evaluate',json={'designSpace':space(),'point':{'x':99,'y':1}}).status_code==422

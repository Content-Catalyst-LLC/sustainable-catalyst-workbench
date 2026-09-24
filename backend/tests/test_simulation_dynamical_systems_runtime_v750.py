import os
from fastapi.testclient import TestClient
from app.main import app
from app.v750 import SCHEMA, SIMULATION_RESULT_SCHEMA, CORE_COMPUTATION_LINEAGE_CONTRACT

def client(): return TestClient(app)

def test_manifest_catalog_status_and_capabilities():
    c=client(); m=c.get('/simulations/manifest'); assert m.status_code==200
    d=m.json(); assert d['schema']==SCHEMA and d['version']=='8.11.0' and len(d['simulationKinds'])==4
    cat=c.get('/simulations/catalog').json(); assert cat['simulationCount']==4
    s=c.get('/v750/status').json(); assert s['ok'] and s['eventDetection'] and s['stabilityDiagnostics']
    caps=c.get('/capabilities').json(); assert caps['version']=='8.11.0' and caps['coreIntegration']['simulationDynamicalSystemsRuntime'] is True

def test_scalar_dynamic_trajectory_event_and_execution_object():
    c=client(); r=c.post('/simulations/run',json={'simulationKind':'scalar-dynamic','model':{'model_type':'first_order','solver':'rk4','initial_state':0,'input_value':10,'gain':1,'time_constant':2,'time_step':0.1,'duration':5},'events':[{'eventKey':'cross-5','stateKey':'state','threshold':5,'direction':'rising'}]})
    assert r.status_code==200,r.text; d=r.json(); assert d['schema']==SIMULATION_RESULT_SCHEMA
    assert d['trajectory']['sampleCount']>10 and d['events'][0]['eventKey']=='cross-5'
    assert d['diagnostics']['stability']['classification']=='asymptotically-stable'
    assert d['executionObject']['objectKind']=='single_execution' and d['simulationRunHash']

def test_linear_state_space_stability_diagnostics():
    c=client(); r=c.post('/simulations/run',json={'simulationKind':'linear-state-space','model':{'matrix_a':[[-1,0],[0,-2]],'initial_state':[1,2],'input_vector':[0,0],'state_names':['x','y'],'solver':'rk4','time_step':0.05,'duration':2}})
    assert r.status_code==200,r.text; d=r.json(); st=d['diagnostics']['stability']; assert st['classification']=='asymptotically-stable' and st['maxRealEigenvalue']<0
    assert set(d['trajectory']['finalState'])=={'x','y'}

def test_ode_ivp_uses_solver_runtime_and_normalizes_trajectory():
    c=client(); r=c.post('/simulations/run',json={'simulationKind':'ode-ivp','model':{'equations':['-k*x'],'stateNames':['x'],'initialValues':[1],'tMin':0,'tMax':2,'samples':41,'method':'RK45','parameters':{'k':1}}})
    assert r.status_code==200,r.text; d=r.json(); assert d['underlyingRun']['mode']=='solver-runtime'
    assert d['trajectory']['states'][0]['stateKey']=='x' and d['trajectory']['finalState']['x']<0.2
    assert d['diagnostics']['stability']['classification']=='not-automatically-classified'

def test_validation_detects_tampering():
    c=client(); d=c.post('/simulations/run',json={'simulationKind':'scalar-dynamic','model':{'model_type':'first_order','initial_state':0,'input_value':1,'gain':1,'time_constant':1,'duration':1}}).json()
    assert c.post('/simulations/validate',json=d).json()['valid'] is True
    d['trajectory']['finalState']['state']=999
    bad=c.post('/simulations/validate',json=d).json(); assert bad['valid'] is False and 'simulation-run-hash-mismatch' in bad['reasons']

def test_parameter_sweep_is_bounded_and_does_not_optimize():
    c=client(); base={'simulationKind':'scalar-dynamic','model':{'model_type':'first_order','initial_state':0,'input_value':1,'gain':1,'time_constant':1,'duration':2,'time_step':0.1}}
    r=c.post('/simulations/parameter-sweep',json={'baseSimulation':base,'parameterPath':'gain','values':[0.5,1,2],'metric':'final-state'})
    assert r.status_code==200,r.text; d=r.json(); assert d['runCount']==3 and d['automaticOptimizationPerformed'] is False and d['maximumMetric']>d['minimumMetric']

def _workspace(c):
    r=c.post('/data-workspace/build',json={'workspaceKey':'sim-ws','variables':[],'parameterSets':[{'parameterSetKey':'model','parameters':[{'parameterKey':'tau','value':3.0}]}],'datasets':[],'assumptions':[]}); assert r.status_code==200,r.text; return r.json()

def test_workspace_binding_materializes_parameter_without_execution():
    c=client(); ws=_workspace(c)
    r=c.post('/simulations/workspace-binding/plan',json={'workspace':ws,'simulationKind':'scalar-dynamic','model':{'model_type':'first_order','initial_state':0,'input_value':1,'gain':1,'time_constant':1,'duration':2},'bindings':[{'sourceKind':'parameter','parameterSetKey':'model','sourceKey':'tau','targetField':'time_constant'}]})
    assert r.status_code==200,r.text; d=r.json(); assert d['simulationRequest']['model']['time_constant']==3.0 and d['executionPerformed'] is False

def test_core_lineage_plan_is_two_phase_and_token_bounded(monkeypatch):
    c=client(); sim=c.post('/simulations/run',json={'simulationKind':'scalar-dynamic','model':{'model_type':'first_order','initial_state':0,'input_value':1,'gain':1,'time_constant':1,'duration':1}}).json()
    first=c.post('/integration/core/simulation-lineage/plan',json={'simulationResult':sim}); assert first.status_code==200,first.text
    d=first.json(); assert d['coreComputationLineageContract']==CORE_COMPUTATION_LINEAGE_CONTRACT and d['coreExecutionIdMustComeFromCore'] is True and d['outputRegistrations']==[]
    second=c.post('/integration/core/simulation-lineage/plan',json={'simulationResult':sim,'coreExecutionId':'core-exec-750'}); assert second.status_code==200 and second.json()['outputRegistrations'][0]['path'].endswith('/outputs')
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret750')
    assert c.post('/integration/core/simulation-lineage/plan',json={'simulationResult':sim}).status_code==401
    ok=c.post('/integration/core/simulation-lineage/plan',headers={'X-SC-Service-Token':'secret750'},json={'simulationResult':sim}); assert ok.status_code==200 and ok.json()['automaticCoreDispatchAuthorized'] is False

def test_digital_twin_is_bounded_calibration_not_stability_proof():
    c=client(); samples=[{'time':0,'input':1,'observed':0},{'time':1,'input':1,'observed':0.6},{'time':2,'input':1,'observed':0.85},{'time':3,'input':1,'observed':0.95}]
    r=c.post('/simulations/run',json={'simulationKind':'digital-twin','model':{'name':'demo','initial_state':0,'gain':1,'time_constant':1,'samples':samples}})
    assert r.status_code==200,r.text; d=r.json(); assert d['diagnostics']['stability']['classification']=='calibration-fit-only' and d['diagnostics']['stability']['established'] is False

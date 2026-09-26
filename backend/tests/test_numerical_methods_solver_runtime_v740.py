import os
from fastapi.testclient import TestClient
from app.main import app
from app.v740 import SCHEMA, SOLVER_RESULT_SCHEMA, CORE_COMPUTATION_LINEAGE_CONTRACT


def client(): return TestClient(app)


def test_manifest_catalog_status_and_capabilities():
    c=client(); m=c.get('/solvers/manifest'); assert m.status_code==200
    d=m.json(); assert d['schema']==SCHEMA and d['version']=='9.8.0' and d['solverCount']>=20
    cat=c.get('/solvers/catalog').json(); assert cat['solverCount']==d['solverCount']; assert cat['defaultSolvers']['root']=='root.brentq'
    s=c.get('/v740/status').json(); assert s['ok'] and s['version']=='9.8.0' and s['convergenceDiagnostics'] is True
    caps=c.get('/capabilities').json(); assert caps['version']=='9.8.0'; assert caps['coreIntegration']['numericalMethodsSolverRuntime'] is True


def test_root_solver_returns_diagnostics_and_execution_object():
    c=client(); r=c.post('/solvers/solve',json={'problemKind':'root','solverKey':'root.brentq','problem':{'expression':'x**2-2','variable':'x','bracket':[0,2],'tolerance':1e-10},'requestKey':'sqrt2'})
    assert r.status_code==200,r.text; d=r.json(); assert d['schema']==SOLVER_RESULT_SCHEMA and d['solverKey']=='root.brentq'
    assert d['diagnostics']['converged'] is True and d['diagnostics']['absoluteResidual'] < 1e-8
    assert d['executionObject']['objectKind']=='single_execution' and d['solverRunHash']


def test_integration_linear_algebra_and_optimization_diagnostics():
    c=client()
    integ=c.post('/solvers/solve',json={'problemKind':'integration','problem':{'expression':'x**2','lower':0,'upper':1}}); assert integ.status_code==200
    assert abs(integ.json()['orchestration']['executionResult']['result']['result']['value']-1/3)<1e-8
    lin=c.post('/solvers/solve',json={'problemKind':'linear-algebra','solverKey':'linear.solve','problem':{'matrix':[[3,1],[1,2]],'vector':[9,8]}}); assert lin.status_code==200,lin.text
    assert lin.json()['diagnostics']['residualNorm'] < 1e-10
    opt=c.post('/solvers/solve',json={'problemKind':'optimization','problem':{'expression':'(x-3)**2','variables':['x'],'initial':[0],'bounds':[[-10,10]]}}); assert opt.status_code==200,opt.text
    assert opt.json()['diagnostics']['converged'] is True


def test_solver_key_mismatch_rejected_and_no_fallback():
    c=client(); r=c.post('/solvers/solve',json={'problemKind':'root','solverKey':'ode.rk45','problem':{'expression':'x','bracket':[-1,1]}}); assert r.status_code==422


def test_solver_integrity_validation_detects_tampering():
    c=client(); d=c.post('/solvers/solve',json={'problemKind':'root','problem':{'expression':'x-1','bracket':[0,2]}}).json()
    ok=c.post('/solvers/validate',json=d); assert ok.status_code==200 and ok.json()['valid'] is True
    d['diagnostics']['residual']=99
    bad=c.post('/solvers/validate',json=d); assert bad.status_code==200 and bad.json()['valid'] is False and 'diagnostics-hash-mismatch' in bad.json()['reasons']


def test_convergence_study_refines_integration_problem():
    c=client(); r=c.post('/solvers/convergence-study',json={'problemKind':'integration','solverKey':'integration.simpson','problem':{'expression':'sin(x)','lower':0,'upper':3.141592653589793,'samples':21},'levels':3})
    assert r.status_code==200,r.text; d=r.json(); assert len(d['levels'])==3 and d['studyHash'] and d['scientificConvergenceCertified'] is False
    assert abs(d['levels'][-1]['primaryValue']-2.0)<1e-5


def _workspace(c):
    payload={'workspaceKey':'solver-ws','variables':[{'variableKey':'lo','value':0},{'variableKey':'hi','value':2}], 'parameterSets':[{'parameterSetKey':'solver','parameters':[{'parameterKey':'tol','value':1e-9}]}], 'datasets':[], 'assumptions':[]}
    r=c.post('/data-workspace/build',json=payload); assert r.status_code==200,r.text; return r.json()


def test_workspace_binding_materializes_declared_values_without_execution():
    c=client(); ws=_workspace(c)
    r=c.post('/solvers/workspace-binding/plan',json={'workspace':ws,'problemKind':'root','problem':{'expression':'x**2-2','variable':'x'},'bindings':[{'sourceKind':'variable','sourceKey':'lo','targetField':'bracket.0'}]})
    # list index paths are intentionally unsupported by bounded object path setter
    assert r.status_code==422
    r=c.post('/solvers/workspace-binding/plan',json={'workspace':ws,'problemKind':'root','problem':{'expression':'x**2-2','variable':'x','bracket':[0,2]},'bindings':[{'sourceKind':'parameter','parameterSetKey':'solver','sourceKey':'tol','targetField':'tolerance'}]})
    assert r.status_code==200,r.text; d=r.json(); assert d['solverRequest']['problem']['tolerance']==1e-9 and d['executionPerformed'] is False


def test_core_lineage_plan_two_phase_and_token_boundary(monkeypatch):
    c=client(); solved=c.post('/solvers/solve',json={'problemKind':'root','problem':{'expression':'x-1','bracket':[0,2]}}).json()
    first=c.post('/integration/core/solver-lineage/plan',json={'solverResult':solved}); assert first.status_code==200,first.text
    d=first.json(); assert d['coreComputationLineageContract']==CORE_COMPUTATION_LINEAGE_CONTRACT and d['coreExecutionIdMustComeFromCore'] is True and d['outputRegistrations']==[]
    second=c.post('/integration/core/solver-lineage/plan',json={'solverResult':solved,'coreExecutionId':'core-exec-740'}); assert second.status_code==200
    assert second.json()['outputRegistrations'][0]['path'].endswith('/outputs') and second.json()['automaticCoreDispatchAuthorized'] is False
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN','true'); monkeypatch.setenv('SCWB_SERVICE_TOKEN','secret740')
    denied=c.post('/integration/core/solver-lineage/plan',json={'solverResult':solved}); assert denied.status_code==401
    ok=c.post('/integration/core/solver-lineage/plan',headers={'X-SC-Service-Token':'secret740'},json={'solverResult':solved}); assert ok.status_code==200 and ok.json()['version']=='9.8.0'

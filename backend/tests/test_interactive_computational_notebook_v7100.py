from fastapi.testclient import TestClient
from app.main import app

c=TestClient(app)

def notebook():
    return {'notebookKey':'nb-demo','title':'Demo','cells':[
      {'cellId':'intro','cellType':'markdown','source':'# demo'},
      {'cellId':'eng','cellType':'engineering','request':{'analysisKey':'mechanical.axial-member','inputs':{'force_n':1000,'area_m2':0.01,'length_m':1,'elastic_modulus_pa':200000000000}}},
      {'cellId':'vv','cellType':'validation','action':'benchmark','dependsOn':['eng'],'bindings':[{'sourceNodeId':'eng','sourcePath':'result','targetPath':'targetResult'}],
       'request':{'cases':[{'caseKey':'stress','actualPath':'stressPa','expected':100000,'absoluteTolerance':1e-9,'relativeTolerance':0}]}}
    ]}

def test_manifest_status_capabilities():
    m=c.get('/notebooks/manifest'); assert m.status_code==200; d=m.json(); assert d['version']=='9.5.0' and d['capabilities']['typedNotebookCells']
    s=c.get('/v7100/status').json(); assert s['ok'] and s['hiddenInterpreterState'] is False
    caps=c.get('/capabilities').json(); assert caps['version']=='9.5.0' and caps['coreIntegration']['interactiveComputationalNotebookRuntime'] is True

def test_run_explicit_binding_and_integrity():
    r=c.post('/notebooks/run',json={'notebook':notebook()}); assert r.status_code==200,r.text; d=r.json(); assert d['ok'] and d['completedExecutableCellCount']==2
    assert d['hiddenInterpreterStateUsed'] is False and d['automaticResultSubstitutionPerformed'] is False
    vv=next(x for x in d['cellRuns'] if x['cellId']=='vv'); assert vv['appliedBindings'][0]['sourceCellId']=='eng'
    v=c.post('/notebooks/run/validate',json={'notebookRun':d}); assert v.status_code==200 and v.json()['valid'] is True
    d['cellRuns'][1]['resultHash']='tampered'; assert c.post('/notebooks/run/validate',json={'notebookRun':d}).json()['valid'] is False

def test_cycle_rejected():
    nb={'notebookKey':'cycle','cells':[{'cellId':'a','cellType':'markdown','dependsOn':['b']},{'cellId':'b','cellType':'markdown','dependsOn':['a']}]}
    r=c.post('/notebooks/validate',json=nb); assert r.status_code==200 and r.json()['ok'] is False

def test_replay_plan_nonexecuting():
    d=c.post('/notebooks/run',json={'notebook':notebook()}).json(); p=c.post('/notebooks/replay/plan',json={'notebookRun':d}).json()
    assert p['replayPerformed'] is False and p['hiddenStateReplayAuthorized'] is False and len(p['cells'])==2

def test_workflow_graph_projection():
    p=c.post('/notebooks/workflow-graph/plan',json=notebook()); assert p.status_code==200,p.text; d=p.json(); assert d['executionPerformed'] is False and d['markdownCellsExcludedFromExecutionGraph'] is True
    assert len(d['graph']['nodes'])==2

def test_core_plan_two_phase(monkeypatch):
    d=c.post('/notebooks/run',json={'notebook':notebook()}).json()
    p=c.post('/integration/core/notebook-workflow/plan',json={'notebookRun':d,'coreWorkflowId':'core-nb-1'}); assert p.status_code==200,p.text
    q=p.json(); assert q['coreWorkflowContract']=='sc.research.workflow-orchestration.v1' and q['automaticCoreDispatchAuthorized'] is False and len(q['stageRegistrations'])==2

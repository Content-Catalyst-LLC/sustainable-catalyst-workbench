from copy import deepcopy
from fastapi.testclient import TestClient
from app.main import app

c=TestClient(app)

def workspace_payload():
    return {"workspace":{"workspaceKey":"scientific-demo","title":"Scientific Demo","projectEntityId":"project:demo","views":[
        {"viewId":"trajectory","kind":"trajectory","title":"Trajectory","data":{"x":[0,1,2],"y":[1,0.5,0.25]},"linkGroups":["time"]},
        {"viewId":"uncertainty","kind":"uncertainty-band","title":"Uncertainty","data":{"x":[0,1,2],"center":[1,1.1,1.2],"lower":[0.8,0.9,1.0],"upper":[1.2,1.3,1.4]},"linkGroups":["time"]},
        {"viewId":"pareto","kind":"pareto","title":"Pareto","data":{"x":[1,2,3],"y":[3,2,1]}}
    ],"controls":[{"controlId":"gain","label":"Gain","targetPath":"payload.gain","value":1.0,"minimum":0,"maximum":2,"step":0.1,"targetRuntimePath":"/simulations/run"}],
    "links":[{"linkId":"time-link","sourceViewId":"trajectory","targetViewId":"uncertainty","relation":"time","sourceField":"x","targetField":"x"}]}}

def test_manifest_status():
    m=c.get('/visual-workspace/manifest').json(); assert m['ok'] and m['version']=='8.1.0' and m['coreContracts']['linkedViews']=='sc.visual-runtime.linked-views.v1'
    s=c.get('/v7110/status').json(); assert s['ok'] and s['controlsExecuteAutomatically'] is False

def test_build_validate_and_tamper():
    r=c.post('/visual-workspace/build',json=workspace_payload()); assert r.status_code==200,r.text; w=r.json(); assert len(w['views'])==3 and w['linkedViewsEnabled'] is True
    v=c.post('/visual-workspace/validate',json={'visualWorkspace':w}).json(); assert v['valid'] is True
    bad=deepcopy(w); bad['views'][0]['data']['y'][0]=999
    assert c.post('/visual-workspace/validate',json={'visualWorkspace':bad}).json()['valid'] is False

def test_linked_state_and_control_plan_are_nonexecuting():
    w=c.post('/visual-workspace/build',json=workspace_payload()).json()
    state=c.post('/visual-workspace/linked-state/apply',json={'visualWorkspace':w,'sourceViewId':'trajectory','cursor':{'x':1}}).json(); assert state['affectedViews'][0]['targetViewId']=='uncertainty' and state['recomputationPerformed'] is False
    plan=c.post('/visual-workspace/control/plan',json={'visualWorkspace':w,'controlId':'gain','value':1.5,'runtimeRequest':{'payload':{'model':'x'}}}).json(); assert plan['preparedRuntimeRequest']['payload']['gain']==1.5 and plan['executionPerformed'] is False

def test_core_plan_uses_existing_visual_contracts():
    w=c.post('/visual-workspace/build',json=workspace_payload()).json()
    headers={'X-Request-ID':'v7110','X-SC-Gateway-Service':'workbench','X-SC-Core-Version':'3.0'}
    r=c.post('/integration/core/visual-workspace/plan',json={'visualWorkspace':w,'coreSessionId':'core-session-1'},headers=headers); assert r.status_code==200,r.text; p=r.json()
    assert len(p['viewPlans'])==3 and p['coreSceneContract']=='sc.visual-runtime.scene.v1' and p['coreLinkedViewsContract']=='sc.visual-runtime.linked-views.v1'
    assert p['automaticCoreDispatchAuthorized'] is False and p['coreExecutesScientificComputation'] is False

def test_invalid_band_and_bad_control_rejected():
    p=workspace_payload(); p['workspace']['views'][1]['data']['lower']=[2,2,2]
    assert c.post('/visual-workspace/build',json=p).status_code==422
    w=c.post('/visual-workspace/build',json=workspace_payload()).json()
    assert c.post('/visual-workspace/control/plan',json={'visualWorkspace':w,'controlId':'gain','value':3,'runtimeRequest':{}}).status_code==422

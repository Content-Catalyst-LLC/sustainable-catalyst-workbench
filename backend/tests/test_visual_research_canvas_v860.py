import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.v810 import _store_root

c=TestClient(app)


def _seed(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    envkey='env-v860'; projectkey='project-v860'
    env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Visual Canvas Environment','projectEntityId':projectkey,'components':[]}}); assert env.status_code==200,env.text
    saved=c.post('/research-environment/persistence/save',json={'researchEnvironment':env.json(),'expectedCurrentRevision':0,'reason':'canvas-seed','actor':'researcher'}); assert saved.status_code==200,saved.text
    ws=c.post('/research-projects/build',json={'project':{'projectKey':projectkey,'title':'Visual Research Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}); assert ws.status_code==200,ws.text
    ps=c.post('/research-projects/save',json={'workspace':ws.json(),'expectedProjectRevision':0,'reason':'canvas-seed','actor':'researcher'}); assert ps.status_code==200,ps.text
    asset={'projectKey':projectkey,'assetKey':'paper-a','assetType':'source','title':'Paper A','assetRef':'https://example.org/a','contentHash':'abc123456789','origin':'external','tags':['canvas']}
    ar=c.post('/research-assets/register',json={'asset':asset,'expectedAssetRevision':0,'reason':'canvas-seed','actor':'researcher'}); assert ar.status_code==200,ar.text
    job=c.post('/execution-console/jobs/prepare',json={'projectKey':projectkey,'runtimeKind':'solver','label':'Canvas solver run','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}); assert job.status_code==200,job.text
    run=c.post(f"/execution-console/jobs/{job.json()['jobId']}/run",json={'expectedJobRevision':1,'reason':'canvas-seed','actor':'researcher'}); assert run.status_code==200,run.text
    return projectkey


def test_manifest_status_and_capabilities():
    m=c.get('/research-canvas/manifest').json()
    assert m['ok'] and m['version']=='8.6.0' and m['release']=='Visual Research Canvas'
    assert m['capabilities']['projectVisualCanvas'] is True and m['boundaries']['canvasIsScientificSourceOfTruth'] is False
    s=c.get('/v860/status').json(); assert s['ok'] and s['version']=='8.6.0' and s['persistentLayout'] is True
    caps=c.get('/capabilities').json(); assert caps['version']=='8.6.0'
    for key in ('visualResearchCanvas','visualResearchCanvasPersistentLayout','visualResearchCanvasLineageOverlay','visualResearchCanvasLinkedSelection','visualResearchCanvasCorePlanning'):
        assert caps['coreIntegration'][key] is True


def test_canvas_projects_authoritative_objects(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    r=c.get(f'/research-canvas/{project}'); assert r.status_code==200,r.text
    b=r.json(); kinds={n['kind'] for n in b['nodes']}
    assert {'project','environment','asset','execution','timeline'} <= kinds
    assert b['derivedFromAuthoritativeStores'] is True
    assert b['canvasIsScientificSourceOfTruth'] is False
    assert b['layoutPersistsScientificPayloads'] is False
    relations={e['relation'] for e in b['edges']}
    assert 'active-environment' in relations and 'project-asset' in relations and 'project-execution' in relations


def test_layout_persistence_and_projection_application(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    canvas=c.get(f'/research-canvas/{project}').json()
    nodes=canvas['nodes'][:3]
    payload={'expectedLayoutRevision':0,'nodes':[{'nodeId':n['nodeId'],'x':100+i*250,'y':80+i*90,'width':260,'height':120,'pinned':True} for i,n in enumerate(nodes)],'links':[{'fromNodeId':nodes[0]['nodeId'],'toNodeId':nodes[2]['nodeId'],'relation':'researcher-context','label':'supports review'}],'viewport':{'x':12,'y':34,'zoom':1.25},'layers':{'timeline':True,'lineage':True,'assets':True,'executions':True},'actor':'researcher','reason':'arrange-canvas'}
    s=c.post(f'/research-canvas/{project}/layout/save',json=payload); assert s.status_code==200,s.text
    saved=s.json(); assert saved['layoutRevision']==1 and saved['layoutHash'] and saved['scientificPayloadsPersisted'] is False
    loaded=c.get(f'/research-canvas/{project}/layout').json(); assert loaded['layoutRevision']==1 and loaded['viewport']['zoom']==1.25
    projected=c.get(f'/research-canvas/{project}').json(); by={n['nodeId']:n for n in projected['nodes']}
    assert by[nodes[0]['nodeId']]['x']==100 and by[nodes[0]['nodeId']]['pinned'] is True
    assert any(e['kind']=='researcher' and e['relation']=='researcher-context' for e in projected['edges'])
    conflict=dict(payload); conflict['expectedLayoutRevision']=0
    rr=c.post(f'/research-canvas/{project}/layout/save',json=conflict); assert rr.status_code==409


def test_layout_rejects_unknown_nodes(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    r=c.post(f'/research-canvas/{project}/layout/save',json={'expectedLayoutRevision':0,'nodes':[{'nodeId':'missing','x':0,'y':0}]})
    assert r.status_code==422 and 'unknown node' in r.text.lower()


def test_selection_and_lineage_overlay(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    canvas=c.get(f'/research-canvas/{project}').json(); ids=[n['nodeId'] for n in canvas['nodes'][:2]]
    sel=c.post('/research-canvas/selection/resolve',json={'projectKey':project,'nodeIds':ids}); assert sel.status_code==200,sel.text
    assert sel.json()['selectionCount']==2 and sel.json()['selectionIsViewStateOnly'] is True
    lin=c.get(f'/research-canvas/{project}/lineage-overlay'); assert lin.status_code==200,lin.text
    assert lin.json()['edgeCount']>=1 and lin.json()['automaticCausalInferencePerformed'] is False


def test_layout_integrity_failure_propagates(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    canvas=c.get(f'/research-canvas/{project}').json(); n=canvas['nodes'][0]
    s=c.post(f'/research-canvas/{project}/layout/save',json={'expectedLayoutRevision':0,'nodes':[{'nodeId':n['nodeId'],'x':5,'y':7}]}); assert s.status_code==200
    paths=list((_store_root()/'visual-research-canvas').glob('*/layout.json')); assert paths
    data=json.loads(paths[0].read_text()); data['reason']='tampered'; paths[0].write_text(json.dumps(data))
    r=c.get(f'/research-canvas/{project}/layout'); assert r.status_code==422 and 'integrity' in r.text.lower()


def test_core_plan_is_two_phase_and_view_only(monkeypatch,tmp_path):
    project=_seed(monkeypatch,tmp_path)
    canvas=c.get(f'/research-canvas/{project}').json(); n=canvas['nodes'][0]
    assert c.post(f'/research-canvas/{project}/layout/save',json={'expectedLayoutRevision':0,'nodes':[{'nodeId':n['nodeId'],'x':20,'y':20}]}).status_code==200
    p1=c.post('/integration/core/research-canvas/plan',json={'projectKey':project,'nodeIds':[n['nodeId']],'coreProjectEntityId':'core-project'}); assert p1.status_code==200,p1.text
    b1=p1.json(); assert b1['coreSessionId'] is None and b1['automaticCoreDispatchAuthorized'] is False and b1['canvasBindingIsViewCompositionOnly'] is True
    p2=c.post('/integration/core/research-canvas/plan',json={'projectKey':project,'nodeIds':[n['nodeId']],'coreProjectEntityId':'core-project','coreSessionId':'core-session'}); assert p2.status_code==200,p2.text
    b2=p2.json(); assert any(x.get('phase')=='visual-research-canvas-layout-bind' and x.get('data',{}).get('object_type')=='workbench.visual-research-canvas-layout' for x in b2['coreRequests'])

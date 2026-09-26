import json
from fastapi.testclient import TestClient
from app.main import app
from app.v810 import _store_root

c=TestClient(app)


def _project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    spec={'environmentKey':'env-v830','title':'Registry Environment','projectEntityId':'project-v830','components':[
        {'componentKey':'data-main','componentType':'data-workspace','payload':{'workspaceHash':'data-v830','rows':12},'metadata':{'title':'Primary dataset'}},
        {'componentKey':'notebook-main','componentType':'notebook-run','payload':{'notebookRunHash':'nb-v830','cellRuns':[]}},
        {'componentKey':'visual-main','componentType':'visual-workspace','payload':{'visualWorkspaceHash':'vis-v830','views':[]}},
    ],'executionObjects':[{'objectRef':'sc://exec/v830','objectHash':'exec-hash-v830'}]}
    env=c.post('/research-environment/build',json={'environment':spec}).json()
    saved=c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'v830-test'}); assert saved.status_code==200,saved.text
    ws=c.post('/research-projects/build',json={'project':{'projectKey':'project-v830','title':'Registry Project','activeEnvironmentKey':'env-v830','activeEnvironmentRevision':1}}); assert ws.status_code==200,ws.text
    ps=c.post('/research-projects/save',json={'workspace':ws.json(),'expectedProjectRevision':0,'reason':'v830-test'}); assert ps.status_code==200,ps.text
    return ws.json()


def test_manifest_status():
    m=c.get('/research-assets/manifest').json(); assert m['ok'] and m['version']=='9.10.0' and m['capabilities']['projectScopedAssetRegistry'] is True
    s=c.get('/v830/status').json(); assert s['ok'] and s['version']=='9.10.0' and s['projectStateAuthority']=='v8.2' and s['environmentStateAuthority']=='v8.1'


def test_index_project_and_search(monkeypatch,tmp_path):
    _project(monkeypatch,tmp_path)
    r=c.post('/research-assets/index/project',json={'projectKey':'project-v830'}); assert r.status_code==200,r.text
    b=r.json(); assert b['indexedCount']==4 and b['scientificPayloadsDuplicated'] is False
    q=c.get('/research-assets/search',params={'project_key':'project-v830','asset_type':'dataset'}); assert q.status_code==200,q.text
    out=q.json(); assert out['resultCount']==1 and out['results'][0]['title']=='Primary dataset'
    q2=c.get('/research-assets/search',params={'project_key':'project-v830','q':'notebook-main'}).json(); assert q2['resultCount']==1 and q2['results'][0]['assetType']=='notebook'


def test_explicit_external_asset_and_revisions(monkeypatch,tmp_path):
    _project(monkeypatch,tmp_path)
    payload={'asset':{'projectKey':'project-v830','assetKey':'external-paper','assetType':'source','title':'External paper','assetRef':'https://example.org/paper','contentHash':'12345678abcdef','origin':'external','tags':['source','paper']},'expectedAssetRevision':0,'reason':'register-source'}
    a=c.post('/research-assets/register',json=payload); assert a.status_code==200,a.text
    assert a.json()['assetRevision']==1
    payload['expectedAssetRevision']=1; payload['asset']['description']='Reviewed source'
    b=c.post('/research-assets/register',json=payload); assert b.status_code==200,b.text
    assert b.json()['assetRevision']==2 and b.json()['parentAssetRevision']==1
    rev=c.get('/research-assets/project-v830/external-paper/revisions'); assert rev.status_code==200 and rev.json()['revisionCount']==2
    conflict=c.post('/research-assets/register',json={**payload,'expectedAssetRevision':0}); assert conflict.status_code==409


def test_external_requires_ref_and_hash():
    r=c.post('/research-assets/register',json={'asset':{'projectKey':'p','assetKey':'a','assetType':'external','title':'x','contentHash':'12345678','origin':'external'}})
    assert r.status_code==422


def test_asset_tamper_detected(monkeypatch,tmp_path):
    _project(monkeypatch,tmp_path)
    c.post('/research-assets/index/project',json={'projectKey':'project-v830'})
    revs=list((_store_root()/'asset-registry').glob('*/assets/*/revisions/*.json')); assert revs
    data=json.loads(revs[0].read_text()); data['reason']='tampered'; revs[0].write_text(json.dumps(data))
    idx=json.loads((revs[0].parents[1]/'index.json').read_text())
    r=c.get(f"/research-assets/project-v830/{idx['assetKey']}")
    assert r.status_code==422 and 'integrity' in r.text


def test_core_plan_is_two_phase(monkeypatch,tmp_path):
    _project(monkeypatch,tmp_path)
    c.post('/research-assets/index/project',json={'projectKey':'project-v830'})
    p1=c.post('/integration/core/research-assets/plan',json={'projectKey':'project-v830','coreProjectEntityId':'core-project-v830'}); assert p1.status_code==200,p1.text
    assert p1.json()['phase']=='prepare-session' and p1.json()['coreSessionId'] is None and p1.json()['automaticCoreDispatchAuthorized'] is False
    p2=c.post('/integration/core/research-assets/plan',json={'projectKey':'project-v830','coreProjectEntityId':'core-project-v830','coreSessionId':'core-session-v830','assetKeys':['environment:data-main']}); assert p2.status_code==200,p2.text
    b=p2.json(); assert b['phase']=='bind-environment' and b['assetCount']==1
    assert any(x.get('phase')=='research-asset-bind' and x.get('data',{}).get('object_type')=='workbench.research-asset.dataset' for x in b['coreRequests'])


def test_capabilities_advertise_v830():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.10.0'
    ci=caps['coreIntegration']
    for key in ('researchAssetArtifactRegistry','researchAssetProjectIndexing','researchAssetSearch','researchAssetRevisionHistory','researchAssetCorePlanning'):
        assert ci[key] is True

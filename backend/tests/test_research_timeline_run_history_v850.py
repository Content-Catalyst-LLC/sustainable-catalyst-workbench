import json
from fastapi.testclient import TestClient
from app.main import app
from app.v810 import _store_root

c = TestClient(app)


def _seed(monkeypatch, tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    env_spec={
        'environmentKey':'env-v850','title':'Timeline Environment','projectEntityId':'project-v850',
        'components':[{'componentKey':'data-main','componentType':'data-workspace','payload':{'rows':5},'metadata':{'title':'Timeline dataset'}}]
    }
    env=c.post('/research-environment/build',json={'environment':env_spec}).json()
    s1=c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'initial-save','actor':'researcher'}); assert s1.status_code==200,s1.text
    cp=c.post('/research-environment/checkpoints/create',json={'environmentKey':'env-v850','revision':1,'label':'baseline','actor':'researcher'}); assert cp.status_code==200,cp.text
    rec=c.post('/research-environment/recovery/apply',json={'environmentKey':'env-v850','target':{'revision':1},'expectedCurrentRevision':1,'reason':'test-recovery','actor':'researcher'}); assert rec.status_code==200,rec.text
    ws=c.post('/research-projects/build',json={'project':{'projectKey':'project-v850','title':'Timeline Project','activeEnvironmentKey':'env-v850','activeEnvironmentRevision':2}}); assert ws.status_code==200,ws.text
    ps=c.post('/research-projects/save',json={'workspace':ws.json(),'expectedProjectRevision':0,'reason':'project-created','actor':'researcher'}); assert ps.status_code==200,ps.text
    asset={'projectKey':'project-v850','assetKey':'source-paper','assetType':'source','title':'Source Paper','assetRef':'https://example.org/source','contentHash':'abcdef1234567890','origin':'external','tags':['source','timeline']}
    a1=c.post('/research-assets/register',json={'asset':asset,'expectedAssetRevision':0,'reason':'source-added','actor':'researcher'}); assert a1.status_code==200,a1.text
    asset['description']='reviewed'
    a2=c.post('/research-assets/register',json={'asset':asset,'expectedAssetRevision':1,'reason':'source-reviewed','actor':'researcher'}); assert a2.status_code==200,a2.text
    job=c.post('/execution-console/jobs/prepare',json={'projectKey':'project-v850','runtimeKind':'solver','label':'timeline root','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}); assert job.status_code==200,job.text
    run=c.post(f"/execution-console/jobs/{job.json()['jobId']}/run",json={'expectedJobRevision':1,'reason':'timeline-run','actor':'researcher'}); assert run.status_code==200,run.text
    return {'jobId':job.json()['jobId'],'checkpointId':cp.json()['checkpointId']}


def test_manifest_and_status():
    m=c.get('/research-timeline/manifest').json()
    assert m['ok'] and m['version']=='9.12.0' and m['capabilities']['derivedProjectTimeline'] is True
    assert m['boundaries']['timelineIsCompetingSourceOfTruth'] is False
    s=c.get('/v850/status').json(); assert s['ok'] and s['version']=='9.12.0' and s['runHistory'] is True


def test_timeline_aggregates_authoritative_sources(monkeypatch,tmp_path):
    _seed(monkeypatch,tmp_path)
    r=c.get('/research-timeline/project-v850'); assert r.status_code==200,r.text
    b=r.json(); sources={e['source'] for e in b['events']}
    assert {'project','environment','checkpoint','asset','execution'} <= sources
    assert b['derivedFromAuthoritativeStores'] is True and b['timelineIsSourceOfTruth'] is False and b['timelineHash']
    assert any(e['eventType']=='environment-recovery-applied' for e in b['events'])
    assert any(e['eventType']=='execution-completed' for e in b['events'])
    asset_events=[e for e in b['events'] if e['source']=='asset']
    assert len(asset_events)==2 and all(e['timeSource']=='recorded' for e in asset_events)


def test_timeline_filters(monkeypatch,tmp_path):
    _seed(monkeypatch,tmp_path)
    a=c.get('/research-timeline/project-v850',params={'source':'asset'}).json(); assert a['eventCount']==2 and all(e['source']=='asset' for e in a['events'])
    q=c.get('/research-timeline/project-v850',params={'q':'recovery'}).json(); assert q['eventCount']>=1 and any('recovery' in e['eventType'] for e in q['events'])


def test_run_history(monkeypatch,tmp_path):
    seed=_seed(monkeypatch,tmp_path)
    r=c.get('/research-timeline/project-v850/runs'); assert r.status_code==200,r.text
    b=r.json(); assert b['runCount']==1 and b['runs'][0]['jobId']==seed['jobId'] and b['runs'][0]['status']=='completed'
    statuses=[h['status'] for h in b['runs'][0]['history']]
    assert statuses==['prepared','running','completed']


def test_lineage_graph(monkeypatch,tmp_path):
    _seed(monkeypatch,tmp_path)
    r=c.get('/research-timeline/project-v850/lineage'); assert r.status_code==200,r.text
    b=r.json(); relations={e['relation'] for e in b['edges']}
    assert 'environment-revision-parent' in relations
    assert 'recovery-source' in relations
    assert 'checkpoint-of' in relations
    assert 'asset-revision-parent' in relations
    assert 'job-transition' in relations
    assert b['automaticCausalInferencePerformed'] is False


def test_neutral_timeline_comparison(monkeypatch,tmp_path):
    _seed(monkeypatch,tmp_path)
    timeline=c.get('/research-timeline/project-v850').json()['events']
    left=next(e for e in timeline if e['source']=='environment')
    right=next(e for e in timeline if e['source']=='execution' and e['eventType']=='execution-completed')
    r=c.post('/research-timeline/compare',json={'projectKey':'project-v850','leftEventId':left['eventId'],'rightEventId':right['eventId']}); assert r.status_code==200,r.text
    b=r.json(); assert b['changedFieldCount']>0 and b['automaticWinnerSelected'] is False and b['automaticScientificInterpretationPerformed'] is False


def test_timeline_propagates_integrity_failure(monkeypatch,tmp_path):
    _seed(monkeypatch,tmp_path)
    revs=list((_store_root()/'asset-registry').glob('*/assets/*/revisions/*.json')); assert revs
    data=json.loads(revs[0].read_text()); data['reason']='tampered'; revs[0].write_text(json.dumps(data))
    r=c.get('/research-timeline/project-v850'); assert r.status_code==422 and 'integrity' in r.text


def test_core_plan_two_phase(monkeypatch,tmp_path):
    _seed(monkeypatch,tmp_path)
    timeline=c.get('/research-timeline/project-v850').json()['events']
    eid=timeline[-1]['eventId']
    p1=c.post('/integration/core/research-timeline/plan',json={'projectKey':'project-v850','eventIds':[eid],'coreProjectEntityId':'core-project'}); assert p1.status_code==200,p1.text
    assert p1.json()['coreSessionId'] is None and p1.json()['automaticCoreDispatchAuthorized'] is False
    p2=c.post('/integration/core/research-timeline/plan',json={'projectKey':'project-v850','eventIds':[eid],'coreProjectEntityId':'core-project','coreSessionId':'core-session'}); assert p2.status_code==200,p2.text
    b=p2.json(); assert any(x.get('phase')=='research-timeline-event-bind' and x.get('data',{}).get('object_type')=='workbench.research-timeline-event' for x in b['coreRequests'])


def test_capabilities_advertise_v850():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.12.0'
    for key in ('researchTimelineRunHistory','researchTimelineDerivedEvents','researchTimelineLineageGraph','researchTimelineComparison','researchTimelineCorePlanning'):
        assert caps['coreIntegration'][key] is True

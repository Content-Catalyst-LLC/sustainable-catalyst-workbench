from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def _seed(monkeypatch, tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path / 'store'))
    project='project-v8100'; envkey='env-v8100'
    env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Analysis Board Environment','projectEntityId':project,'components':[]}}).json()
    assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'v8100-seed'}).status_code==200
    ws=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Analysis Board Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}).json()
    assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'v8100-seed'}).status_code==200
    jobs=[]
    for bracket,label in [([0,3],'Run A'),([1,4],'Run B')]:
        r=c.post('/execution-console/jobs/prepare',json={'projectKey':project,'runtimeKind':'solver','label':label,'request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':bracket},'solverKey':'root.brentq'}})
        assert r.status_code==200,r.text
        jid=r.json()['jobId']; assert c.post(f'/execution-console/jobs/{jid}/run',json={'expectedJobRevision':1,'reason':'v8100-seed'}).status_code==200; jobs.append(jid)
    # Explicit asset with verifiable hash
    ar=c.post('/research-assets/register',json={'asset':{'projectKey':project,'assetKey':'dataset-a','assetType':'dataset','title':'Dataset A','contentHash':'0123456789abcdef','origin':'explicit'},'expectedAssetRevision':0,'reason':'v8100-seed'})
    assert ar.status_code==200, ar.text
    return project,jobs,['dataset-a']


def _figure_request(project,jobs):
    cat=c.get(f'/figure-composer/source-catalog/{project}').json()
    metric=next(x['metric'] for x in cat['resultMetrics'] if x['presentCount']>=2)
    return {'projectKey':project,'jobIds':jobs,'title':'Board figure','panels':[{'panelId':'p1','mark':'bar','metricScope':'result','yMetrics':[metric]}]}


def test_manifest_status_capabilities():
    m=c.get('/analysis-board/manifest').json()
    assert m['ok'] and m['version']=='8.10.0'
    assert m['capabilities']['crossObjectAnalysisAssembly'] and m['capabilities']['immutableAnalysisSnapshots']
    assert m['boundaries']['automaticFindingGenerationAuthorized'] is False
    s=c.get('/v8100/status').json()
    assert s['immutableAnalysisSnapshots'] and s['automaticFindingGeneration'] is False
    caps=c.get('/capabilities').json()
    assert caps['version']=='8.10.0'
    for key in ('reproducibleAnalysisBoard','analysisBoardCrossObjectAssembly','analysisBoardImmutableSnapshots','analysisBoardProvenance','analysisBoardResearcherNarrative','analysisBoardCorePlanning'):
        assert caps['coreIntegration'][key] is True


def test_board_assembles_authoritative_sources(monkeypatch,tmp_path):
    project,jobs,assets=_seed(monkeypatch,tmp_path)
    figure=_figure_request(project,jobs)
    payload={'projectKey':project,'title':'Root solver analysis','jobIds':jobs,'assetKeys':assets,
             'comparison':{'projectKey':project,'jobIds':jobs},'figures':[figure],
             'narrative':[{'itemId':'a1','kind':'assumption','title':'Bracket','text':'Each run uses an explicit bracket.','evidenceRefs':[jobs[0]]},
                          {'itemId':'f1','kind':'finding','title':'Observed output','text':'Finding text is explicitly researcher-authored.','state':'final'}]}
    r=c.post('/analysis-board/build',json=payload); assert r.status_code==200,r.text
    b=r.json(); assert b['version']=='8.10.0' and b['projectKey']==project
    assert len(b['sources']['jobs'])==2 and len(b['sources']['assets'])==1
    assert b['analysis']['comparison']['comparisonHash'] and b['analysis']['figures'][0]['figureHash']
    assert b['narrative']['assumptions'][0]['itemId']=='a1' and b['narrative']['findings'][0]['itemId']=='f1'
    assert b['provenance']['sourceHashesPreserved'] is True and b['reproducibility']['snapshotEligible'] is True
    assert b['boundaries']['findingsAutomaticallyGenerated'] is False and b['boardHash']


def test_snapshot_is_immutable_content_addressed_and_idempotent(monkeypatch,tmp_path):
    project,jobs,assets=_seed(monkeypatch,tmp_path)
    payload={'projectKey':project,'jobIds':jobs,'assetKeys':assets,'snapshotLabel':'Certified board','createdBy':'tester'}
    one=c.post('/analysis-board/snapshots',json=payload); assert one.status_code==200,one.text
    a=one.json(); assert a['immutable'] is True and a['snapshotHash'] and a['recordHash']
    two=c.post('/analysis-board/snapshots',json=payload); assert two.status_code==200,two.text
    assert two.json()['snapshotHash']==a['snapshotHash'] and two.json()['idempotent'] is True
    ls=c.get(f'/analysis-board/snapshots/{project}').json(); assert ls['snapshotCount']==1
    load=c.get(f"/analysis-board/snapshots/{project}/{a['snapshotHash']}"); assert load.status_code==200
    assert load.json()['boardHash']==a['boardHash']


def test_cross_project_sources_rejected(monkeypatch,tmp_path):
    project,jobs,assets=_seed(monkeypatch,tmp_path)
    bad=c.post('/analysis-board/build',json={'projectKey':project,'jobIds':jobs,'comparison':{'projectKey':'other','jobIds':jobs}})
    assert bad.status_code==422


def test_core_plan_is_two_phase_and_non_authoritative(monkeypatch,tmp_path):
    project,jobs,assets=_seed(monkeypatch,tmp_path)
    r=c.post('/integration/core/analysis-board/plan',json={'projectKey':project,'jobIds':jobs,'assetKeys':assets,'coreSessionId':'core-v8100'})
    assert r.status_code==200,r.text
    b=r.json(); assert b['version']=='8.10.0' and b['boardBindingIsReproducibleAnalyticalViewOnly'] is True
    assert b['automaticCoreDispatchAuthorized'] is False and b['scientificValidityInferenceAuthorized'] is False
    assert any(x.get('phase')=='reproducible-analysis-board-bind' for x in b['coreRequests'])

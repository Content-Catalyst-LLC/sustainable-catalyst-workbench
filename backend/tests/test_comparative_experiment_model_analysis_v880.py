from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)

def _seed(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    project='project-v880'; envkey='env-v880'
    env=c.post('/research-environment/build',json={'environment':{'environmentKey':envkey,'title':'Comparison Environment','projectEntityId':project,'components':[]}}).json()
    assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'v880-seed'}).status_code==200
    ws=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Comparison Project','activeEnvironmentKey':envkey,'activeEnvironmentRevision':1}}).json()
    assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'v880-seed'}).status_code==200
    jobs=[]
    for bracket,label in [([0,3],'solver-a'),([1,4],'solver-b'),([0,5],'solver-c')]:
        r=c.post('/execution-console/jobs/prepare',json={'projectKey':project,'runtimeKind':'solver','label':label,'request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':bracket},'solverKey':'root.brentq'}}); assert r.status_code==200,r.text
        jid=r.json()['jobId']; run=c.post(f'/execution-console/jobs/{jid}/run',json={'expectedJobRevision':1,'reason':'v880-seed'}); assert run.status_code==200,run.text; jobs.append(jid)
    return project,jobs

def test_manifest_status_capabilities():
    m=c.get('/comparative-analysis/manifest').json(); assert m['ok'] and m['version']=='9.8.0' and m['capabilities']['pairwiseNumericDeltas']
    s=c.get('/v880/status').json(); assert s['completedRunComparison'] and s['automaticWinnerSelection'] is False
    caps=c.get('/capabilities').json(); assert caps['version']=='9.8.0'
    for key in ('comparativeExperimentModelAnalysis','comparativeRunMetricExtraction','comparativePairwiseDeltas','comparativeNeutralAssessment','comparativeCorePlanning'): assert caps['coreIntegration'][key] is True

def test_compare_completed_runs(monkeypatch,tmp_path):
    project,jobs=_seed(monkeypatch,tmp_path)
    r=c.post('/comparative-analysis/compare',json={'projectKey':project,'jobIds':jobs}); assert r.status_code==200,r.text
    b=r.json(); assert b['jobCount']==3 and len(b['pairwiseComparisons'])==3
    assert b['requestMetricMatrix']['metricCount']>0 and b['resultMetricMatrix']['metricCount']>0
    assert all(p['winnerSelected'] is False and p['scientificValidityInferred'] is False for p in b['pairwiseComparisons'])
    assert b['boundaries']['automaticWinnerSelectionPerformed'] is False

def test_baseline_comparison(monkeypatch,tmp_path):
    project,jobs=_seed(monkeypatch,tmp_path)
    r=c.post('/comparative-analysis/compare',json={'projectKey':project,'jobIds':jobs,'baselineJobId':jobs[0]}); assert r.status_code==200,r.text
    b=r.json(); assert b['comparisonMode']=='baseline' and len(b['pairwiseComparisons'])==2
    assert all(x['leftJobId']==jobs[0] for x in b['pairwiseComparisons'])

def test_duplicate_and_incomplete_rejected(monkeypatch,tmp_path):
    project,jobs=_seed(monkeypatch,tmp_path)
    dup=c.post('/comparative-analysis/compare',json={'projectKey':project,'jobIds':[jobs[0],jobs[0]]}); assert dup.status_code==422
    pending=c.post('/execution-console/jobs/prepare',json={'projectKey':project,'runtimeKind':'solver','label':'pending','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}).json()['jobId']
    bad=c.post('/comparative-analysis/compare',json={'projectKey':project,'jobIds':[jobs[0],pending]}); assert bad.status_code==409

def test_core_plan_is_neutral_and_two_phase(monkeypatch,tmp_path):
    project,jobs=_seed(monkeypatch,tmp_path)
    r=c.post('/integration/core/comparative-analysis/plan',json={'projectKey':project,'jobIds':jobs[:2],'coreSessionId':'core-v880'}); assert r.status_code==200,r.text
    b=r.json(); assert b['version']=='9.8.0' and b['comparisonBindingIsAnalyticalViewOnly'] is True
    assert b['automaticCoreDispatchAuthorized'] is False and b['automaticWinnerSelectionAuthorized'] is False
    assert any(x.get('phase')=='comparative-analysis-bind' for x in b['coreRequests'])

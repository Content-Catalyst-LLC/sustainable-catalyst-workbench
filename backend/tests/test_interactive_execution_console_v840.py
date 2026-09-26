import json
from fastapi.testclient import TestClient
from app.main import app
from app.v810 import _store_root

c=TestClient(app)

def _project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    spec={'environmentKey':'env-v840','title':'Execution Console Environment','projectEntityId':'project-v840','components':[]}
    env=c.post('/research-environment/build',json={'environment':spec}).json()
    s=c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'v840-test'}); assert s.status_code==200,s.text
    ws=c.post('/research-projects/build',json={'project':{'projectKey':'project-v840','title':'Execution Project','activeEnvironmentKey':'env-v840','activeEnvironmentRevision':1}}); assert ws.status_code==200,ws.text
    ps=c.post('/research-projects/save',json={'workspace':ws.json(),'expectedProjectRevision':0,'reason':'v840-test'}); assert ps.status_code==200,ps.text

def _solver_job(monkeypatch,tmp_path,label='root'):
    _project(monkeypatch,tmp_path)
    payload={'projectKey':'project-v840','runtimeKind':'solver','label':label,'request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}
    r=c.post('/execution-console/jobs/prepare',json=payload); assert r.status_code==200,r.text
    return r.json()

def test_manifest_status():
    m=c.get('/execution-console/manifest').json(); assert m['ok'] and m['version']=='9.10.0' and m['capabilities']['durableProjectExecutionJobs'] is True
    s=c.get('/v840/status').json(); assert s['ok'] and s['version']=='9.10.0' and s['hiddenBackgroundExecution'] is False

def test_prepare_queue_run_inspect(monkeypatch,tmp_path):
    job=_solver_job(monkeypatch,tmp_path)
    assert job['status']=='prepared' and job['scientificExecutionPerformed'] is False
    q=c.post(f"/execution-console/jobs/{job['jobId']}/queue",json={'expectedJobRevision':1,'reason':'queue'}); assert q.status_code==200,q.text
    assert q.json()['status']=='queued'
    run=c.post(f"/execution-console/jobs/{job['jobId']}/run",json={'expectedJobRevision':2,'reason':'run'}); assert run.status_code==200,run.text
    done=run.json(); assert done['status']=='completed' and done['scientificExecutionPerformed'] is True and done['resultHash']
    got=c.get(f"/execution-console/jobs/{job['jobId']}").json(); assert got['jobHash']==done['jobHash']
    listing=c.get('/execution-console/jobs',params={'project_key':'project-v840','status':'completed'}).json(); assert listing['jobCount']==1

def test_cancel_pending(monkeypatch,tmp_path):
    job=_solver_job(monkeypatch,tmp_path)
    r=c.post(f"/execution-console/jobs/{job['jobId']}/cancel",json={'expectedJobRevision':1,'reason':'cancel'}); assert r.status_code==200,r.text
    assert r.json()['status']=='cancelled' and r.json()['scientificExecutionPerformed'] is False
    again=c.post(f"/execution-console/jobs/{job['jobId']}/run",json={'reason':'should-fail'}); assert again.status_code==409

def test_revision_conflict(monkeypatch,tmp_path):
    job=_solver_job(monkeypatch,tmp_path)
    r=c.post(f"/execution-console/jobs/{job['jobId']}/queue",json={'expectedJobRevision':99,'reason':'bad'}); assert r.status_code==409

def test_tamper_detected(monkeypatch,tmp_path):
    job=_solver_job(monkeypatch,tmp_path)
    paths=list((_store_root()/'execution-console'/'jobs').glob('*.json')); assert paths
    data=json.loads(paths[0].read_text()); data['label']='tampered'; paths[0].write_text(json.dumps(data))
    r=c.get(f"/execution-console/jobs/{job['jobId']}"); assert r.status_code==422 and 'integrity' in r.text

def test_compare_completed_jobs(monkeypatch,tmp_path):
    first=_solver_job(monkeypatch,tmp_path,'a')
    r1=c.post(f"/execution-console/jobs/{first['jobId']}/run",json={'expectedJobRevision':1,'reason':'run'}); assert r1.status_code==200,r1.text
    payload={'projectKey':'project-v840','runtimeKind':'solver','label':'b','request':{'problemKind':'root','problem':{'expression':'x**2-9','variable':'x','bracket':[0,4]},'solverKey':'root.brentq'}}
    second=c.post('/execution-console/jobs/prepare',json=payload).json()
    r2=c.post(f"/execution-console/jobs/{second['jobId']}/run",json={'expectedJobRevision':1,'reason':'run'}); assert r2.status_code==200,r2.text
    cmp=c.post('/execution-console/compare',json={'jobIds':[first['jobId'],second['jobId']]}); assert cmp.status_code==200,cmp.text
    body=cmp.json(); assert body['jobCount']==2 and body['automaticWinnerSelected'] is False and body['automaticScientificInterpretationPerformed'] is False

def test_invalid_payload_fails_and_persists(monkeypatch,tmp_path):
    _project(monkeypatch,tmp_path)
    job=c.post('/execution-console/jobs/prepare',json={'projectKey':'project-v840','runtimeKind':'solver','request':{'bad':True}}).json()
    run=c.post(f"/execution-console/jobs/{job['jobId']}/run",json={'expectedJobRevision':1,'reason':'run'}); assert run.status_code==422
    got=c.get(f"/execution-console/jobs/{job['jobId']}").json(); assert got['status']=='failed' and got['error']

def test_core_plan_two_phase(monkeypatch,tmp_path):
    job=_solver_job(monkeypatch,tmp_path)
    p=c.post('/integration/core/execution-console/plan',json={'projectKey':'project-v840','jobIds':[job['jobId']],'coreProjectEntityId':'core-project'}); assert p.status_code==200,p.text
    body=p.json(); assert body['jobCount']==1 and body['automaticCoreDispatchAuthorized'] is False and body['coreExecutesWorkbenchJobs'] is False

def test_capabilities_advertise_v840():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.10.0'
    for key in ('interactiveExecutionConsole','executionConsoleDurableJobs','executionConsoleExplicitDispatch','executionConsoleJobComparison','executionConsoleCorePlanning'):
        assert caps['coreIntegration'][key] is True

import json
from fastapi.testclient import TestClient
from app.main import app
from app.v510 import content_hash
from app.v840 import _job_path
from app.v920 import _state_path
c=TestClient(app)

def seed_project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    project='p940'; env_key='env-'+project
    spec={'environmentKey':env_key,'title':'Uncertainty environment','projectEntityId':project,'components':[]}
    env=c.post('/research-environment/build',json={'environment':spec}); assert env.status_code==200,env.text
    saved=c.post('/research-environment/persistence/save',json={'researchEnvironment':env.json(),'expectedCurrentRevision':0,'reason':'v940-test'}); assert saved.status_code==200,saved.text
    built=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Uncertainty Study','researchQuestion':'How uncertain are outputs?','objectives':['quantify uncertainty'],'activeEnvironmentKey':env_key,'activeEnvironmentRevision':1}}); assert built.status_code==200,built.text
    saved_project=c.post('/research-projects/save',json={'workspace':built.json(),'expectedProjectRevision':0,'reason':'v940-test'}); assert saved_project.status_code==200,saved_project.text
    return project

def base_payload(p,method='monte-carlo'):
    return {'projectKey':p,'studyKey':'u1','title':'U','samplingMethod':method,'sampleCount':16,'seed':42,'uncertainInputs':[{'path':'parameters.x','distribution':'uniform','minimum':0,'maximum':1},{'path':'parameters.z','distribution':'normal','mean':0,'stdDev':1}]}

def test_manifest_and_status():
    m=c.get('/uncertainty-sensitivity/manifest').json(); assert m['ok'] and m['version']=='9.7.0'
    assert m['capabilities']['monteCarloSampling'] and m['capabilities']['sobolSampling']
    assert m['boundaries']['automaticParameterImportanceRanking'] is False
    s=c.get('/v940/status').json(); assert s['uncertaintySensitivityStudyComposer'] and s['automaticCausalImportanceInference'] is False

def test_monte_carlo_is_deterministic(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); x=base_payload(p)
    a=c.post('/uncertainty-sensitivity/compose',json=x).json(); b=c.post('/uncertainty-sensitivity/compose',json=x).json()
    assert a['studyHash']==b['studyHash'] and a['samples']==b['samples'] and len(a['samples'])==16

def test_lhs_and_sobol_supported(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path)
    for m in ('latin-hypercube','sobol'):
        d=c.post('/uncertainty-sensitivity/compose',json=base_payload(p,m)).json(); assert d['samplingMethod']==m and len(d['samples'])==16

def test_distribution_validation(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); x=base_payload(p); x['uncertainInputs']=[{'path':'x','distribution':'uniform','minimum':2,'maximum':1}]
    assert c.post('/uncertainty-sensitivity/compose',json=x).status_code==422

def test_save_idempotent(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); x={**base_payload(p),'createdBy':'tester'}
    a=c.post('/uncertainty-sensitivity/studies',json=x).json(); b=c.post('/uncertainty-sensitivity/studies',json=x).json()
    assert a['idempotent'] is False and b['idempotent'] is True and a['studyHash']==b['studyHash']

def test_catalog_lists_studies(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); c.post('/uncertainty-sensitivity/studies',json={**base_payload(p),'createdBy':'tester'})
    d=c.get(f'/uncertainty-sensitivity/source-catalog/{p}').json(); assert d['studyCount']==1 and d['boundaries']['catalogExecutesJobs'] is False

def test_core_plan_preserves_authority(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); a=c.post('/uncertainty-sensitivity/studies',json={**base_payload(p),'createdBy':'tester'}).json()
    d=c.post('/integration/core/uncertainty-sensitivity/plan',json={'projectKey':p,'studyHash':a['studyHash'],'createdBy':'tester'}).json()
    assert d['bindingPlan']['objectType']=='workbench.uncertainty-sensitivity-study' and d['boundaries']['automaticCoreDispatchAuthorized'] is False

def test_capability_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.7.0'
    for k in ('uncertaintySensitivityStudyComposer','uncertaintySensitivityMonteCarloSampling','uncertaintySensitivityLatinHypercubeSampling','uncertaintySensitivitySobolSampling','uncertaintySensitivityCampaignAnalysis','uncertaintySensitivityContentAddressedStudies','uncertaintySensitivityCorePlanning'): assert caps['coreIntegration'][k] is True

def test_sensitivity_statistics_are_neutral(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path)
    from app.v920 import _campaign_path,_state_path,_state_hash,STATE_SCHEMA
    from app.v810 import _atomic_json_write
    campaign_hash='a'*64
    campaign={'ok':True,'schema':'sc-workbench-computational-campaign/1.0','version':'9.7.0','projectKey':p,'campaignHash':campaign_hash,'campaignRef':f'sc://workbench/campaign/{p}/{campaign_hash}','campaignKey':'c','title':'C','plannedRunCount':5,'recordLabel':'C','createdBy':'test','createdAt':'2026-09-25T00:00:00Z'}
    campaign['recordHash']=content_hash({k:v for k,v in campaign.items() if k not in {'createdAt','recordHash','idempotent'}})
    _campaign_path(p,campaign_hash).parent.mkdir(parents=True,exist_ok=True); _atomic_json_write(_campaign_path(p,campaign_hash),campaign)
    jobs={}
    for i,x in enumerate([1,2,3,4,5],1):
        jid=f'u{i}'; path=_job_path(jid); path.parent.mkdir(parents=True,exist_ok=True); result={'metrics':{'y':2*x+1}}; req={'x':x}; job={'ok':True,'schema':'sc-workbench-execution-job/1.0','version':'9.7.0','jobId':jid,'projectKey':p,'runtimeKind':'unified','label':jid,'tags':[],'metadata':{'parameterValues':{'parameters.x':x}},'status':'completed','jobRevision':1,'request':req,'requestHash':content_hash(req),'result':result,'resultHash':content_hash(result),'jobHash':'','createdAt':'2026-09-25T00:00:00Z','updatedAt':'2026-09-25T00:00:00Z','startedAt':'2026-09-25T00:00:00Z','completedAt':'2026-09-25T00:00:00Z','scientificExecutionPerformed':True}; job['jobHash']=content_hash({k:v for k,v in job.items() if k!='jobHash'}); path.write_text(json.dumps(job)); jobs[str(i)]={'jobId':jid,'status':'completed','resultHash':job['resultHash'],'parameterValues':{'parameters.x':x}}
    state={'ok':True,'schema':STATE_SCHEMA,'version':'9.7.0','projectKey':p,'campaignHash':campaign_hash,'campaignRef':campaign['campaignRef'],'stateRevision':1,'updatedAt':'2026-09-25T00:00:00Z','jobs':jobs,'summary':{'planned':5,'completed':5},'automaticQueueingPerformed':False,'automaticExecutionPerformed':False,'automaticAnalysisPerformed':False,'automaticCoreDispatchPerformed':False}; state['stateHash']=_state_hash(state); _state_path(p,campaign_hash).parent.mkdir(parents=True,exist_ok=True); _atomic_json_write(_state_path(p,campaign_hash),state)
    r=c.post('/uncertainty-sensitivity/analyze',json={'projectKey':p,'campaignHash':campaign_hash,'resultMetricPath':'metrics.y','parameterPaths':['parameters.x'],'methods':['pearson','spearman','standardized-regression']}); assert r.status_code==200,r.text
    d=r.json(); assert abs(d['results']['pearson']['parameters.x']['coefficient']-1)<1e-10 and d['results']['pearson']['parameters.x']['causalImportanceInferred'] is False
    assert d['results']['standardized-regression']['importanceRankGenerated'] is False and d['outputUncertainty']['count']==5

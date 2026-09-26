import json
from fastapi.testclient import TestClient
from app.main import app
from app.v510 import content_hash
from app.v810 import _atomic_json_write
from app.v840 import _job_path, _job_hash
from app.v920 import _campaign_path, _state_path, _state_hash, STATE_SCHEMA
c = TestClient(app)


def seed_project(monkeypatch, tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    project='p950'; env_key='env-'+project
    env=c.post('/research-environment/build',json={'environment':{'environmentKey':env_key,'title':'Calibration environment','projectEntityId':project,'components':[]}}); assert env.status_code==200,env.text
    saved=c.post('/research-environment/persistence/save',json={'researchEnvironment':env.json(),'expectedCurrentRevision':0,'reason':'v950-test'}); assert saved.status_code==200,saved.text
    built=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Calibration Study','researchQuestion':'What parameter values reproduce the observations?','objectives':['estimate parameters'],'activeEnvironmentKey':env_key,'activeEnvironmentRevision':1}}); assert built.status_code==200,built.text
    sp=c.post('/research-projects/save',json={'workspace':built.json(),'expectedProjectRevision':0,'reason':'v950-test'}); assert sp.status_code==200,sp.text
    return project


def seed_campaign(project):
    ch='b'*64
    campaign={'ok':True,'schema':'sc-workbench-computational-campaign/1.0','version':'9.9.0','projectKey':project,'campaignHash':ch,'campaignRef':f'sc://workbench/campaign/{project}/{ch}','campaignKey':'cal','title':'Calibration campaign','status':'completed','runtimeKind':'unified','protocolHash':'c'*64,'studyHash':'d'*64,'plannedRunCount':6,'recordLabel':'Calibration campaign','createdBy':'test','createdAt':'2026-09-26T00:00:00Z'}
    campaign['recordHash']=content_hash({k:v for k,v in campaign.items() if k not in {'createdAt','recordHash','idempotent'}})
    _campaign_path(project,ch).parent.mkdir(parents=True,exist_ok=True); _atomic_json_write(_campaign_path(project,ch),campaign)
    points=[(0,0),(1,0),(0,1),(2,1),(1,3),(4,2)]
    jobs={}
    for i,(x,z) in enumerate(points,1):
        jid=f'cal-{i}'; result={'metrics':{'y1':2*x+z,'y2':x-z}}
        req={'x':x,'z':z}
        job={'ok':True,'schema':'sc-workbench-execution-job/1.0','version':'9.9.0','jobId':jid,'projectKey':project,'runtimeKind':'unified','label':jid,'tags':[],'metadata':{'parameterValues':{'parameters.x':x,'parameters.z':z}},'status':'completed','jobRevision':1,'request':req,'requestHash':content_hash(req),'result':result,'resultHash':content_hash(result),'jobHash':'','createdAt':'2026-09-26T00:00:00Z','updatedAt':'2026-09-26T00:00:00Z','startedAt':'2026-09-26T00:00:00Z','completedAt':'2026-09-26T00:00:00Z','scientificExecutionPerformed':True}
        job['jobHash']=_job_hash(job); p=_job_path(jid); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(job))
        jobs[str(i)]={'jobId':jid,'status':'completed','resultHash':job['resultHash'],'parameterValues':{'parameters.x':x,'parameters.z':z}}
    state={'ok':True,'schema':STATE_SCHEMA,'version':'9.9.0','projectKey':project,'campaignHash':ch,'campaignRef':campaign['campaignRef'],'stateRevision':1,'updatedAt':'2026-09-26T00:00:00Z','jobs':jobs,'summary':{'planned':6,'completed':6},'automaticQueueingPerformed':False,'automaticExecutionPerformed':False,'automaticAnalysisPerformed':False,'automaticCoreDispatchPerformed':False}
    state['stateHash']=_state_hash(state); _state_path(project,ch).parent.mkdir(parents=True,exist_ok=True); _atomic_json_write(_state_path(project,ch),state)
    return ch


def payload(project,ch,estimator='linear-response-surface',loss='weighted-least-squares'):
    return {'projectKey':project,'calibrationKey':'fit-1','title':'Fit parameters','campaignHash':ch,'estimator':estimator,'loss':loss,'parameters':[{'path':'parameters.x','lower':0,'upper':5,'initial':2.5},{'path':'parameters.z','lower':0,'upper':5,'initial':2.5}],'targets':[{'metricPath':'metrics.y1','observedValue':8,'weight':1},{'metricPath':'metrics.y2','observedValue':1,'weight':1}],'confidenceLevel':0.95}


def test_manifest_and_status():
    m=c.get('/model-calibration/manifest').json(); assert m['ok'] and m['version']=='9.9.0'
    assert m['capabilities']['boundedParameterEstimation'] and m['capabilities']['robustHuberCalibration']
    assert m['boundaries']['automaticPreferredModelSelection'] is False
    s=c.get('/v950/status').json(); assert s['modelCalibrationParameterEstimation'] and s['automaticModelValidityInference'] is False


def test_linear_response_surface_recovers_known_parameters(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p)
    r=c.post('/model-calibration/estimate',json=payload(p,ch)); assert r.status_code==200,r.text
    d=r.json(); est=d['result']['estimatedParameters']
    assert abs(est['parameters.x']-3)<1e-8 and abs(est['parameters.z']-2)<1e-8
    assert d['result']['diagnostics']['fullColumnRank'] is True
    assert d['boundaries']['automaticModelValidityInference'] is False


def test_campaign_search_is_explicit_candidate_objective(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p)
    d=c.post('/model-calibration/estimate',json=payload(p,ch,'campaign-search')).json()
    assert d['result']['estimator']=='campaign-search' and len(d['result']['candidateScores'])==6
    assert d['result']['diagnostics']['continuousOptimizationPerformed'] is False


def test_huber_loss_supported(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p)
    d=c.post('/model-calibration/estimate',json=payload(p,ch,'linear-response-surface','huber')).json()
    assert d['result']['estimator']=='linear-response-surface' and d['loss']=='huber'


def test_compose_problem_is_content_addressed(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p); x=payload(p,ch)
    a=c.post('/model-calibration/compose',json=x).json(); b=c.post('/model-calibration/compose',json=x).json()
    assert a['problemHash']==b['problemHash'] and len(a['problemHash'])==64


def test_save_is_idempotent(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p); x={**payload(p,ch),'createdBy':'tester'}
    a=c.post('/model-calibration/calibrations',json=x).json(); b=c.post('/model-calibration/calibrations',json=x).json()
    assert a['idempotent'] is False and b['idempotent'] is True and a['calibrationHash']==b['calibrationHash']


def test_catalog_lists_calibration(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p); c.post('/model-calibration/calibrations',json={**payload(p,ch),'createdBy':'tester'})
    d=c.get(f'/model-calibration/source-catalog/{p}').json(); assert d['calibrationCount']==1 and d['boundaries']['catalogPerformsCalibration'] is False


def test_analysis_plan_is_plan_only(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p); a=c.post('/model-calibration/calibrations',json={**payload(p,ch),'createdBy':'tester'}).json()
    d=c.post('/model-calibration/analysis-plan',json={'projectKey':p,'calibrationHash':a['calibrationHash'],'createdBy':'tester'}).json()
    assert len(d['plannedHandoffs'])==2 and d['boundaries']['automaticAnalysisDispatch'] is False


def test_core_plan_preserves_authority(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p); a=c.post('/model-calibration/calibrations',json={**payload(p,ch),'createdBy':'tester'}).json()
    d=c.post('/integration/core/model-calibration/plan',json={'projectKey':p,'calibrationHash':a['calibrationHash'],'createdBy':'tester'}).json()
    assert d['bindingPlan']['objectType']=='workbench.model-calibration' and d['boundaries']['automaticCoreDispatchAuthorized'] is False


def test_rank_deficient_surface_rejected(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p); x=payload(p,ch)
    # Duplicate parameter paths are rejected before estimation.
    x['parameters'][1]['path']='parameters.x'
    assert c.post('/model-calibration/estimate',json=x).status_code==422


def test_parameter_bounds_validation(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ch=seed_campaign(p); x=payload(p,ch); x['parameters'][0]['lower']=5; x['parameters'][0]['upper']=1
    assert c.post('/model-calibration/compose',json=x).status_code==422


def test_capability_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.9.0'
    for k in ('modelCalibrationParameterEstimation','modelCalibrationCampaignObjectiveScoring','modelCalibrationBoundedEstimation','modelCalibrationRobustLoss','modelCalibrationIdentifiabilityDiagnostics','modelCalibrationContentAddressedRecords','modelCalibrationCorePlanning'): assert caps['coreIntegration'][k] is True

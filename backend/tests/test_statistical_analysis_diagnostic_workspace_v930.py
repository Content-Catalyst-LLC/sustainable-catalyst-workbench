import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.v510 import content_hash
from app.v840 import _job_path

c=TestClient(app)


def seed_project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    project='stats-project'; env_key='env-'+project
    spec={'environmentKey':env_key,'title':'Statistics environment','projectEntityId':project,'components':[]}
    env=c.post('/research-environment/build',json={'environment':spec}); assert env.status_code==200,env.text
    saved=c.post('/research-environment/persistence/save',json={'researchEnvironment':env.json(),'expectedCurrentRevision':0,'reason':'v930-test'}); assert saved.status_code==200,saved.text
    built=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Statistical Study','researchQuestion':'How do outputs vary?','objectives':['analyze completed results'],'activeEnvironmentKey':env_key,'activeEnvironmentRevision':1}}); assert built.status_code==200,built.text
    saved_project=c.post('/research-projects/save',json={'workspace':built.json(),'expectedProjectRevision':0,'reason':'v930-test'}); assert saved_project.status_code==200,saved_project.text
    return project


def write_job(tmp_path, project, jid, value, x=None, group=None):
    path=_job_path(jid); path.parent.mkdir(parents=True,exist_ok=True)
    params={}
    if x is not None: params['parameters.x']=x
    if group is not None: params['parameters.group']=group
    result={'metrics':{'y':value}}
    request={'operation':'evaluate','parameters':{'x':x,'group':group}}
    job={
      'ok':True,'schema':'sc-workbench-execution-job/1.0','version':'9.6.0','jobId':jid,'projectKey':project,
      'runtimeKind':'unified','label':jid,'tags':['stats'],'metadata':{'parameterValues':params},'status':'completed','jobRevision':1,
      'request':request,'requestHash':content_hash(request),'result':result,'resultHash':content_hash(result),'jobHash':'',
      'createdAt':'2026-09-25T00:00:00Z','updatedAt':'2026-09-25T00:00:00Z','startedAt':'2026-09-25T00:00:00Z','completedAt':'2026-09-25T00:00:00Z',
      'scientificExecutionPerformed':True,
    }
    job['jobHash']=content_hash({k:v for k,v in job.items() if k!='jobHash'})
    path.write_text(json.dumps(job))
    return jid


def payload(project,ids,methods=None):
    return {'projectKey':project,'analysisKey':'a1','title':'Statistical analysis','jobIds':ids,'resultMetricPath':'metrics.y','methods':methods or ['descriptive','distribution-diagnostics'],'confidenceLevel':0.95}


def test_manifest_status_boundaries():
    m=c.get('/statistical-workspace/manifest').json(); assert m['ok'] and m['version']=='9.6.0'
    assert m['capabilities']['linearRegressionDiagnostics'] and m['boundaries']['automaticSignificanceDecision'] is False
    s=c.get('/v930/status').json(); assert s['statisticalAnalysisDiagnosticWorkspace'] and s['automaticCausalInference'] is False


def test_descriptive_and_distribution(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ids=[write_job(tmp_path,p,f'j{i}',v) for i,v in enumerate([1,2,3,4,5],1)]
    r=c.post('/statistical-workspace/analyze',json=payload(p,ids)); assert r.status_code==200,r.text
    d=r.json(); assert d['observationCount']==5 and d['results']['descriptive']['mean']==3.0
    assert d['results']['descriptive']['meanConfidenceInterval'][0] < 3 < d['results']['descriptive']['meanConfidenceInterval'][1]
    assert d['results']['distribution-diagnostics']['diagnosticDecisionGenerated'] is False


def test_shapiro_returns_statistic_not_decision(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ids=[write_job(tmp_path,p,f'j{i}',v) for i,v in enumerate([1,2,3,4,5],1)]
    d=c.post('/statistical-workspace/analyze',json=payload(p,ids,['normality-shapiro'])).json()
    assert d['results']['normality-shapiro']['pValue'] is not None and d['results']['normality-shapiro']['normalityDecisionGenerated'] is False


def test_one_sample_t_requires_reference(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ids=[write_job(tmp_path,p,'j1',1),write_job(tmp_path,p,'j2',2)]
    x=payload(p,ids,['one-sample-t']); r=c.post('/statistical-workspace/analyze',json=x); assert r.status_code==422
    x['referenceValue']=0; d=c.post('/statistical-workspace/analyze',json=x).json(); assert d['results']['one-sample-t']['hypothesisDecisionGenerated'] is False


def test_group_tests_are_explicit_and_neutral(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ids=[]
    for i,v in enumerate([1,2,3]): ids.append(write_job(tmp_path,p,f'a{i}',v,group='A'))
    for i,v in enumerate([4,5,6]): ids.append(write_job(tmp_path,p,f'b{i}',v,group='B'))
    x=payload(p,ids,['variance-diagnostic-levene','independent-t','one-way-anova','kruskal-wallis']); x['groupParameterPath']='parameters.group'
    d=c.post('/statistical-workspace/analyze',json=x).json(); assert d['results']['independent-t']['significanceDecisionGenerated'] is False
    assert d['results']['one-way-anova']['etaSquared'] is not None and d['results']['variance-diagnostic-levene']['varianceDecisionGenerated'] is False


def test_correlation_and_regression_residual_diagnostics(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ids=[write_job(tmp_path,p,f'j{i}',2*x+1,x=x) for i,x in enumerate([1,2,3,4,5],1)]
    x=payload(p,ids,['pearson-correlation','spearman-correlation','linear-regression']); x['predictorParameterPath']='parameters.x'
    d=c.post('/statistical-workspace/analyze',json=x).json(); reg=d['results']['linear-regression']
    assert abs(reg['slope']-2)<1e-10 and abs(reg['intercept']-1)<1e-10 and reg['modelValidityInferred'] is False
    assert reg['residualDiagnostics']['rmse'] < 1e-10 and d['results']['pearson-correlation']['causalInterpretationGenerated'] is False


def test_missing_metric_rows_are_excluded(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); good=write_job(tmp_path,p,'good',3)
    bad=write_job(tmp_path,p,'bad',4); path=_job_path('bad'); j=json.loads(path.read_text()); j['result']={'other':1}; j['resultHash']=content_hash(j['result']); j['jobHash']=content_hash({k:v for k,v in j.items() if k!='jobHash'}); path.write_text(json.dumps(j))
    d=c.post('/statistical-workspace/analyze',json=payload(p,[good,bad],['descriptive'])).json(); assert d['observationCount']==1 and d['excludedObservationCount']==1


def test_save_is_content_addressed_and_integrity_checked(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ids=[write_job(tmp_path,p,'j1',1),write_job(tmp_path,p,'j2',2),write_job(tmp_path,p,'j3',3)]
    x={**payload(p,ids,['descriptive']),'createdBy':'tester'}
    a=c.post('/statistical-workspace/analyses',json=x); assert a.status_code==200,a.text; d=a.json(); assert d['idempotent'] is False
    b=c.post('/statistical-workspace/analyses',json=x).json(); assert b['idempotent'] is True and b['analysisHash']==d['analysisHash']
    got=c.get(f"/statistical-workspace/analyses/{p}/{d['analysisHash']}").json(); assert got['recordHash']==d['recordHash']


def test_catalog_lists_completed_jobs_and_analyses(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ids=[write_job(tmp_path,p,'j1',1),write_job(tmp_path,p,'j2',2)]
    c.post('/statistical-workspace/analyses',json={**payload(p,ids,['descriptive']),'createdBy':'tester'})
    d=c.get(f'/statistical-workspace/source-catalog/{p}').json(); assert d['completedJobCount']==2 and d['analysisCount']==1 and d['boundaries']['catalogRunsAnalysis'] is False


def test_core_plan_preserves_governance(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ids=[write_job(tmp_path,p,'j1',1),write_job(tmp_path,p,'j2',2)]
    a=c.post('/statistical-workspace/analyses',json={**payload(p,ids,['descriptive']),'createdBy':'tester'}).json()
    r=c.post('/integration/core/statistical-workspace/plan',json={'projectKey':p,'analysisHash':a['analysisHash'],'coreProjectEntityId':'core-p','createdBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['bindingPlan']['objectType']=='workbench.statistical-analysis' and d['boundaries']['automaticCoreDispatchAuthorized'] is False and d['boundaries']['coreGovernanceAuthorityPreserved'] is True


def test_capability_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.6.0'
    for key in ('statisticalAnalysisDiagnosticWorkspace','statisticalAnalysisDescriptiveStatistics','statisticalAnalysisDiagnostics','statisticalAnalysisHypothesisStatistics','statisticalAnalysisRegressionDiagnostics','statisticalAnalysisContentAddressedRecords','statisticalAnalysisCorePlanning'):
        assert caps['coreIntegration'][key] is True


def test_group_and_predictor_methods_require_paths(monkeypatch,tmp_path):
    p=seed_project(monkeypatch,tmp_path); ids=[write_job(tmp_path,p,'j1',1),write_job(tmp_path,p,'j2',2)]
    assert c.post('/statistical-workspace/analyze',json=payload(p,ids,['independent-t'])).status_code==422
    assert c.post('/statistical-workspace/analyze',json=payload(p,ids,['linear-regression'])).status_code==422


def test_no_scientific_decision_flags_enabled():
    b=c.get('/statistical-workspace/manifest').json()['boundaries']; assert all(v is False for v in b.values())

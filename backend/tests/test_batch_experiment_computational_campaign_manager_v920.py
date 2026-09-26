from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)


def seed(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    project='p-v920'; env_key='env-'+project
    spec={'environmentKey':env_key,'title':'Campaign environment','projectEntityId':project,'components':[]}
    env=c.post('/research-environment/build',json={'environment':spec}); assert env.status_code==200,env.text
    saved=c.post('/research-environment/persistence/save',json={'researchEnvironment':env.json(),'expectedCurrentRevision':0,'reason':'v920-test'}); assert saved.status_code==200,saved.text
    built=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Campaign project','researchQuestion':'How does parameter x affect output?','objectives':['explore parameter response'],'activeEnvironmentKey':env_key,'activeEnvironmentRevision':1}}); assert built.status_code==200,built.text
    saved_project=c.post('/research-projects/save',json={'workspace':built.json(),'expectedProjectRevision':0,'reason':'v920-test'}); assert saved_project.status_code==200,saved_project.text
    study=c.post('/study-composer/studies',json={'projectKey':project,'studyKey':'study-1','title':'Campaign study','researchQuestion':'How does parameter x affect output?','objectives':['explore parameter response'],'protocol':{'designType':'simulation','methods':['parameter sweep']},'status':'active','createdBy':'test'}); assert study.status_code==200,study.text
    protocol={
      'projectKey':project,'studyHash':study.json()['studyHash'],'protocolKey':'protocol-001','title':'Campaign protocol','protocolVersion':'1.0','status':'draft',
      'hypotheses':[{'hypothesisId':'h1','statement':'Output changes as x changes','kind':'primary'}],
      'variables':[{'variableId':'x','label':'X','role':'treatment','dataType':'continuous'},{'variableId':'y','label':'Y','role':'outcome','dataType':'continuous'}],
      'sampling':{'population':'simulated systems','method':'simulation','targetSampleSize':6},
      'measurement':{'primaryOutcomeIds':['y']},
      'analysis':{'primaryEstimand':'response across x','statisticalMethods':['descriptive comparison']},
      'stopping':{'ruleType':'fixed','target':'six planned runs'},'createdBy':'tester'
    }
    pr=c.post('/protocol-builder/protocols',json=protocol); assert pr.status_code==200,pr.text
    return project,pr.json()['protocolHash']


def campaign_payload(project,protocol):
    return {
      'projectKey':project,'protocolHash':protocol,'campaignKey':'sweep-001','title':'Parameter sweep campaign','status':'ready','runtimeKind':'unified',
      'requestTemplate':{'operation':'evaluate','parameters':{'x':0,'alpha':1}},
      'parameterAxes':[{'path':'parameters.x','label':'X','values':[1,2,3]}],
      'replications':2,'budget':{'maxRuns':10,'maxPreparedJobs':6,'maxFailures':2,'maxWallMinutes':120},'tags':['sweep'],'notes':'researcher-defined sweep'
    }


def test_manifest_status_and_boundaries():
    m=c.get('/campaign-manager/manifest').json(); assert m['ok'] and m['version']=='9.11.0'
    assert m['capabilities']['deterministicCartesianParameterSweeps'] and m['capabilities']['resumableCampaignState']
    assert all(v is False for v in m['boundaries'].values())
    s=c.get('/v920/status').json(); assert s['batchExperimentComputationalCampaignManager'] and s['automaticJobExecution'] is False


def test_compose_cartesian_runs_is_deterministic(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); p=campaign_payload(project,protocol)
    a=c.post('/campaign-manager/compose',json=p); b=c.post('/campaign-manager/compose',json=p); assert a.status_code==200 and b.status_code==200
    x=a.json(); y=b.json(); assert x['plannedRunCount']==6 and x['campaignHash']==y['campaignHash']
    assert [r['parameterValues']['parameters.x'] for r in x['plannedRuns']]==[1,1,2,2,3,3]
    assert x['plannedRuns'][0]['request']['parameters']['x']==1


def test_multiple_axes_expand_cartesian_product(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); p=campaign_payload(project,protocol)
    p['parameterAxes'].append({'path':'parameters.alpha','values':[0.1,0.2]}); p['replications']=1
    d=c.post('/campaign-manager/compose',json=p).json(); assert d['plannedRunCount']==6
    combos={(r['parameterValues']['parameters.x'],r['parameterValues']['parameters.alpha']) for r in d['plannedRuns']}; assert len(combos)==6


def test_budget_blocks_oversized_campaign(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); p=campaign_payload(project,protocol); p['budget']['maxRuns']=5
    r=c.post('/campaign-manager/compose',json=p); assert r.status_code==422 and 'budget.maxRuns' in r.text


def test_invalid_axis_paths_and_duplicate_values_rejected(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); p=campaign_payload(project,protocol); p['parameterAxes']=[{'path':'parameters[x]','values':[1,2]}]
    assert c.post('/campaign-manager/compose',json=p).status_code==422
    p=campaign_payload(project,protocol); p['parameterAxes']=[{'path':'parameters.x','values':[1,1]}]
    assert c.post('/campaign-manager/compose',json=p).status_code==422


def test_save_is_content_addressed_and_initializes_state(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); p={**campaign_payload(project,protocol),'createdBy':'tester'}
    a=c.post('/campaign-manager/campaigns',json=p); assert a.status_code==200,a.text; x=a.json(); assert x['idempotent'] is False
    b=c.post('/campaign-manager/campaigns',json=p).json(); assert b['idempotent'] is True and b['campaignHash']==x['campaignHash']
    st=c.get(f"/campaign-manager/campaigns/{project}/{x['campaignHash']}/state").json(); assert st['summary']['planned']==6 and st['summary']['materialized']==0


def test_materialize_creates_prepared_jobs_only(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); saved=c.post('/campaign-manager/campaigns',json={**campaign_payload(project,protocol),'createdBy':'tester'}).json()
    r=c.post('/campaign-manager/materialize',json={'projectKey':project,'campaignHash':saved['campaignHash'],'limit':2,'actor':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['createdJobCount']==2 and d['automaticQueueingPerformed'] is False and d['automaticExecutionPerformed'] is False
    assert d['state']['summary']['prepared']==2 and d['state']['summary']['unmaterialized']==4
    for row in d['createdJobs']:
        job=c.get('/execution-console/jobs/'+row['jobId']).json(); assert job['status']=='prepared' and job['scientificExecutionPerformed'] is False


def test_materialize_is_resumable_and_does_not_duplicate(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); saved=c.post('/campaign-manager/campaigns',json={**campaign_payload(project,protocol),'createdBy':'tester'}).json(); h=saved['campaignHash']
    a=c.post('/campaign-manager/materialize',json={'projectKey':project,'campaignHash':h,'limit':2}).json(); ids1={x['jobId'] for x in a['createdJobs']}
    b=c.post('/campaign-manager/materialize',json={'projectKey':project,'campaignHash':h,'limit':2}).json(); ids2={x['jobId'] for x in b['createdJobs']}
    assert ids1.isdisjoint(ids2) and b['state']['summary']['materialized']==4


def test_prepared_job_budget_caps_materialization(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); p=campaign_payload(project,protocol); p['budget']['maxPreparedJobs']=3
    saved=c.post('/campaign-manager/campaigns',json={**p,'createdBy':'tester'}).json(); h=saved['campaignHash']
    d=c.post('/campaign-manager/materialize',json={'projectKey':project,'campaignHash':h,'limit':10}).json(); assert d['createdJobCount']==3 and d['state']['summary']['materialized']==3
    e=c.post('/campaign-manager/materialize',json={'projectKey':project,'campaignHash':h,'limit':10}).json(); assert e['createdJobCount']==0


def test_refresh_tracks_job_status_without_running_it(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); saved=c.post('/campaign-manager/campaigns',json={**campaign_payload(project,protocol),'createdBy':'tester'}).json(); h=saved['campaignHash']
    m=c.post('/campaign-manager/materialize',json={'projectKey':project,'campaignHash':h,'limit':1}).json(); jid=m['createdJobs'][0]['jobId']
    job=c.get('/execution-console/jobs/'+jid).json(); q=c.post(f'/execution-console/jobs/{jid}/queue',json={'expectedJobRevision':job['jobRevision'],'actor':'tester','reason':'explicit-test-queue'}); assert q.status_code==200
    d=c.post('/campaign-manager/refresh',json={'projectKey':project,'campaignHash':h}).json(); assert d['state']['summary']['queued']==1 and d['state']['automaticExecutionPerformed'] is False


def test_analysis_plan_is_neutral(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); saved=c.post('/campaign-manager/campaigns',json={**campaign_payload(project,protocol),'createdBy':'tester'}).json(); h=saved['campaignHash']
    d=c.post('/campaign-manager/analysis-plan',json={'projectKey':project,'campaignHash':h}).json(); assert d['completedRunCount']==0 and 'comparative-analysis' in d['suggestedTargets']
    assert d['boundaries']['automaticWinnerSelectionAuthorized'] is False and d['boundaries']['scientificValidityInferred'] is False


def test_core_plan_preserves_governance_boundary(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); saved=c.post('/campaign-manager/campaigns',json={**campaign_payload(project,protocol),'createdBy':'tester'}).json(); h=saved['campaignHash']
    r=c.post('/integration/core/campaign-manager/plan',json={'projectKey':project,'campaignHash':h,'coreProjectEntityId':'core-p','createdBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['bindingPlan']['objectType']=='workbench.computational-campaign' and d['boundaries']['automaticCoreDispatchAuthorized'] is False and d['boundaries']['coreGovernanceAuthorityPreserved'] is True


def test_source_catalog_and_capability_flags(monkeypatch,tmp_path):
    project,protocol=seed(monkeypatch,tmp_path); c.post('/campaign-manager/campaigns',json={**campaign_payload(project,protocol),'createdBy':'tester'})
    cat=c.get(f'/campaign-manager/source-catalog/{project}').json(); assert cat['protocolCount']==1 and cat['campaignCount']==1 and cat['boundaries']['catalogRunsJobs'] is False
    caps=c.get('/capabilities').json(); assert caps['version']=='9.11.0'
    for key in ('batchExperimentComputationalCampaignManager','computationalCampaignDeterministicSweeps','computationalCampaignResumableState','computationalCampaignExecutionMaterialization','computationalCampaignAnalysisPlanning','computationalCampaignCorePlanning'):
        assert caps['coreIntegration'][key] is True

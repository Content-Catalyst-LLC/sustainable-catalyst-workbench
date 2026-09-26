import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)

def seed_project(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    project='p-v910'; env_key='env-'+project
    spec={'environmentKey':env_key,'title':'Protocol environment','projectEntityId':project,'components':[]}
    env=c.post('/research-environment/build',json={'environment':spec}); assert env.status_code==200,env.text
    saved=c.post('/research-environment/persistence/save',json={'researchEnvironment':env.json(),'expectedCurrentRevision':0,'reason':'v910-test'}); assert saved.status_code==200,saved.text
    built=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Protocol project','researchQuestion':'Does treatment change outcome?','objectives':['estimate effect'],'activeEnvironmentKey':env_key,'activeEnvironmentRevision':1}}); assert built.status_code==200,built.text
    saved_project=c.post('/research-projects/save',json={'workspace':built.json(),'expectedProjectRevision':0,'reason':'v910-test'}); assert saved_project.status_code==200,saved_project.text
    study=c.post('/study-composer/studies',json={'projectKey':project,'studyKey':'study-1','title':'Study','researchQuestion':'Does treatment change outcome?','objectives':['estimate effect'],'protocol':{'designType':'experiment','methods':['randomized design']},'status':'active','createdBy':'test'}); assert study.status_code==200,study.text
    return project,study.json()['studyHash']

def payload(project,study):
    return {
      'projectKey':project,'studyHash':study,'protocolKey':'protocol-001','title':'Randomized protocol','protocolVersion':'1.0','status':'draft',
      'hypotheses':[{'hypothesisId':'h1','statement':'Treatment changes outcome','kind':'primary','directional':True,'expectedDirection':'increase'}],
      'variables':[{'variableId':'trt','label':'Treatment','role':'treatment','dataType':'categorical'},{'variableId':'y','label':'Outcome','role':'outcome','dataType':'continuous','unit':'score'},{'variableId':'age','label':'Age','role':'covariate','dataType':'continuous','unit':'years'}],
      'arms':[{'armId':'control','label':'Control','kind':'control','allocationWeight':1},{'armId':'active','label':'Active','kind':'treatment','intervention':'treatment A','allocationWeight':1}],
      'sampling':{'population':'Eligible participants','method':'simple-random','targetSampleSize':120,'inclusionCriteria':['adult'],'sampleSizeRationale':'Researcher-specified planning target'},
      'randomization':{'enabled':True,'unit':'participant','method':'blocked randomization','seedPolicy':'record seed','stratificationVariableIds':['age'],'blinding':'double'},
      'measurement':{'schedule':['baseline','week-8'],'instrumentRefs':['instrument://score'],'primaryOutcomeIds':['y'],'qualityControls':['range checks']},
      'analysis':{'primaryEstimand':'mean treatment effect','statisticalMethods':['linear model'],'covariateIds':['age'],'robustnessChecks':['unadjusted model'],'decisionCriteria':['report estimate and interval']},
      'stopping':{'ruleType':'fixed','target':'120 enrolled'},'tags':['experiment']
    }

def test_manifest_status_and_boundaries():
    m=c.get('/protocol-builder/manifest').json(); assert m['ok'] and m['version']=='9.4.0' and m['capabilities']['formalResearchProtocolObject']
    assert 'analysis' in m['protocolSections']; assert all(v is False for v in m['boundaries'].values())
    s=c.get('/v910/status').json(); assert s['experimentalDesignResearchProtocolBuilder'] and s['automaticExecutionDispatch'] is False

def test_compose_protocol_and_readiness(monkeypatch,tmp_path):
    project,study=seed_project(monkeypatch,tmp_path); r=c.post('/protocol-builder/compose',json=payload(project,study)); assert r.status_code==200,r.text
    d=r.json(); assert d['version']=='9.4.0' and len(d['protocolHash'])==64 and d['sourceHashes']['studyHash']==study
    sections={x['section']:x for x in d['sectionReadiness']}; assert sections['hypotheses']['ready'] and sections['variables']['ready'] and sections['analysis']['ready'] and sections['randomization']['ready']
    assert d['boundaries']['protocolCompletenessIsScientificValidity'] is False

def test_save_is_content_addressed_and_idempotent(monkeypatch,tmp_path):
    project,study=seed_project(monkeypatch,tmp_path); p={**payload(project,study),'createdBy':'tester'}
    a=c.post('/protocol-builder/protocols',json=p); assert a.status_code==200,a.text; x=a.json(); assert x['idempotent'] is False
    b=c.post('/protocol-builder/protocols',json=p); assert b.status_code==200,b.text; y=b.json(); assert y['idempotent'] is True and y['protocolHash']==x['protocolHash'] and y['recordHash']==x['recordHash']
    rows=c.get(f'/protocol-builder/protocols/{project}').json(); assert rows['protocolCount']==1
    got=c.get(f"/protocol-builder/protocols/{project}/{x['protocolHash']}").json(); assert got['recordHash']==x['recordHash']

def test_unknown_variable_reference_is_rejected(monkeypatch,tmp_path):
    project,study=seed_project(monkeypatch,tmp_path); p=payload(project,study); p['analysis']['covariateIds']=['missing']
    r=c.post('/protocol-builder/compose',json=p); assert r.status_code==422

def test_outcome_role_is_enforced(monkeypatch,tmp_path):
    project,study=seed_project(monkeypatch,tmp_path); p=payload(project,study); p['measurement']['primaryOutcomeIds']=['trt']
    assert c.post('/protocol-builder/compose',json=p).status_code==422

def test_preregistered_requires_reference(monkeypatch,tmp_path):
    project,study=seed_project(monkeypatch,tmp_path); p=payload(project,study); p['status']='preregistered'
    assert c.post('/protocol-builder/compose',json=p).status_code==422
    p['preregistrationRef']='https://registry.example/protocol-1'; assert c.post('/protocol-builder/compose',json=p).status_code==200

def test_amendment_requires_reason(monkeypatch,tmp_path):
    project,study=seed_project(monkeypatch,tmp_path); p=payload(project,study); p['status']='amended'
    assert c.post('/protocol-builder/compose',json=p).status_code==422
    p['amendmentReason']='Changed measurement schedule before analysis'; assert c.post('/protocol-builder/compose',json=p).status_code==200

def test_execution_plan_is_explicit_and_non_dispatching(monkeypatch,tmp_path):
    project,study=seed_project(monkeypatch,tmp_path); s=c.post('/protocol-builder/protocols',json={**payload(project,study),'createdBy':'tester'}).json()
    r=c.post('/protocol-builder/execution-plan',json={'projectKey':project,'protocolHash':s['protocolHash'],'runtimeKind':'python','requestedBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['executionContract']['analysis']['primaryEstimand']=='mean treatment effect' and d['boundaries']['automaticExecutionDispatchAuthorized'] is False and len(d['planHash'])==64

def test_core_plan_preserves_governance_boundary(monkeypatch,tmp_path):
    project,study=seed_project(monkeypatch,tmp_path); s=c.post('/protocol-builder/protocols',json={**payload(project,study),'createdBy':'tester'}).json()
    r=c.post('/integration/core/protocol-builder/plan',json={'projectKey':project,'protocolHash':s['protocolHash'],'coreProjectEntityId':'core-p','createdBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['bindingPlan']['objectType']=='workbench.research-protocol' and d['boundaries']['automaticCoreDispatchAuthorized'] is False and d['boundaries']['coreGovernanceAuthorityPreserved'] is True

def test_source_catalog_and_capability_flags(monkeypatch,tmp_path):
    project,study=seed_project(monkeypatch,tmp_path); c.post('/protocol-builder/protocols',json={**payload(project,study),'createdBy':'tester'})
    cat=c.get(f'/protocol-builder/source-catalog/{project}').json(); assert cat['studyCount']==1 and cat['protocolCount']==1 and cat['boundaries']['catalogMutatesSources'] is False
    caps=c.get('/capabilities').json(); assert caps['version']=='9.4.0'
    for key in ('experimentalDesignResearchProtocolBuilder','researchProtocolContentAddressedRecords','researchProtocolPreregistrationMetadata','researchProtocolExecutionPlanning','researchProtocolCorePlanning'): assert caps['coreIntegration'][key] is True

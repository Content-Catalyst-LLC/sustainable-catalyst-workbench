import json
from fastapi.testclient import TestClient
from app.main import app
from app.v810 import _atomic_json_write, _store_root
from app.v510 import content_hash

c=TestClient(app)

def seed_project(monkeypatch,tmp_path,project='study-demo'):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    env_key='env-'+project
    spec={'environmentKey':env_key,'title':'Study environment','projectEntityId':project,'components':[]}
    env=c.post('/research-environment/build',json={'environment':spec}); assert env.status_code==200,env.text
    env_body=env.json()
    saved=c.post('/research-environment/persistence/save',json={'researchEnvironment':env_body,'expectedCurrentRevision':0,'reason':'v900-test'}); assert saved.status_code==200,saved.text
    built=c.post('/research-projects/build',json={'project':{'projectKey':project,'title':'Study demo','researchQuestion':'How does x change y?','objectives':['estimate effect'],'activeEnvironmentKey':env_key,'activeEnvironmentRevision':1}}); assert built.status_code==200,built.text
    saved_project=c.post('/research-projects/save',json={'workspace':built.json(),'expectedProjectRevision':0,'reason':'v900-test'}); assert saved_project.status_code==200,saved_project.text
    return project

def base_payload(project):
    return {'projectKey':project,'studyKey':'study-001','title':'Unified study','researchQuestion':'How does x change y?','objectives':['estimate effect'],'protocol':{'designType':'simulation','methods':['define model','execute runs']},'status':'active'}

def test_manifest_status_and_boundaries():
    m=c.get('/study-composer/manifest').json(); assert m['ok'] and m['version']=='9.11.0' and m['capabilities']['topLevelScientificStudyObject']
    assert m['studyStages']==['question','protocol','inputs','execution','analysis','publication']
    assert all(v is False for v in m['boundaries'].values())
    s=c.get('/v900/status').json(); assert s['unifiedScientificStudyComposer'] and s['automaticCoreDispatch'] is False

def test_compose_reports_explicit_stage_readiness(monkeypatch,tmp_path):
    project=seed_project(monkeypatch,tmp_path); r=c.post('/study-composer/compose',json=base_payload(project)); assert r.status_code==200,r.text
    d=r.json(); assert d['version']=='9.11.0' and len(d['studyHash'])==64
    stages={x['stage']:x for x in d['stageReadiness']}; assert stages['question']['ready'] and stages['protocol']['ready']
    assert stages['inputs']['ready'] is False and stages['execution']['ready'] is False and stages['analysis']['ready'] is False and stages['publication']['ready'] is False
    assert d['boundaries']['stageReadinessIsScientificValidity'] is False

def test_content_addressed_study_save_is_idempotent(monkeypatch,tmp_path):
    project=seed_project(monkeypatch,tmp_path); payload={**base_payload(project),'createdBy':'tester','recordLabel':'Study record'}
    a=c.post('/study-composer/studies',json=payload); assert a.status_code==200,a.text; x=a.json(); assert x['idempotent'] is False
    b=c.post('/study-composer/studies',json=payload); assert b.status_code==200,b.text; y=b.json(); assert y['idempotent'] is True and y['studyHash']==x['studyHash'] and y['recordHash']==x['recordHash']
    rows=c.get(f'/study-composer/studies/{project}').json(); assert rows['studyCount']==1
    got=c.get(f"/study-composer/studies/{project}/{x['studyHash']}").json(); assert got['recordHash']==x['recordHash']

def test_source_catalog_and_core_plan_are_non_mutating(monkeypatch,tmp_path):
    project=seed_project(monkeypatch,tmp_path); cat=c.get(f'/study-composer/source-catalog/{project}'); assert cat.status_code==200,cat.text; d=cat.json(); assert d['catalogHash'] and d['boundaries']['catalogMutatesSources'] is False
    payload={**base_payload(project),'coreProjectEntityId':'core-project-1','visibility':'internal','createdBy':'tester'}
    plan=c.post('/integration/core/study-composer/plan',json=payload); assert plan.status_code==200,plan.text; p=plan.json(); assert p['bindingPlan']['objectType']=='workbench.unified-scientific-study' and p['boundaries']['automaticCoreDispatchAuthorized'] is False and len(p['planHash'])==64

def test_unknown_project_and_missing_source_fail_cleanly(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    assert c.get('/study-composer/source-catalog/missing').status_code==404
    project=seed_project(monkeypatch,tmp_path); payload={**base_payload(project),'assetKeys':['missing-asset']}; assert c.post('/study-composer/compose',json=payload).status_code==404

def test_capability_registry_exposes_v900_flags():
    caps=c.get('/capabilities').json(); assert caps['version']=='9.11.0'
    for key in ('unifiedScientificStudyComposer','scientificStudyStageReadiness','scientificStudyContentAddressedRecords','scientificStudyAnalysisSnapshotBinding','scientificStudyPublicationPackageBinding','scientificStudyCorePlanning'):
        assert caps['coreIntegration'][key] is True

from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def model_req(project='registry-project', version='1.0'):
    return {
        'projectKey': project, 'modelKey': 'climate-surrogate', 'versionLabel': version,
        'title': 'Climate surrogate model', 'provider': 'local', 'modelId': 'sc/climate-surrogate',
        'task': 'surrogate-modeling', 'artifactHash': 'a'*64, 'license': 'Apache-2.0',
        'compatibility': {'runtimeKinds':['ai-engineering','workspace-ml'], 'frameworks':['pytorch'], 'acceleratorKinds':['cpu']},
        'evaluation': {'status':'evaluated','evaluationRefs':['sc://eval/1'],'metrics':{'rmse':0.12}},
        'provenance': {'source':'research-lab'}, 'tags':['climate','surrogate'], 'createdBy':'tester'
    }


def dataset_req(project='registry-project', version='2026.1'):
    return {
        'projectKey': project, 'datasetKey':'climate-training', 'versionLabel':version,
        'title':'Climate training dataset', 'datasetHash':'b'*64, 'datasetRef':'sc://dataset/climate-training',
        'format':'parquet', 'schemaRef':'sc://schema/climate-v1', 'rowCount':1000, 'columnCount':12,
        'license':'CC-BY-4.0', 'compatibility':{'runtimeKinds':['ai-engineering'], 'dataFormats':['parquet']},
        'evaluation':{'status':'reviewed','evaluationRefs':['sc://review/dataset-1']},
        'provenance':{'source':'knowledge-library'}, 'tags':['climate','training'], 'createdBy':'tester'
    }


def experiment_req(project='registry-project'):
    return {
        'projectKey':project,'experimentKey':'registry-exp','title':'Registry bound experiment','mode':'hybrid',
        'model':{'modelKey':'primary-model','provider':'local','modelId':'sc/climate-surrogate','modelVersion':'1.0','task':'surrogate-modeling','artifactHash':'a'*64},
        'datasets':[{'role':'train','datasetRef':'sc://dataset/climate-training','datasetHash':'b'*64}],
        'training':{'enabled':True,'seed':7},'inference':{'enabled':True,'seed':7},'evaluationHooks':[], 'createdBy':'tester'
    }


def test_manifest_status_and_boundaries():
    m=c.get('/ai-registry/manifest').json(); assert m['ok'] and m['version']=='10.4.0'
    for key in ('modelDatasetRegistry','immutableVersionedModelRecords','immutableVersionedDatasetRecords','contentAddressedRegistryRecords','registrySearchAndListing','immutableAIExperimentRegistryBindings','versionCollisionProtection','platformCoreRegistryPlanning'):
        assert m['capabilities'][key] is True
    for key in ('automaticModelDownload','automaticDatasetDownload','automaticTrainingExecution','automaticInferenceExecution','automaticRegistryReplacement','automaticLatestVersionSelection','automaticPreferredModelSelection','automaticPreferredDatasetSelection','scientificValidityInferred','automaticExperimentMutation','automaticCoreDispatch','automaticCorePersistence','governedCoreObjectCreated'):
        assert m['boundaries'][key] is False
    s=c.get('/v1010/status').json(); assert s['modelDatasetRegistry'] and s['immutableVersionedRecords'] and s['automaticExperimentMutation'] is False


def test_model_and_dataset_records_are_content_addressed_idempotent(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    mr=model_req(); dr=dataset_req()
    m1=c.post('/ai-registry/models',json=mr); assert m1.status_code==200,m1.text
    m2=c.post('/ai-registry/models',json=mr); assert m2.status_code==200,m2.text
    assert m1.json()['idempotent'] is False and m2.json()['idempotent'] is True and m1.json()['recordHash']==m2.json()['recordHash']
    d1=c.post('/ai-registry/datasets',json=dr); assert d1.status_code==200,d1.text
    d2=c.post('/ai-registry/datasets',json=dr).json(); assert d2['idempotent'] is True and d2['recordHash']==d1.json()['recordHash']
    assert len(m1.json()['recordHash'])==64 and len(d1.json()['recordHash'])==64
    assert m1.json()['immutability']['replacementAllowed'] is False


def test_same_key_version_different_content_is_collision(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    req=model_req('collision-project'); assert c.post('/ai-registry/models',json=req).status_code==200
    changed=dict(req); changed['title']='Changed immutable title'
    r=c.post('/ai-registry/models',json=changed); assert r.status_code==409


def test_list_load_and_search(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    p='search-project'; m=c.post('/ai-registry/models',json=model_req(p)).json(); d=c.post('/ai-registry/datasets',json=dataset_req(p)).json()
    ml=c.get(f'/ai-registry/models/{p}').json(); dl=c.get(f'/ai-registry/datasets/{p}').json()
    assert ml['recordCount']==1 and dl['recordCount']==1
    assert c.get(f"/ai-registry/models/{p}/{m['recordHash']}").json()['modelKey']=='climate-surrogate'
    assert c.get(f"/ai-registry/datasets/{p}/{d['recordHash']}").json()['datasetKey']=='climate-training'
    s=c.post('/ai-registry/search',json={'projectKey':p,'query':'climate','tags':['climate']}).json(); assert s['resultCount']==2 and len(s['searchHash'])==64
    only=c.post('/ai-registry/search',json={'projectKey':p,'kinds':['model'],'provider':'local','evaluationStatus':'evaluated'}).json(); assert only['resultCount']==1 and only['results'][0]['kind']=='model'


def test_experiment_binding_is_verified_and_does_not_mutate_experiment(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    p='binding-project'; m=c.post('/ai-registry/models',json=model_req(p)).json(); d=c.post('/ai-registry/datasets',json=dataset_req(p)).json(); e=c.post('/ai-engineering/experiments',json=experiment_req(p)).json()
    req={'projectKey':p,'experimentHash':e['experimentHash'],'modelRecordHash':m['recordHash'],'datasets':[{'role':'train','datasetRecordHash':d['recordHash']}],'createdBy':'tester'}
    plan=c.post('/ai-registry/experiment-binding-plan',json=req); assert plan.status_code==200,plan.text
    x=plan.json(); assert x['bindingReady'] is True and x['issues']==[] and x['boundaries']['experimentMutated'] is False
    saved=c.post('/ai-registry/experiment-bindings',json=req); assert saved.status_code==200,saved.text
    y=saved.json(); assert y['idempotent'] is False and len(y['recordHash'])==64
    again=c.post('/ai-registry/experiment-bindings',json=req).json(); assert again['idempotent'] is True
    original=c.get(f"/ai-engineering/experiments/{p}/{e['experimentHash']}").json(); assert original['experimentHash']==e['experimentHash']


def test_binding_mismatch_is_reported_not_silently_fixed(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    p='bad-binding-project'; mreq=model_req(p); mreq['modelId']='different/model'; m=c.post('/ai-registry/models',json=mreq).json(); d=c.post('/ai-registry/datasets',json=dataset_req(p)).json(); e=c.post('/ai-engineering/experiments',json=experiment_req(p)).json()
    req={'projectKey':p,'experimentHash':e['experimentHash'],'modelRecordHash':m['recordHash'],'datasets':[{'role':'train','datasetRecordHash':d['recordHash']}]}
    plan=c.post('/ai-registry/experiment-binding-plan',json=req).json(); assert plan['bindingReady'] is False and any(i['code']=='model-id-mismatch' for i in plan['issues'])
    saved=c.post('/ai-registry/experiment-bindings',json=req); assert saved.status_code==409


def test_core_plan_is_plan_only(monkeypatch,tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE',str(tmp_path/'store'))
    p='core-registry-project'; m=c.post('/ai-registry/models',json=model_req(p)).json()
    r=c.post('/integration/core/ai-registry/plan',json={'projectKey':p,'kind':'model','recordHash':m['recordHash'],'createdBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['bindingPlan']['objectType']=='workbench.ai-model-registry-record'
    assert d['boundaries']['automaticCoreDispatch'] is False and d['boundaries']['governedCoreObjectCreated'] is False and d['boundaries']['scientificValidityInferred'] is False


def test_capability_registry_and_retained_v1000_surface():
    caps=c.get('/capabilities').json(); assert caps['version']=='10.4.0'
    for key in ('modelDatasetRegistry','aiRegistryImmutableModelVersions','aiRegistryImmutableDatasetVersions','aiRegistryContentAddressedRecords','aiRegistryLicenseProvenance','aiRegistryCompatibilityMetadata','aiRegistryNeutralEvaluationState','aiRegistrySearch','aiRegistryExperimentBindings','aiRegistryCorePlanning'):
        assert caps['coreIntegration'][key] is True
    old=c.get('/ai-engineering/manifest').json(); assert old['version']=='10.4.0' and old['capabilities']['scientificAIEngineeringRuntimeFoundation']
    assert c.get('/v1000/status').status_code==200

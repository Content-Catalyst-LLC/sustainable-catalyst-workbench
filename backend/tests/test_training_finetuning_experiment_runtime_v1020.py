from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def model_req(project='train-project'):
    return {
        'projectKey': project, 'modelKey': 'base-model', 'versionLabel': '1.0', 'title': 'Base model',
        'provider': 'local', 'modelId': 'sc/base-model', 'task': 'classification', 'artifactHash': 'a'*64,
        'license': 'Apache-2.0', 'compatibility': {'runtimeKinds':['ai-engineering','workspace-ml']},
        'createdBy': 'tester'
    }


def dataset_req(project='train-project', key='train-data', role='train', h='b'):
    return {
        'projectKey': project, 'datasetKey': key, 'versionLabel': '1.0', 'title': key,
        'datasetHash': h*64, 'datasetRef': f'sc://dataset/{key}', 'format': 'parquet',
        'license': 'CC-BY-4.0', 'compatibility': {'runtimeKinds':['ai-engineering'],'dataFormats':['parquet']},
        'createdBy': 'tester'
    }


def experiment_req(project='train-project'):
    return {
        'projectKey': project, 'experimentKey': 'finetune-exp', 'title': 'Fine-tuning experiment', 'mode': 'training',
        'model': {'modelKey':'base-model','provider':'local','modelId':'sc/base-model','modelVersion':'1.0','task':'classification','artifactHash':'a'*64},
        'datasets': [
            {'role':'train','datasetRef':'sc://dataset/train-data','datasetHash':'b'*64},
            {'role':'validation','datasetRef':'sc://dataset/val-data','datasetHash':'c'*64},
        ],
        'training': {'enabled':True,'seed':42,'epochs':2,'batchSize':4,'learningRate':0.0001},
        'inference': {'enabled':False}, 'evaluationHooks': [], 'createdBy': 'tester'
    }


def setup_sources(monkeypatch, tmp_path, project='train-project'):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    m = c.post('/ai-registry/models', json=model_req(project)); assert m.status_code == 200, m.text
    tr = c.post('/ai-registry/datasets', json=dataset_req(project,'train-data','train','b')); assert tr.status_code == 200, tr.text
    va = c.post('/ai-registry/datasets', json=dataset_req(project,'val-data','validation','c')); assert va.status_code == 200, va.text
    e = c.post('/ai-engineering/experiments', json=experiment_req(project)); assert e.status_code == 200, e.text
    binding_req = {
        'projectKey': project, 'experimentHash': e.json()['experimentHash'], 'modelRecordHash': m.json()['recordHash'],
        'datasets': [
            {'role':'train','datasetRecordHash':tr.json()['recordHash']},
            {'role':'validation','datasetRecordHash':va.json()['recordHash']},
        ], 'createdBy':'tester'
    }
    b = c.post('/ai-registry/experiment-bindings', json=binding_req); assert b.status_code == 200, b.text
    return m.json(), tr.json(), va.json(), e.json(), b.json()


def run_req(project, m, e, b, method='lora'):
    return {
        'projectKey': project, 'trainingKey':'run-001', 'title':'Registry-backed fine-tuning run',
        'experimentHash': e['experimentHash'], 'registryBindingHash': b['recordHash'], 'baseModelRecordHash': m['recordHash'],
        'fineTuning': {'method':method,'trainableParameterPolicy':'adapters-only','targetModules':['q_proj','v_proj'],'loraRank':8,'loraAlpha':16.0,'quantizationBits':4 if method=='qlora' else None},
        'hyperparameters': {'seed':42,'epochs':2,'batchSize':4,'learningRate':0.0001,'optimizer':'adamw','scheduler':'cosine','deterministicRequested':True},
        'evaluation': {'enabled':True,'everySteps':10,'datasetRole':'validation','metrics':['loss','accuracy'],'trackingMetric':'loss','direction':'minimize','automaticEarlyStopping':False},
        'checkpoints': {'enabled':True,'everySteps':20,'maxRetained':3,'saveOptimizerState':True,'finalCheckpointRequired':True},
        'environment': {'adapter':'workspace-ml','environmentRef':'sc://env/ml-1','dependencyLockHash':'d'*64,'accelerator':'cpu','precision':'fp32','networkAccessAllowed':False},
        'budget': {'maxWallMinutes':120,'maxCpuHours':8,'maxGpuHours':0,'maxCostUsd':0,'maxCheckpoints':5},
        'outputModelKey':'fine-tuned-model','outputVersionLabel':'1.0','tags':['training','lora'],'createdBy':'tester'
    }


def test_manifest_status_capabilities_and_boundaries():
    m = c.get('/ai-training/manifest').json(); assert m['ok'] and m['version']=='10.2.0'
    for k in ('trainingFineTuningExperimentRuntime','registryBackedTrainingRuns','fullAndParameterEfficientFineTuning','loraAndQloraConfiguration','deterministicTrainingManifests','trainingResourceBudgets','checkpointLineage','appendOnlyTrainingProgressEvents','immutableTrainingResults','derivedModelRegistrationPlanning','platformCoreTrainingPlanning'):
        assert m['capabilities'][k] is True
    for k in ('automaticModelDownload','automaticDatasetDownload','automaticTrainingExecution','arbitraryCodeExecution','automaticExternalProviderCall','automaticCheckpointPromotion','automaticRegistryPromotion','automaticPreferredModelSelection','scientificValidityInferred','automaticCoreDispatch','automaticCorePersistence','governedCoreObjectCreated'):
        assert m['boundaries'][k] is False
    s=c.get('/v1020/status').json(); assert s['trainingFineTuningExperimentRuntime'] and s['automaticTrainingExecution'] is False


def test_training_run_is_registry_backed_content_addressed_and_idempotent(monkeypatch,tmp_path):
    p='run-project'; m,tr,va,e,b=setup_sources(monkeypatch,tmp_path,p); req=run_req(p,m,e,b)
    plan=c.post('/ai-training/compose',json=req); assert plan.status_code==200,plan.text
    x=plan.json(); assert x['trainingReady'] and x['issues']==[] and len(x['runHash'])==64
    assert x['run']['baseModelRecordHash']==m['recordHash'] and len(x['run']['datasets'])==2
    a=c.post('/ai-training/runs',json=req); assert a.status_code==200,a.text
    b2=c.post('/ai-training/runs',json=req); assert b2.status_code==200,b2.text
    assert a.json()['idempotent'] is False and b2.json()['idempotent'] is True and a.json()['runHash']==b2.json()['runHash']
    listing=c.get(f'/ai-training/runs/{p}').json(); assert listing['runCount']==1


def test_training_source_mismatch_is_reported_not_repaired(monkeypatch,tmp_path):
    p='mismatch-project'; m,tr,va,e,b=setup_sources(monkeypatch,tmp_path,p)
    other=c.post('/ai-registry/models',json={**model_req(p),'modelKey':'other','versionLabel':'1.0','title':'Other','modelId':'sc/other','artifactHash':'e'*64}).json()
    req=run_req(p,other,e,b)
    plan=c.post('/ai-training/compose',json=req).json(); assert plan['trainingReady'] is False
    assert any(i['code']=='registry-binding-model-mismatch' for i in plan['issues'])
    saved=c.post('/ai-training/runs',json=req); assert saved.status_code==409


def test_parameter_efficient_configuration_validation():
    base={'method':'qlora','trainableParameterPolicy':'adapters-only','quantizationBits':16}
    r=c.post('/ai-training/compose',json={'projectKey':'x','trainingKey':'x','title':'x','experimentHash':'a'*64,'registryBindingHash':'b'*64,'baseModelRecordHash':'c'*64,'fineTuning':base,'evaluation':{'enabled':False},'outputModelKey':'x','outputVersionLabel':'1'})
    assert r.status_code==422
    full={'method':'full-finetune','trainableParameterPolicy':'all','freezeBaseModel':True}
    r2=c.post('/ai-training/compose',json={'projectKey':'x','trainingKey':'x','title':'x','experimentHash':'a'*64,'registryBindingHash':'b'*64,'baseModelRecordHash':'c'*64,'fineTuning':full,'evaluation':{'enabled':False},'outputModelKey':'x','outputVersionLabel':'1'})
    assert r2.status_code==422


def test_execution_plan_is_explicit_and_not_authorized(monkeypatch,tmp_path):
    p='execution-project'; m,tr,va,e,b=setup_sources(monkeypatch,tmp_path,p); saved=c.post('/ai-training/runs',json=run_req(p,m,e,b)).json()
    r=c.post('/ai-training/execution-plan',json={'projectKey':p,'runHash':saved['runHash'],'requestedBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['authorized'] is False and d['adapterContract']['adapter']=='workspace-ml'
    assert d['boundaries']['executionRequiresExplicitAuthorization'] is True and d['boundaries']['automaticRegistryPromotion'] is False


def test_progress_events_are_append_only_sequence_protected(monkeypatch,tmp_path):
    p='events-project'; m,tr,va,e,b=setup_sources(monkeypatch,tmp_path,p); saved=c.post('/ai-training/runs',json=run_req(p,m,e,b)).json(); h=saved['runHash']
    event={'projectKey':p,'runHash':h,'sequence':1,'eventType':'progress','step':10,'epoch':0.5,'metrics':{'loss':0.8},'recordedBy':'tester'}
    a=c.post('/ai-training/events',json=event); assert a.status_code==200,a.text
    same=c.post('/ai-training/events',json=event).json(); assert same['idempotent'] is True
    changed={**event,'metrics':{'loss':0.7}}; clash=c.post('/ai-training/events',json=changed); assert clash.status_code==409
    cp=c.post('/ai-training/events',json={'projectKey':p,'runHash':h,'sequence':2,'eventType':'checkpoint','step':20,'checkpointArtifactHash':'f'*64}); assert cp.status_code==200,cp.text
    rows=c.get(f'/ai-training/events/{p}/{h}').json(); assert rows['eventCount']==2


def test_training_result_is_immutable_and_derived_model_plan_is_plan_only(monkeypatch,tmp_path):
    p='result-project'; m,tr,va,e,b=setup_sources(monkeypatch,tmp_path,p); saved=c.post('/ai-training/runs',json=run_req(p,m,e,b)).json(); h=saved['runHash']
    req={'projectKey':p,'runHash':h,'status':'completed','finalModelArtifactHash':'1'*64,'finalCheckpointArtifactHash':'2'*64,'metrics':{'loss':0.2,'accuracy':0.91},'sourceJobId':'job-1','sourceResultHash':'3'*64,'completedBy':'tester'}
    a=c.post('/ai-training/results',json=req); assert a.status_code==200,a.text
    same=c.post('/ai-training/results',json=req).json(); assert same['idempotent'] is True
    changed={**req,'metrics':{'loss':0.19}}; clash=c.post('/ai-training/results',json=changed); assert clash.status_code==409
    result=a.json(); plan=c.post('/ai-training/derived-model-plan',json={'projectKey':p,'runHash':h,'resultHash':result['resultHash'],'title':'Fine-tuned model','license':'Apache-2.0','createdBy':'tester'}); assert plan.status_code==200,plan.text
    d=plan.json(); assert d['authorized'] is False and d['modelRegistryRequest']['artifactHash']=='1'*64
    assert d['modelRegistryRequest']['provenance']['derivedFromModelRecordHash']==m['recordHash']
    assert d['boundaries']['automaticRegistryPromotion'] is False


def test_core_plan_is_plan_only(monkeypatch,tmp_path):
    p='core-training-project'; m,tr,va,e,b=setup_sources(monkeypatch,tmp_path,p); saved=c.post('/ai-training/runs',json=run_req(p,m,e,b)).json()
    r=c.post('/integration/core/ai-training/plan',json={'projectKey':p,'kind':'training-run','sourceHash':saved['runHash'],'createdBy':'tester'}); assert r.status_code==200,r.text
    d=r.json(); assert d['bindingPlan']['objectType']=='workbench.ai-training-run'
    assert d['boundaries']['automaticCoreDispatch'] is False and d['boundaries']['governedCoreObjectCreated'] is False and d['boundaries']['scientificValidityInferred'] is False


def test_capability_registry_and_retained_v10_surfaces():
    caps=c.get('/capabilities').json(); assert caps['version']=='10.2.0'
    for k in ('trainingFineTuningExperimentRuntime','aiTrainingRegistryBackedRuns','aiTrainingFineTuningMethods','aiTrainingDeterministicManifests','aiTrainingResourceBudgets','aiTrainingCheckpointLineage','aiTrainingAppendOnlyProgress','aiTrainingImmutableResults','aiTrainingDerivedModelPlanning','aiTrainingCorePlanning'):
        assert caps['coreIntegration'][k] is True
    assert c.get('/ai-engineering/manifest').json()['version']=='10.2.0'
    assert c.get('/ai-registry/manifest').json()['version']=='10.2.0'
    assert c.get('/v1000/status').status_code==200 and c.get('/v1010/status').status_code==200

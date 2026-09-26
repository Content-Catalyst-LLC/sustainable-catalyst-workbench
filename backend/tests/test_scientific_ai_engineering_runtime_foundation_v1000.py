from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def base_request(project='ai-project'):
    return {
        'projectKey': project,
        'experimentKey': 'exp-001',
        'title': 'AI engineering experiment',
        'mode': 'hybrid',
        'model': {
            'modelKey': 'primary-model', 'provider': 'local', 'modelId': 'example/model',
            'modelVersion': '1', 'task': 'regression', 'artifactHash': 'a'*64,
        },
        'datasets': [
            {'role': 'train', 'datasetRef': 'sc://dataset/train', 'datasetHash': 'b'*64},
            {'role': 'test', 'datasetRef': 'sc://dataset/test', 'datasetHash': 'c'*64},
        ],
        'environment': {
            'pythonVersion': '3.12', 'framework': 'pytorch', 'frameworkVersion': '2.x',
            'containerImage': 'local/research-ai:1', 'dependencyLockHash': 'd'*64,
            'accelerator': 'cpu', 'precision': 'float32', 'networkAccessAllowed': False,
        },
        'training': {
            'enabled': True, 'seed': 42, 'epochs': 3, 'batchSize': 8,
            'learningRate': 0.001, 'optimizer': 'adam', 'deterministicRequested': True,
        },
        'inference': {
            'enabled': True, 'seed': 42, 'temperature': 0.0, 'topP': 1.0,
            'maxOutputTokens': 512, 'deterministicRequested': True,
            'toolUseAllowed': False, 'externalNetworkAllowed': False,
        },
        'evaluationHooks': [
            {'name': 'mae', 'metric': 'mean-absolute-error', 'datasetRole': 'test', 'direction': 'minimize'}
        ],
        'budget': {'maxWallMinutes': 30, 'maxCpuHours': 2, 'maxGpuHours': 0, 'maxCostUsd': 0, 'maxRuns': 1},
        'createdBy': 'tester',
    }


def test_manifest_status_and_boundaries():
    m = c.get('/ai-engineering/manifest').json()
    assert m['ok'] and m['version'] == '10.0.0'
    assert m['capabilities']['scientificAIEngineeringRuntimeFoundation']
    assert m['capabilities']['contentAddressedAIExperimentSpecifications']
    for key in ('automaticModelDownload','automaticTrainingExecution','automaticInferenceExecution','externalProviderCallsAuthorized','arbitraryCodeExecutionAuthorized','hiddenAgentExecutionAuthorized','automaticModelSelection','automaticScientificInterpretation','scientificValidityInferred','automaticCoreDispatch','automaticCorePersistence','governedCoreObjectCreated'):
        assert m['boundaries'][key] is False
    s = c.get('/v1000/status').json()
    assert s['scientificAIEngineeringRuntimeFoundation'] and s['automaticTrainingExecution'] is False


def test_runtime_contracts_are_plan_only():
    d = c.get('/ai-engineering/runtime-contracts').json()
    assert d['version'] == '10.0.0' and len(d['contracts']) == 2 and len(d['contractHash']) == 64
    assert all(x['executionImplemented'] is False for x in d['contracts'])


def test_compose_is_content_addressed_and_deterministic():
    req = base_request()
    a = c.post('/ai-engineering/compose', json=req); assert a.status_code == 200, a.text
    b = c.post('/ai-engineering/compose', json=req); assert b.status_code == 200, b.text
    x, y = a.json(), b.json()
    assert x['experimentHash'] == y['experimentHash'] and len(x['experimentHash']) == 64
    assert x['reproducibility']['explicitTrainingSeed'] == 42
    assert x['reproducibility']['environmentFullyPinned'] is True
    assert x['lineage']['datasetHashes'] == ['b'*64, 'c'*64]


def test_training_mode_requires_train_dataset():
    req = base_request(); req['datasets'] = [req['datasets'][1]]
    r = c.post('/ai-engineering/compose', json=req)
    assert r.status_code == 422


def test_save_load_list_are_integrity_checked(monkeypatch, tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    req = base_request('persisted-ai-project')
    a = c.post('/ai-engineering/experiments', json=req); assert a.status_code == 200, a.text
    x = a.json(); assert x['idempotent'] is False and len(x['recordHash']) == 64
    b = c.post('/ai-engineering/experiments', json=req).json(); assert b['idempotent'] is True and b['experimentHash'] == x['experimentHash']
    got = c.get(f"/ai-engineering/experiments/{req['projectKey']}/{x['experimentHash']}"); assert got.status_code == 200
    ls = c.get(f"/ai-engineering/experiments/{req['projectKey']}").json(); assert ls['experimentCount'] == 1 and ls['experiments'][0]['modelId'] == 'example/model'


def test_execution_plan_never_executes(monkeypatch, tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    req = base_request('plan-project')
    saved = c.post('/ai-engineering/experiments', json=req).json()
    r = c.post('/ai-engineering/execution-plan', json={'projectKey': req['projectKey'], 'experimentHash': saved['experimentHash'], 'requestedBy': 'tester'}); assert r.status_code == 200, r.text
    d = r.json(); assert d['runtimeKind'] == 'ai-engineering' and d['executionAuthorized'] is False
    assert {x['operation'] for x in d['operations']} == {'train-model','run-inference','evaluate-model'}
    assert all(x['authorized'] is False for x in d['operations'])
    assert d['boundaries']['providerCallPerformed'] is False and d['boundaries']['trainingPerformed'] is False


def test_core_plan_is_plan_only(monkeypatch, tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    req = base_request('core-ai-project')
    saved = c.post('/ai-engineering/experiments', json=req).json()
    r = c.post('/integration/core/ai-engineering/plan', json={'projectKey': req['projectKey'], 'experimentHash': saved['experimentHash'], 'requestedBy': 'tester'}); assert r.status_code == 200, r.text
    d = r.json(); assert d['bindingPlan']['objectType'] == 'workbench.ai-engineering-experiment'
    assert d['boundaries']['automaticCoreDispatch'] is False and d['boundaries']['governedCoreObjectCreated'] is False
    assert d['boundaries']['scientificValidityInferred'] is False


def test_capability_registry_exposes_v1000_flags():
    caps = c.get('/capabilities').json(); assert caps['version'] == '10.0.0'
    for key in ('scientificAIEngineeringRuntimeFoundation','aiEngineeringContentAddressedExperiments','aiEngineeringModelProviderContracts','aiEngineeringDatasetLineage','aiEngineeringDeterministicConfiguration','aiEngineeringResourceBudgets','aiEngineeringNeutralExecutionPlanning','aiEngineeringCorePlanning'):
        assert caps['coreIntegration'][key] is True


def test_execution_console_retains_ai_engineering_runtime_kind():
    m = c.get('/execution-console/manifest').json()
    assert 'ai-engineering' in m['runtimeKinds']


def test_health_and_v9_production_surface_retained(monkeypatch, tmp_path):
    monkeypatch.setenv('SCWB_RESEARCH_ENVIRONMENT_STORE', str(tmp_path/'store'))
    h = c.get('/health').json(); assert h['version'] == '10.0.0' and h['readiness'] == 'ready'
    old = c.get('/v9-production-certification/manifest').json(); assert old['version'] == '10.0.0' and old['capabilities']['retainedV9MilestoneAudit']
    for path in ('/v9120/status','/v1000/status'):
        r = c.get(path); assert r.status_code == 200, (path, r.text)

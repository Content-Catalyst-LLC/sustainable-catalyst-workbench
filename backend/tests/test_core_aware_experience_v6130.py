from fastapi.testclient import TestClient
from app.main import app
from app.v640 import CORE_RUNTIME_CONTRACT
from app.v660 import CORE_UNIFIED_RUNTIME_CONTRACT

c = TestClient(app)


def test_status_and_manifest():
    s = c.get('/v6130/status')
    assert s.status_code == 200
    d = s.json()
    assert d['version'] == '7.10.0'
    assert d['coreAwareContext'] is True
    assert d['automaticCoreDispatch'] is False
    m = c.get('/integration/core/experience/manifest')
    assert m.status_code == 200, m.text
    body = m.json()
    assert body['version'] == '7.10.0'
    assert len(body['bridges']) == 9
    assert body['contracts']['runtime'] == CORE_RUNTIME_CONTRACT
    assert body['boundaries']['coreIdsMustComeFromCore'] is True


def test_context_assembly_detects_present_missing_ids_and_actions():
    r = c.post('/integration/core/experience/context/assemble', json={
        'projectRef': 'sc://workbench/project/p1',
        'projectTitle': 'Project One',
        'coreProjectRef': 'core-project:1',
        'coreSessionId': 'session:1',
        'objectRefs': ['obj:2', 'obj:1', 'obj:1'],
        'executionRefs': ['exec:1'],
    })
    assert r.status_code == 200, r.text
    d = r.json()
    assert 'coreProjectRef' in d['presentCoreIds']
    assert 'coreExecutionId' in d['missingCoreIds']
    assert d['objectRefs'] == ['obj:1', 'obj:2']
    assert 'register-execution-lineage' in d['nextActions']
    assert d['automaticDispatchAuthorized'] is False
    assert len(d['contextHash']) == 64


def test_compatibility_ready_and_attention_states():
    ok = c.post('/integration/core/experience/compatibility/evaluate', json={
        'coreReachable': True,
        'coreVersion': '3.2.1',
        'expectedCoreVersionPrefix': '3.',
        'runtimeContract': CORE_RUNTIME_CONTRACT,
        'unifiedRuntimeContract': CORE_UNIFIED_RUNTIME_CONTRACT,
    }).json()
    assert ok['compatible'] is True and ok['readiness'] == 'ready'
    bad = c.post('/integration/core/experience/compatibility/evaluate', json={
        'coreReachable': False,
        'coreVersion': '2.9.0',
        'expectedCoreVersionPrefix': '3.',
        'runtimeContract': 'wrong',
        'unifiedRuntimeContract': CORE_UNIFIED_RUNTIME_CONTRACT,
        'serviceTokenRequired': True,
        'serviceTokenConfigured': False,
    }).json()
    assert bad['compatible'] is False
    assert 'core-unreachable' in bad['reasons']
    assert 'runtime-contract-mismatch' in bad['reasons']
    assert 'service-token-required-but-not-configured' in bad['reasons']
    assert bad['automaticRepairAuthorized'] is False


def test_action_planning_enforces_core_id_requirements_without_dispatch():
    blocked = c.post('/integration/core/experience/actions/plan', json={
        'action': 'bind-execution-to-session',
        'context': {'projectRef': 'sc://workbench/project/p1'}
    }).json()
    assert blocked['ready'] is False
    assert blocked['missingRequirements'] == ['coreSessionId', 'coreExecutionId']
    assert blocked['automaticDispatchAuthorized'] is False
    ready = c.post('/integration/core/experience/actions/plan', json={
        'action': 'bind-execution-to-session',
        'context': {
            'projectRef': 'sc://workbench/project/p1',
            'coreSessionId': 'session:1',
            'coreExecutionId': 'execution:1'
        }
    }).json()
    assert ready['ready'] is True
    assert ready['request']['path'] == '/integration/core/computation-lineage/executions/session-binding/build'
    assert ready['callerMustReviewAndInvoke'] is True


def test_capability_registry_declares_v6130_experience():
    caps = c.get('/capabilities').json()
    assert caps['version'] == '7.10.0'
    assert caps['coreIntegration']['coreAwareWorkbenchExperience'] is True
    assert 'platform-core-aware-workbench-experience' in caps['capabilities']


def test_service_token_guard(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN', 'true')
    monkeypatch.setenv('SCWB_SERVICE_TOKEN', 'secret6130')
    assert c.get('/integration/core/experience/manifest').status_code == 401
    ok = c.get('/integration/core/experience/manifest', headers={'X-SC-Service-Token': 'secret6130'})
    assert ok.status_code == 200 and ok.json()['version'] == '7.10.0'

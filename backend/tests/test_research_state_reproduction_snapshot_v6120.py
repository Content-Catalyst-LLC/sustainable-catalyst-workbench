from fastapi.testclient import TestClient
from app.main import app
from app.v6120 import SNAPSHOT_SCHEMA, CORE_PROJECT_STATE_CONTRACT, CORE_REPRODUCIBLE_RESEARCH_CONTRACT, CORE_CONTEXT_HANDOFF_CONTRACT

c = TestClient(app)


def sample_snapshot_payload():
    return {
        "snapshotKey": "snap-demo",
        "projectRef": "sc://workbench/project/demo",
        "title": "Demo project",
        "projectHash": "sha256:project",
        "workbenchProjectVersion": "project-v3",
        "coreSessionId": "session-core-1",
        "bindings": [
            {"bindingKey": "dataset-1", "objectType": "dataset", "objectRef": "sc://workbench/dataset/1", "contentHash": "sha256:data"},
            {"bindingKey": "execution-1", "objectType": "execution", "objectRef": "sc://workbench/execution/1", "contentHash": "sha256:exec"},
            {"bindingKey": "output-1", "objectType": "output", "objectRef": "sc://workbench/output/1", "contentHash": "sha256:out"},
        ],
        "dependencies": [
            {"dependencyKey": "dep-1", "fromBindingKey": "dataset-1", "toBindingKey": "execution-1", "relation": "input_to"},
            {"dependencyKey": "dep-2", "fromBindingKey": "execution-1", "toBindingKey": "output-1", "relation": "produced"},
        ],
        "environments": [
            {"environmentKey": "env-1", "environmentType": "workbench", "environmentRef": "sc://workbench/runtime/6.12.0", "versionRef": "6.12.0", "contentHash": "sha256:env"}
        ],
        "artifacts": [
            {"artifactKey": "artifact-1", "artifactType": "result_bundle", "artifactRef": "sc://workbench/artifact/1", "mediaType": "application/json", "contentHash": "sha256:artifact"}
        ],
        "researchState": {"activeNotebook": "nb-1", "selectedObject": "output-1"},
    }


def build_snapshot():
    r = c.post('/research-state/snapshot/build', json=sample_snapshot_payload())
    assert r.status_code == 200, r.text
    return r.json()


def test_manifest_and_status_contracts():
    m = c.get('/integration/core/research-state/manifest')
    assert m.status_code == 200
    d = m.json()
    assert d['version'] == '7.1.0'
    assert d['coreProjectStateContract'] == CORE_PROJECT_STATE_CONTRACT
    assert d['coreReproducibleResearchContract'] == CORE_REPRODUCIBLE_RESEARCH_CONTRACT
    assert d['coreContextHandoffContract'] == CORE_CONTEXT_HANDOFF_CONTRACT
    assert d['boundaries']['automaticStateRestoreAuthorized'] is False
    s = c.get('/v6120/status').json()
    assert s['ok'] and s['version'] == '7.1.0'
    assert s['deterministicWorkbenchStateCapture'] is True
    assert s['automaticExecutionReplay'] is False


def test_snapshot_is_deterministic_and_auto_adds_project_binding():
    a = build_snapshot(); b = build_snapshot()
    assert a['schema'] == SNAPSHOT_SCHEMA
    assert a['snapshotHash'] == b['snapshotHash']
    assert any(x['bindingKey'] == 'workbench-project' and x['objectType'] == 'project' for x in a['bindings'])
    assert a['captureSemantics']['automaticRestoreAuthorized'] is False


def test_snapshot_rejects_dependency_to_unknown_binding():
    p = sample_snapshot_payload()
    p['dependencies'][0]['fromBindingKey'] = 'missing'
    r = c.post('/research-state/snapshot/build', json=p)
    assert r.status_code == 422


def test_project_state_prepare_targets_core_state_registry():
    snap = build_snapshot()
    r = c.post('/integration/core/research-state/project-state/prepare', json={'snapshot': snap})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['coreStateIdMustComeFromCore'] is True
    assert d['coreRequest']['path'] == '/v1/research/project-state/states'
    assert d['coreRequest']['contract'] == CORE_PROJECT_STATE_CONTRACT
    assert d['coreRequest']['automaticDispatchAuthorized'] is False


def test_project_state_version_plan_orders_freeze_checkpoint_and_reconstruction():
    snap = build_snapshot()
    r = c.post('/integration/core/research-state/project-state/version/plan', json={'coreStateId': 'state-core-1', 'snapshot': snap, 'version': 3})
    assert r.status_code == 200, r.text
    d = r.json(); paths = [x['path'] for x in d['coreRequests']]
    assert paths[0] == '/v1/research/project-state/states/state-core-1/versions'
    assert '/v1/research/project-state/states/state-core-1/versions/3/freeze' in paths
    assert paths[-2].endswith('/checkpoints')
    assert paths[-1].endswith('/reconstruction-plans')
    assert d['freezeMustFollowBindings'] is True
    assert d['automaticExecutionReplayAuthorized'] is False


def test_project_state_plan_requires_core_issued_state_id():
    snap = build_snapshot()
    r = c.post('/integration/core/research-state/project-state/version/plan', json={'coreStateId': '', 'snapshot': snap})
    assert r.status_code == 422


def test_reproduction_prepare_requires_core_project_entity_and_returns_create_request():
    snap = build_snapshot()
    r = c.post('/integration/core/research-state/reproduction/prepare', json={'coreProjectEntityId': 'project-core-72', 'snapshot': snap})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['corePackageIdMustComeFromCore'] is True
    assert d['coreRequest']['path'] == '/v1/research/reproducible/projects/project-core-72/packages'
    assert d['coreRequest']['contract'] == CORE_REPRODUCIBLE_RESEARCH_CONTRACT


def test_reproduction_package_plan_emits_components_environment_replay_and_snapshot():
    snap = build_snapshot()
    r = c.post('/integration/core/research-state/reproduction/package/plan', json={'corePackageId': 'pkg-core-1', 'snapshot': snap})
    assert r.status_code == 200, r.text
    d = r.json(); paths = [x['path'] for x in d['coreRequests']]
    assert any(x.endswith('/components') for x in paths)
    assert any(x.endswith('/artifacts') for x in paths)
    assert any(x.endswith('/environments') for x in paths)
    assert any(x.endswith('/replay-plans') for x in paths)
    assert paths[-1].endswith('/snapshots')
    assert d['automaticReplayAuthorized'] is False
    assert d['reproducibilityCertified'] is False


def test_context_prepare_and_plan_use_snapshot_transfer_without_execution():
    snap = build_snapshot()
    prep = c.post('/integration/core/research-state/context/prepare', json={'snapshot': snap}).json()
    assert prep['coreContextIdMustComeFromCore'] is True
    assert prep['coreRequest']['path'] == '/v1/research/context-handoffs/contexts'
    r = c.post('/integration/core/research-state/context/plan', json={'coreContextId': 'ctx-core-1', 'snapshot': snap, 'toProduct': 'core'})
    assert r.status_code == 200, r.text
    d = r.json(); reqs = d['coreRequests']
    protocol = next(x for x in reqs if x['path'].endswith('/protocols'))
    assert protocol['data']['transfer_mode'] == 'snapshot'
    assert protocol['data']['from_product'] == 'workbench'
    assert d['automaticHandoffExecutionAuthorized'] is False


def test_resume_consumes_core_project_state_manifest_without_auto_restore():
    bundle = {
        'state': {'project_ref': 'core-project:1'},
        'version': {'version': 2, 'status': 'frozen'},
        'bindings': [{'object_ref': 'obj:1', 'content_hash': 'abc'}],
        'dependencies': [],
        'environments': [{'environment_ref': 'env:1'}],
    }
    r = c.post('/integration/core/research-state/resume/consume', json={'bundle': bundle})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['sourceKind'] == 'core-project-state-historical-manifest'
    assert d['requiredObjectRefs'] == ['obj:1']
    assert d['automaticRestoreAuthorized'] is False
    assert d['automaticExecutionReplayAuthorized'] is False


def test_resume_consumes_reproducible_package():
    bundle = {
        'contract': CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        'package': {'id': 'pkg-1'},
        'components': [{'component_ref': 'comp:1'}],
        'artifacts': [{'artifact_ref': 'artifact:1'}],
        'environments': [{'environment_ref': 'env:1'}],
        'replay_plans': [{'instructions': {'step': 'explicit'}}],
    }
    d = c.post('/integration/core/research-state/resume/consume', json={'bundle': bundle}).json()
    assert d['sourceKind'] == 'core-reproducible-research-package'
    assert d['requiredObjectRefs'] == ['artifact:1', 'comp:1']
    assert d['reproducibilityCertified'] is False


def test_resume_rejects_unknown_bundle_shape():
    assert c.post('/integration/core/research-state/resume/consume', json={'bundle': {'hello': 'world'}}).status_code == 422


def test_verification_compare_records_evidence_not_certification():
    snap = build_snapshot()
    manifest = {
        'bindings': [
            {'object_ref': 'sc://workbench/dataset/1', 'content_hash': 'sha256:data'},
            {'object_ref': 'sc://workbench/execution/1', 'content_hash': 'DIFFERENT'},
        ]
    }
    r = c.post('/research-state/verification/compare', json={'snapshot': snap, 'coreManifest': manifest})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d['statusCounts']['hash-match'] == 1
    assert d['statusCounts']['hash-mismatch'] == 1
    assert d['evidenceOnly'] is True and d['reproducibilityCertified'] is False


def test_capability_registry_declares_v6120_integration():
    caps = c.get('/capabilities').json()
    assert caps['version'] == '7.1.0'
    assert caps['coreIntegration']['researchStateReproductionSnapshotIntegration'] is True
    assert 'platform-core-research-state-reproduction-snapshot-integration' in caps['capabilities']


def test_service_token_guard(monkeypatch):
    monkeypatch.setenv('SCWB_REQUIRE_SERVICE_TOKEN', 'true')
    monkeypatch.setenv('SCWB_SERVICE_TOKEN', 'secret6120')
    assert c.get('/integration/core/research-state/manifest').status_code == 401
    ok = c.get('/integration/core/research-state/manifest', headers={'X-SC-Service-Token': 'secret6120'})
    assert ok.status_code == 200 and ok.json()['version'] == '7.1.0'

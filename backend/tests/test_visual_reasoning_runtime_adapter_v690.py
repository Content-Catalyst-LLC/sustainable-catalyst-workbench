from fastapi.testclient import TestClient
from app.main import app
from app.v690 import RESULT_SCHEMA, adapt_visual_result, VisualResultAdapterRequest

c = TestClient(app)


def sample_manifest(data_kind="series"):
    payload = {
        "projectEntityId": "project-core-1",
        "title": "Workbench result",
        "dataKind": data_kind,
        "visualKind": "generic",
        "reasoningPurpose": "explore",
        "coordinateSpace": "cartesian",
        "sourceRef": "workbench:run:1",
        "workbenchExecutionRef": "run:1",
        "coreExecutionId": "core-exec-1",
        "data": {"x": [0, 1, 2], "y": [2, 4, 8]},
    }
    if data_kind == "distribution": payload["data"] = {"values": [1, 2, 3, 4, 5]}
    if data_kind == "sensitivity": payload["data"] = {"indices": {"alpha": 0.7, "beta": {"total": 0.3}}}
    if data_kind == "matrix": payload["data"] = {"matrix": [[1, 2], [3, 4]]}
    if data_kind == "scenario": payload["data"] = {"outputs": {"cost": 12.5, "risk": [1, 2, 3]}}
    r = c.post("/integration/core/visual-reasoning/result/adapt", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def test_manifest_and_status():
    m = c.get("/integration/core/visual-reasoning/manifest")
    assert m.status_code == 200
    d = m.json()
    assert d["version"] == "9.6.0"
    assert d["coreSceneContract"] == "sc.visual-runtime.scene.v1"
    assert d["coreGrammarContract"] == "sc.visual-runtime.grammar.v1"
    assert d["coreUnifiedVisualContract"] == "sc.visual-runtime.unified-reasoning.v1"
    assert d["boundaries"]["automaticCoreDispatchAuthorized"] is False
    assert d["boundaries"]["rendererExecutionByCore"] is False
    s = c.get("/v690/status").json()
    assert s["ok"] is True and s["version"] == "9.6.0" and s["rendererNeutral"] is True


def test_capabilities_promote_visual_adapter():
    caps = c.get("/capabilities").json()
    assert caps["coreIntegration"]["visualReasoningRuntimeAdapter"] is True
    assert "platform-core-visual-reasoning-runtime-adapter" in caps["capabilities"]


def test_series_result_adapter_is_renderer_neutral_and_hashed():
    d = sample_manifest("series")
    assert d["schema"] == RESULT_SCHEMA
    assert len(d["elements"]) == 3
    assert d["summary"]["mean"] == 14 / 3
    assert d["grammarHints"]["markKind"] == "line"
    assert d["rendererNeutral"] is True
    assert d["calculated_by_workbench"] is True
    assert d["calculated_by_core"] is False
    assert len(d["manifestHash"]) == 64


def test_uncertainty_result_adapters():
    dist = sample_manifest("distribution")
    assert dist["summary"]["p50"] == 3
    assert all(x["semantic_role"] == "uncertainty" for x in dist["elements"])
    sens = sample_manifest("sensitivity")
    assert sens["summary"]["factorCount"] == 2
    assert sens["grammarHints"]["markKind"] == "bar"


def test_matrix_and_scenario_adapters():
    matrix = sample_manifest("matrix")
    assert matrix["summary"] == {"rows": 2, "columns": 2, "numericCells": 4}
    assert matrix["grammarHints"]["grammarKind"] == "matrix"
    scenario = sample_manifest("scenario")
    assert scenario["summary"]["outputCount"] == 2


def test_visual_object_registration_plan_targets_core_object_model():
    m = sample_manifest()
    r = c.post("/integration/core/visual-reasoning/object/plan", json={"manifest": m})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["coreVisualEntityIdMustComeFromCore"] is True
    assert d["coreRequests"][0]["path"] == "/v1/visual-reasoning/objects"
    assert d["coreRequests"][0]["data"]["project_entity_id"] == "project-core-1"
    assert d["automaticCorePersistenceAuthorized"] is False


def test_scene_registration_requires_core_issued_visual_id():
    m = sample_manifest()
    bad = c.post("/integration/core/visual-reasoning/scene/plan", json={"manifest": m, "coreVisualEntityId": ""})
    assert bad.status_code == 422
    r = c.post("/integration/core/visual-reasoning/scene/plan", json={"manifest": m, "coreVisualEntityId": "visual-core-1"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["coreSceneIdMustComeFromCore"] is True
    assert any(x["path"] == "/v1/visual-runtime/scenes" for x in d["coreRequests"])
    assert any("/v1/visual-reasoning/objects/visual-core-1/elements" == x["path"] for x in d["coreRequests"])


def test_grammar_registration_targets_scene_composition_and_grammar():
    m = sample_manifest("distribution")
    r = c.post("/integration/core/visual-reasoning/grammar/plan", json={"manifest": m, "coreSceneId": "scene-core-1"})
    assert r.status_code == 200, r.text
    d = r.json()
    paths = [x["path"] for x in d["coreRequests"]]
    assert "/v1/visual-runtime/scenes/scene-core-1/layers" in paths
    assert "/v1/visual-runtime/composition/scenes/scene-core-1/compositions" in paths
    assert "/v1/visual-runtime/grammar/specifications" in paths
    assert d["coreCompositionIdMustComeFromCore"] is True
    assert d["coreGrammarSpecificationIdMustComeFromCore"] is True


def test_unified_visual_workspace_plan_requires_core_composition():
    m = sample_manifest()
    r = c.post("/integration/core/visual-reasoning/unified-workspace/plan", json={"manifest": m, "coreCompositionId": "composition-core-1", "coreSceneIds": ["scene-core-1"]})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["coreWorkspaceIdMustComeFromCore"] is True
    assert d["coreRequests"][0]["path"] == "/v1/visual-runtime/unified/compositions/composition-core-1/workspaces"


def test_cross_product_plan_is_workbench_scoped_and_non_dispatching():
    m = sample_manifest()
    r = c.post("/integration/core/visual-reasoning/cross-product/plan", json={"manifest": m, "coreWorkspaceId": "workspace-core-1", "coreVisualEntityIds": ["visual-core-1"]})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["coreIntegrationIdMustComeFromCore"] is True
    assert d["coreRequests"][0]["data"]["product_key"] == "workbench"
    assert d["automaticCoreDispatchAuthorized"] is False


def test_service_token_guard_is_reused(monkeypatch):
    monkeypatch.setenv("SCWB_REQUIRE_SERVICE_TOKEN", "true")
    monkeypatch.setenv("SCWB_SERVICE_TOKEN", "secret")
    denied = c.get("/integration/core/visual-reasoning/manifest")
    assert denied.status_code == 401
    ok = c.get("/integration/core/visual-reasoning/manifest", headers={"X-SC-Service-Token": "secret"})
    assert ok.status_code == 200

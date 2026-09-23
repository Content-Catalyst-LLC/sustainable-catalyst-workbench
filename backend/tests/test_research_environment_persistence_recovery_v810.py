import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def _env(monkeypatch, tmp_path, key="persist-1", title="Persistent Environment"):
    monkeypatch.setenv("SCWB_RESEARCH_ENVIRONMENT_STORE", str(tmp_path / "store"))
    spec = {
        "environmentKey": key,
        "title": title,
        "projectEntityId": f"project:{key}",
        "activeSurface": "notebook",
        "components": [
            {"componentKey":"notebook","componentType":"notebook-run","payload":{"notebookRunHash":"nb-1","cellRuns":[]}},
            {"componentKey":"visual","componentType":"visual-workspace","componentRef":"sc://workbench/visual/1","contentHash":"a"*64},
        ],
    }
    r = c.post("/research-environment/build", json={"environment": spec})
    assert r.status_code == 200, r.text
    return r.json()


def test_manifest_and_status(monkeypatch, tmp_path):
    monkeypatch.setenv("SCWB_RESEARCH_ENVIRONMENT_STORE", str(tmp_path / "store"))
    m = c.get("/research-environment/persistence/manifest").json()
    assert m["ok"] and m["version"] == "8.3.0"
    assert m["storage"]["appendOnlyRevisionHistory"] is True
    assert m["boundaries"]["recoveryCreatesNewRevision"] is True
    s = c.get("/v810/status").json()
    assert s["ok"] and s["version"] == "8.3.0" and s["atomicFilePersistence"] is True


def test_save_load_revision_history(monkeypatch, tmp_path):
    env = _env(monkeypatch, tmp_path)
    a = c.post("/research-environment/persistence/save", json={"researchEnvironment": env, "expectedCurrentRevision": 0, "reason": "initial"})
    assert a.status_code == 200, a.text
    assert a.json()["revision"] == 1 and a.json()["persistence"]["atomicWrite"] is True
    loaded = c.get("/research-environment/persistence/persist-1").json()
    assert loaded["currentRevision"] == 1 and loaded["researchEnvironment"]["environmentHash"] == env["environmentHash"]
    revs = c.get("/research-environment/persistence/persist-1/revisions").json()
    assert revs["revisionCount"] == 1 and revs["revisions"][0]["reason"] == "initial"


def test_optimistic_revision_conflict(monkeypatch, tmp_path):
    env = _env(monkeypatch, tmp_path)
    assert c.post("/research-environment/persistence/save", json={"researchEnvironment": env, "expectedCurrentRevision": 0}).status_code == 200
    conflict = c.post("/research-environment/persistence/save", json={"researchEnvironment": env, "expectedCurrentRevision": 0})
    assert conflict.status_code == 409 and "revision conflict" in conflict.text


def test_checkpoint_and_recovery_create_new_revision(monkeypatch, tmp_path):
    env1 = _env(monkeypatch, tmp_path)
    r1 = c.post("/research-environment/persistence/save", json={"researchEnvironment": env1, "expectedCurrentRevision": 0}).json()
    cp = c.post("/research-environment/checkpoints/create", json={"environmentKey":"persist-1","label":"before-change"})
    assert cp.status_code == 200, cp.text
    checkpoint = cp.json(); assert checkpoint["revision"] == 1 and checkpoint["checkpointId"].startswith("cp-1-")

    env2 = _env(monkeypatch, tmp_path, title="Changed Environment")
    r2 = c.post("/research-environment/persistence/save", json={"researchEnvironment": env2, "expectedCurrentRevision": 1, "reason":"changed"})
    assert r2.status_code == 200 and r2.json()["revision"] == 2

    plan = c.post("/research-environment/recovery/plan", json={"environmentKey":"persist-1","target":{"checkpointId":checkpoint["checkpointId"]}})
    assert plan.status_code == 200, plan.text
    assert plan.json()["currentRevision"] == 2 and plan.json()["recoveryCreatesNewRevision"] is True and plan.json()["destructiveRollbackPerformed"] is False

    rec = c.post("/research-environment/recovery/apply", json={"environmentKey":"persist-1","target":{"checkpointId":checkpoint["checkpointId"]},"expectedCurrentRevision":2})
    assert rec.status_code == 200, rec.text
    body = rec.json(); assert body["newRevision"] == 3 and body["researchEnvironment"]["environmentHash"] == env1["environmentHash"]
    assert body["destructiveRollbackPerformed"] is False and body["scientificExecutionPerformed"] is False
    revs = c.get("/research-environment/persistence/persist-1/revisions").json()
    assert revs["revisionCount"] == 3 and revs["revisions"][-1]["recoveredFrom"]["kind"] == "checkpoint"


def test_revision_integrity_tamper_is_rejected(monkeypatch, tmp_path):
    env = _env(monkeypatch, tmp_path)
    c.post("/research-environment/persistence/save", json={"researchEnvironment": env, "expectedCurrentRevision": 0})
    files = list((tmp_path / "store" / "environments").glob("*/revisions/0000000001.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text()); data["reason"] = "tampered"; files[0].write_text(json.dumps(data))
    r = c.get("/research-environment/persistence/persist-1")
    assert r.status_code == 422 and "integrity validation" in r.text


def test_capabilities_advertise_v810():
    caps = c.get("/capabilities").json()
    assert caps["version"] == "8.3.0"
    ci = caps["coreIntegration"]
    assert ci["researchEnvironmentPersistenceRecovery"] is True
    assert ci["researchEnvironmentRevisionHistory"] is True
    assert ci["researchEnvironmentCheckpoints"] is True
    assert ci["researchEnvironmentRecovery"] is True

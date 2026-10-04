import os
from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
DB = "/tmp/scwb-v1290-test.sqlite3"

def setup_module():
    Path(DB).unlink(missing_ok=True)
    os.environ["SCWB_SESSION_SECRET"] = "v12.9-test-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"] = "v12.9-test-link-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"] = DB
    os.environ["SCWB_STANDALONE_APP_URL"] = "https://workbench.example.test"

def teardown_module():
    for k in [
        "SCWB_SESSION_SECRET",
        "SCWB_DEEP_LINK_SECRET",
        "SCWB_PROJECT_STORE_PATH",
        "SCWB_STANDALONE_APP_URL",
    ]:
        os.environ.pop(k, None)
    for p in [DB, DB + "-wal", DB + "-shm"]:
        Path(p).unlink(missing_ok=True)

def headers(label="v1290"):
    d = client.post(
        "/standalone/v1/auth/session/anonymous",
        json={"ttlSeconds": 600, "clientLabel": label},
    ).json()
    return {"Authorization": f"Bearer {d['token']}"}

def test_status_certifies_migration():
    d = client.get("/v1290/status").json()
    assert d["version"] == "12.9.0"
    assert d["certification"] == "pass"
    assert d["migrationReady"] is True
    assert d["wordpressRequired"] is False
    assert d["capabilities"]["standaloneMigrationCertified"] is True

def test_full_certification_is_green():
    d = client.get("/standalone/v1/migration/certification").json()
    assert d["certification"] == "pass"
    assert d["migrationReady"] is True
    assert all(d["checks"].values())
    assert d["migrationBoundary"]["wordpressRemovalDoesNotChangeV12CanonicalContracts"] is True
    assert d["nextRelease"]["version"] == "12.10.0"

def test_capability_matrix():
    m = client.get("/standalone/v1/migration/capability-matrix").json()["matrix"]
    assert m["count"] == 9
    assert m["allMigrationReady"] is True
    assert m["allWordPressIndependent"] is True
    assert any(x["capability"] == "reproducibility-packages" for x in m["capabilities"])

def test_runbook():
    r = client.get("/standalone/v1/migration/runbook").json()["runbook"]
    assert r["wordpressRequired"] is False
    blocking = [x["id"] for x in r["phases"] if x["blocking"]]
    assert "serve-fastapi" in blocking
    assert "preserve-v12-store" in blocking
    assert r["rollback"]["applicationStateRollbackDependsOnWordPress"] is False

def test_session_probe_uses_standalone_session():
    assert client.get("/standalone/v1/migration/session-probe").status_code in (401, 403)
    d = client.get("/standalone/v1/migration/session-probe", headers=headers()).json()
    assert d["wordpressRequired"] is False
    assert d["wpRestNonceRequired"] is False
    assert d["migrationPath"] == "standalone-browser->FastAPI"

def test_end_to_end_standalone_workflow():
    h = headers("e2e")

    project = client.post(
        "/standalone/v1/projects",
        headers=h,
        json={"name": "Migration Certification Project"},
    ).json()["project"]

    calc = client.post(
        "/standalone/v1/calculator/execute",
        headers=h,
        json={
            "calculationRequest": {
                "calculation": {"operation": "evaluate", "expression": "7*8"},
                "requestedResultType": "numeric",
                "requireVerification": True,
                "requireProvenance": True,
            },
            "projectId": project["id"],
            "saveResult": True,
            "title": "Fifty Six",
        },
    ).json()
    assert calc["calculationObject"]["result"]["value"]["float"] == 56.0
    cid = calc["savedCalculation"]["id"]

    graph = client.post(
        "/standalone/v1/renderer/view-spec",
        headers=h,
        json={
            "graphing": {
                "operation": "function-plot",
                "expression": "x**2-1",
                "variable": "x",
                "domain": [-2, 2],
                "samples": 101,
                "includeRoots": True,
            }
        },
    ).json()
    assert graph["viewSpec"]["result"]["viewCount"] >= 1

    notebook = client.post(
        "/standalone/v1/notebooks",
        headers=h,
        json={"projectId": project["id"], "title": "Migration Notebook"},
    ).json()["notebook"]

    entry = client.post(
        f"/standalone/v1/notebooks/{notebook['id']}/entries",
        headers=h,
        json={
            "kind": "calculation-reference",
            "savedCalculationId": cid,
            "markdown": "Certified standalone calculation",
        },
    ).json()["entry"]
    assert entry["savedCalculationId"] == cid

    history = client.get(
        f"/standalone/v1/projects/{project['id']}/history", headers=h
    ).json()["history"]
    assert history["count"] >= 1

    package = client.post(
        "/standalone/v1/reproducibility/packages",
        headers=h,
        json={
            "projectId": project["id"],
            "title": "Migration Repro Package",
            "calculationRequest": {
                "calculation": {"operation": "evaluate", "expression": "7*8"},
                "requestedResultType": "numeric",
                "requireVerification": True,
                "requireProvenance": True,
            },
        },
    ).json()["package"]

    verified = client.post(
        f"/standalone/v1/reproducibility/packages/{package['id']}/verify",
        headers=h,
        json={},
    ).json()
    assert verified["verified"] is True

    replayed = client.post(
        f"/standalone/v1/reproducibility/packages/{package['id']}/replay",
        headers=h,
        json={"comparisonMode": "strict"},
    ).json()
    assert replayed["certificate"]["reproducible"] is True

    launch = client.post(
        "/standalone/v1/launch",
        json={
            "route": "/workspace",
            "targetType": "project",
            "targetId": project["id"],
            "source": "direct",
            "ttlSeconds": 600,
        },
    ).json()
    assert launch["launchDescriptor"]["authenticationEmbedded"] is False

    state_cert = client.get("/standalone/v1/state-dependency/certification").json()
    assert state_cert["certification"] == "pass"

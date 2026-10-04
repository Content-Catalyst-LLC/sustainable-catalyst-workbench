import os
from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
DB = "/tmp/scwb-v12100-test.sqlite3"

def setup_module():
    Path(DB).unlink(missing_ok=True)
    os.environ["SCWB_SESSION_SECRET"] = "v12.10-test-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"] = "v12.10-test-link-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"] = DB
    os.environ["SCWB_STANDALONE_APP_URL"] = "https://workbench.example.test"
    os.environ["SCWB_PUBLIC_API_URL"] = "https://workbench-api.example.test"
    os.environ["SCWB_ALLOWED_ORIGINS"] = "https://workbench.example.test,https://sustainablecatalyst.com"

def teardown_module():
    for k in [
        "SCWB_SESSION_SECRET",
        "SCWB_DEEP_LINK_SECRET",
        "SCWB_PROJECT_STORE_PATH",
        "SCWB_STANDALONE_APP_URL",
        "SCWB_PUBLIC_API_URL",
        "SCWB_ALLOWED_ORIGINS",
    ]:
        os.environ.pop(k, None)
    for p in [DB, DB + "-wal", DB + "-shm"]:
        Path(p).unlink(missing_ok=True)

def headers():
    d = client.post(
        "/standalone/v1/auth/session/anonymous",
        json={"ttlSeconds": 600, "clientLabel": "v12100"},
    ).json()
    return {"Authorization": f"Bearer {d['token']}"}

def test_status():
    d = client.get("/v12100/status").json()
    assert d["version"] == "12.10.0"
    assert d["architectureCertification"] == "pass"
    assert d["productionEnvironmentCertification"] == "pass"
    assert d["productionReady"] is True
    assert d["wordpressRequired"] is False

def test_deployment_manifest():
    d = client.get("/standalone/v1/production/deployment-manifest").json()["deployment"]
    assert d["canonicalFrontend"] == "standalone-web-app"
    assert d["canonicalBackend"] == "FastAPI"
    assert d["canonicalPersistentState"] == "SQLite"
    assert d["wordpressRequired"] is False
    assert d["frontend"]["requiresWordPress"] is False
    assert d["backend"]["internalListen"] == "127.0.0.1:8088"

def test_environment_contract():
    e = client.get("/standalone/v1/production/environment").json()["environment"]
    assert e["standaloneAppUrl"] == "https://workbench.example.test"
    assert e["publicApiUrl"] == "https://workbench-api.example.test"
    assert e["requirements"]["durableSessionSecretConfigured"] is True
    assert e["requirements"]["durableDeepLinkSecretConfigured"] is True
    assert e["requirements"]["standaloneOriginAllowed"] is True

def test_production_certification():
    c = client.get("/standalone/v1/production/certification").json()
    assert c["certification"] == "pass"
    assert c["productionReady"] is True
    assert all(c["architectureChecks"].values())
    assert all(c["productionEnvironmentChecks"].values())
    assert c["remainingProductionActions"] == []
    assert c["v12Consolidation"]["v12SeriesConsolidated"] is True

def test_readiness():
    r = client.get("/standalone/v1/production/readiness").json()
    assert r["architectureReady"] is True
    assert r["productionEnvironmentReady"] is True
    assert r["productionReady"] is True
    assert r["remainingProductionActions"] == []

def test_session_probe():
    assert client.get("/standalone/v1/production/session-probe").status_code in (401, 403)
    d = client.get("/standalone/v1/production/session-probe", headers=headers()).json()
    assert d["canonicalSessionAuthority"] == "FastAPI"
    assert d["productionPath"] == "standalone-web-app->FastAPI->SQLite"

def test_direct_standalone_calculation_still_works():
    h = headers()
    project = client.post(
        "/standalone/v1/projects",
        headers=h,
        json={"name": "v12.10 Production Project"},
    ).json()["project"]

    calc = client.post(
        "/standalone/v1/calculator/execute",
        headers=h,
        json={
            "calculationRequest": {
                "calculation": {"operation": "evaluate", "expression": "9*9"},
                "requestedResultType": "numeric",
                "requireVerification": True,
                "requireProvenance": True,
            },
            "projectId": project["id"],
            "saveResult": True,
            "title": "Eighty One",
        },
    ).json()

    assert calc["calculationObject"]["result"]["value"]["float"] == 81.0
    assert calc["saved"] is True
    assert calc["wordpressRequired"] is False

import os
from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
DB="/tmp/scwb-v1280-test.sqlite3"

def setup_module():
    Path(DB).unlink(missing_ok=True)
    os.environ["SCWB_SESSION_SECRET"]="v12.8-test-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"]="v12.8-test-link-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]=DB

def teardown_module():
    for k in ["SCWB_SESSION_SECRET","SCWB_DEEP_LINK_SECRET","SCWB_PROJECT_STORE_PATH"]:
        os.environ.pop(k,None)
    for p in [DB,DB+"-wal",DB+"-shm"]:
        Path(p).unlink(missing_ok=True)

def headers():
    s=client.post("/standalone/v1/auth/session/anonymous",json={"ttlSeconds":600}).json()
    return {"Authorization":f"Bearer {s['token']}"}

def test_status_passes():
    d=client.get("/v1280/status").json()
    assert d["version"]=="12.8.0"
    assert d["certification"]=="pass"
    assert d["wordpressRequired"] is False
    assert d["capabilities"]["wordpressStateDependencyEliminated"] is True

def test_authority_has_no_wordpress_state():
    d=client.get("/standalone/v1/state-authority").json()["authority"]
    assert d["wordpressCanonicalState"] is False
    assert all(x["wordpressDependency"] is False for x in d["stateCategories"])
    assert "project-store" in d["wordpressProhibitedRoles"]
    assert d["legacyCompatibility"]["historicalWordPressModulesMayRemainLoaded"] is True

def test_certification_checks_all_green():
    d=client.get("/standalone/v1/state-dependency/certification").json()
    assert d["certification"]=="pass"
    assert all(d["checks"].values())
    assert d["boundary"]["wordpressMayOwnCanonicalV12State"] is False
    assert d["storage"]["projects"]["engine"]=="sqlite"
    assert d["storage"]["notebooks"]["engine"]=="sqlite"
    assert d["storage"]["packages"]["engine"]=="sqlite"

def test_wordpress_policy_is_adapter_only():
    d=client.get("/standalone/v1/state-dependency/wordpress-policy").json()["policy"]
    assert d["wordpressRequired"] is False
    assert "standalone-browser -> FastAPI" in d["canonicalStatePath"]
    assert any("get_option/update_option" in x for x in d["forbiddenCanonicalStatePatterns"])

def test_session_probe_requires_standalone_bearer():
    assert client.get("/standalone/v1/state-dependency/session-probe").status_code in (401,403)
    d=client.get("/standalone/v1/state-dependency/session-probe",headers=headers()).json()
    assert d["wordpressRequired"] is False
    assert d["wpRestNonceRequired"] is False
    assert d["canonicalSessionAuthority"]=="FastAPI"

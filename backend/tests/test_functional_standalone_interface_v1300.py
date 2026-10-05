import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
DB="/tmp/scwb-v1300-test.sqlite3"

def setup_module():
    Path(DB).unlink(missing_ok=True)
    os.environ["SCWB_SESSION_SECRET"]="v13-test-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"]="v13-test-link-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]=DB
    os.environ["SCWB_STANDALONE_APP_URL"]="https://workbench.example.test"
    os.environ["SCWB_PUBLIC_API_URL"]="https://workbench-api.example.test"
    os.environ["SCWB_ALLOWED_ORIGINS"]="https://workbench.example.test"

def teardown_module():
    for k in ["SCWB_SESSION_SECRET","SCWB_DEEP_LINK_SECRET","SCWB_PROJECT_STORE_PATH","SCWB_STANDALONE_APP_URL","SCWB_PUBLIC_API_URL","SCWB_ALLOWED_ORIGINS"]:
        os.environ.pop(k,None)
    for p in [DB,DB+"-wal",DB+"-shm"]: Path(p).unlink(missing_ok=True)

def token():
    d=client.post("/standalone/v1/auth/session/anonymous",json={"ttlSeconds":600,"clientLabel":"v1300"}).json()
    return d["token"]

def test_status_and_capabilities():
    d=client.get("/v1300/status").json()
    assert d["version"]=="13.0.0"
    assert d["functionalReady"] is True
    assert d["wordpressRequired"] is False
    assert d["capabilities"]["calculationExecute"] is True
    assert d["capabilities"]["graphBrowserRenderer"] is True
    assert d["capabilities"]["reproducibilityReplay"] is True

def test_interface_readiness():
    d=client.get("/standalone/v1/interface/readiness").json()
    assert d["functionalReady"] is True
    assert all(d["checks"].values())

def test_session_probe():
    assert client.get("/standalone/v1/interface/session-probe").status_code in (401,403)
    d=client.get("/standalone/v1/interface/session-probe",headers={"Authorization":f"Bearer {token()}"}).json()
    assert d["functionalStandalone"] is True

def test_end_to_end_core_workflow():
    h={"Authorization":f"Bearer {token()}"}
    project=client.post("/standalone/v1/projects",headers=h,json={"name":"v13 Functional Project"}).json()["project"]
    calc_req={"calculation":{"operation":"evaluate","expression":"6*7"},"requestedResultType":"numeric","requireVerification":True,"requireProvenance":True}
    calc=client.post("/standalone/v1/calculator/execute",headers=h,json={"calculationRequest":calc_req,"projectId":project["id"],"saveResult":True,"title":"Forty Two"}).json()
    assert calc["calculationObject"]["result"]["value"]["float"]==42.0
    assert calc["saved"] is True
    notebook=client.post("/standalone/v1/notebooks",headers=h,json={"projectId":project["id"],"title":"Functional Notebook"}).json()["notebook"]
    client.post(f"/standalone/v1/notebooks/{notebook['id']}/entries",headers=h,json={"kind":"calculation-reference","markdown":"42","savedCalculationId":calc["savedCalculation"]["id"]}).raise_for_status()
    hist=client.get(f"/standalone/v1/projects/{project['id']}/history",headers=h).json()
    assert hist["history"]
    pkg=client.post("/standalone/v1/reproducibility/packages",headers=h,json={"projectId":project["id"],"calculationRequest":calc_req,"calculationObject":calc["calculationObject"],"title":"42 Package"}).json()["package"]
    client.post(f"/standalone/v1/reproducibility/packages/{pkg['id']}/verify",headers=h,json={}).raise_for_status()
    replay=client.post(f"/standalone/v1/reproducibility/packages/{pkg['id']}/replay",headers=h,json={"comparisonMode":"strict"}).json()
    assert replay["ok"] is True

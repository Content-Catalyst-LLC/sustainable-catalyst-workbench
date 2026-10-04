import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

TEST_DB="/tmp/scwb-v1230-test.sqlite3"

def setup_module():
    Path(TEST_DB).unlink(missing_ok=True)
    os.environ["SCWB_SESSION_SECRET"]="v12.3-test-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]=TEST_DB

def teardown_module():
    os.environ.pop("SCWB_SESSION_SECRET",None)
    os.environ.pop("SCWB_PROJECT_STORE_PATH",None)
    Path(TEST_DB).unlink(missing_ok=True)
    Path(TEST_DB+"-wal").unlink(missing_ok=True)
    Path(TEST_DB+"-shm").unlink(missing_ok=True)

def session_headers(label="calculator-test"):
    created=client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":600,"clientLabel":label
    }).json()
    return {"Authorization":f"Bearer {created['token']}"}

def test_status():
    d=client.get("/v1230/status").json()
    assert d["version"]=="12.3.0"
    assert d["wordpressRequired"] is False
    assert d["capabilities"]["standaloneCalculatorWorkspace"] is True
    assert d["capabilities"]["oneStepExecuteAndSave"] is True

def test_config_requires_session_and_returns_projects():
    h=session_headers()
    d=client.get("/standalone/v1/calculator/config",headers=h).json()
    assert d["ok"] is True
    assert d["calculator"]["defaults"]["operation"]=="evaluate"
    assert any(op["id"]=="differentiate" for op in d["calculator"]["operations"])
    assert d["projects"]==[]

def test_execute_unsaved_calculation():
    h=session_headers()
    d=client.post("/standalone/v1/calculator/execute",headers=h,json={
        "calculationRequest":{
            "calculation":{"operation":"evaluate","expression":"2+3*4"},
            "requestedResultType":"numeric"
        },
        "saveResult":False,
        "title":"Arithmetic"
    }).json()
    assert d["ok"] is True
    assert d["saved"] is False
    obj=d["calculationObject"]
    assert obj["schema"]=="sc-workbench-calculation-object/1.0"
    assert obj["result"]["value"]["float"]==14.0
    assert obj["verification"]["status"]=="verified-by-canonical-runtime"
    assert obj["provenance"]["canonicalBackend"]=="FastAPI"

def test_execute_and_save_to_project():
    h=session_headers("save-test")
    project=client.post("/standalone/v1/projects",headers=h,json={
        "name":"Calculator Project"
    }).json()["project"]

    d=client.post("/standalone/v1/calculator/execute",headers=h,json={
        "calculationRequest":{
            "calculation":{
                "operation":"differentiate",
                "expression":"x**3 + 2*x",
                "variable":"x"
            },
            "requestedResultType":"symbolic",
            "requireVerification":True,
            "requireProvenance":True
        },
        "projectId":project["id"],
        "saveResult":True,
        "title":"Derivative",
        "tags":["calculus"]
    }).json()

    assert d["saved"] is True
    obj=d["calculationObject"]
    saved=d["savedCalculation"]
    assert obj["result"]["value"]["expression"]=="3*x**2 + 2"
    assert saved["projectId"]==project["id"]
    assert saved["calculationObjectHash"]==obj["calculationObjectHash"]

    listed=client.get(
        f"/standalone/v1/projects/{project['id']}/calculations",
        headers=h
    ).json()
    assert listed["count"]==1
    assert listed["calculations"][0]["id"]==saved["id"]

def test_save_requires_project_id():
    h=session_headers()
    r=client.post("/standalone/v1/calculator/execute",headers=h,json={
        "calculationRequest":{
            "calculation":{"operation":"evaluate","expression":"5"},
            "requestedResultType":"numeric"
        },
        "saveResult":True
    })
    assert r.status_code==422

def test_project_ownership_enforced():
    h1=session_headers("owner-one")
    h2=session_headers("owner-two")
    project=client.post("/standalone/v1/projects",headers=h1,json={
        "name":"Private"
    }).json()["project"]

    r=client.post("/standalone/v1/calculator/execute",headers=h2,json={
        "calculationRequest":{
            "calculation":{"operation":"evaluate","expression":"10"},
            "requestedResultType":"numeric"
        },
        "projectId":project["id"],
        "saveResult":True
    })
    assert r.status_code==404

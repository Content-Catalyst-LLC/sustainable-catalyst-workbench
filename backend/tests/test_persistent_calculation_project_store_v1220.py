import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

TEST_DB="/tmp/scwb-v1220-test.sqlite3"

def setup_module():
    Path(TEST_DB).unlink(missing_ok=True)
    os.environ["SCWB_SESSION_SECRET"]="v12.2-test-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]=TEST_DB

def teardown_module():
    os.environ.pop("SCWB_SESSION_SECRET",None)
    os.environ.pop("SCWB_PROJECT_STORE_PATH",None)
    Path(TEST_DB).unlink(missing_ok=True)
    Path(TEST_DB+"-wal").unlink(missing_ok=True)
    Path(TEST_DB+"-shm").unlink(missing_ok=True)

def session_headers(label="pytest"):
    created=client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":600,"clientLabel":label
    }).json()
    return {"Authorization":f"Bearer {created['token']}"}, created["session"]

def test_status():
    d=client.get("/v1220/status").json()
    assert d["version"]=="12.2.0"
    assert d["wordpressRequired"] is False
    assert d["storage"]["engine"]=="sqlite"
    assert d["capabilities"]["persistentProjects"] is True

def test_project_crud():
    h,_=session_headers()
    created=client.post("/standalone/v1/projects",headers=h,json={
        "name":"Physics Project",
        "description":"Persistent standalone project",
        "metadata":{"course":"demo"}
    }).json()["project"]
    pid=created["id"]
    assert created["name"]=="Physics Project"

    listed=client.get("/standalone/v1/projects",headers=h).json()
    assert listed["count"]==1
    assert listed["projects"][0]["id"]==pid

    updated=client.patch(f"/standalone/v1/projects/{pid}",headers=h,json={
        "name":"Updated Physics Project"
    }).json()["project"]
    assert updated["name"]=="Updated Physics Project"

    fetched=client.get(f"/standalone/v1/projects/{pid}",headers=h).json()["project"]
    assert fetched["id"]==pid

def test_save_and_reload_calculation():
    h,_=session_headers("calc-owner")
    project=client.post("/standalone/v1/projects",headers=h,json={
        "name":"Calculation Project"
    }).json()["project"]

    calculation_object={
        "schema":"sc-workbench-calculation-object/1.0",
        "input":{"expression":"2+2"},
        "result":{"value":4},
        "calculationObjectHash":"known-calculation-hash"
    }
    saved=client.post("/standalone/v1/calculations",headers=h,json={
        "projectId":project["id"],
        "title":"Two plus two",
        "calculationObject":calculation_object,
        "tags":["arithmetic","demo"]
    }).json()["calculation"]

    assert saved["calculationObjectHash"]=="known-calculation-hash"
    assert saved["calculationObject"]["result"]["value"]==4

    listed=client.get(
        f"/standalone/v1/projects/{project['id']}/calculations",
        headers=h
    ).json()
    assert listed["count"]==1

    loaded=client.get(
        f"/standalone/v1/calculations/{saved['id']}",
        headers=h
    ).json()["calculation"]
    assert loaded["id"]==saved["id"]
    assert loaded["calculationObject"]==calculation_object

def test_owner_isolation():
    h1,_=session_headers("owner-1")
    h2,_=session_headers("owner-2")
    project=client.post("/standalone/v1/projects",headers=h1,json={
        "name":"Private Project"
    }).json()["project"]

    assert client.get(f"/standalone/v1/projects/{project['id']}",headers=h2).status_code==404

def test_project_delete_cascades_calculations():
    h,_=session_headers("cascade")
    project=client.post("/standalone/v1/projects",headers=h,json={
        "name":"Cascade Project"
    }).json()["project"]

    saved=client.post("/standalone/v1/calculations",headers=h,json={
        "projectId":project["id"],
        "title":"Saved",
        "calculationObject":{"result":{"value":1}}
    }).json()["calculation"]

    deleted=client.delete(
        f"/standalone/v1/projects/{project['id']}",
        headers=h
    ).json()
    assert deleted["cascadeDeletedCalculations"]==1
    assert client.get(
        f"/standalone/v1/calculations/{saved['id']}",
        headers=h
    ).status_code==404

def test_store_survives_new_request_connections():
    h,_=session_headers("persistence")
    p=client.post("/standalone/v1/projects",headers=h,json={
        "name":"Durable Project"
    }).json()["project"]
    # Each route opens a new sqlite connection; successful reload proves
    # persistence outside request-local memory.
    reloaded=client.get(f"/standalone/v1/projects/{p['id']}",headers=h).json()["project"]
    assert reloaded["id"]==p["id"]

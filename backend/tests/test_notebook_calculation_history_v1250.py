import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
DB="/tmp/scwb-v1250-test.sqlite3"

def setup_module():
    Path(DB).unlink(missing_ok=True)
    os.environ["SCWB_SESSION_SECRET"]="v12.5-test-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]=DB

def teardown_module():
    os.environ.pop("SCWB_SESSION_SECRET",None)
    os.environ.pop("SCWB_PROJECT_STORE_PATH",None)
    for p in [DB,DB+"-wal",DB+"-shm"]: Path(p).unlink(missing_ok=True)

def headers(label="v1250"):
    s=client.post("/standalone/v1/auth/session/anonymous",json={"ttlSeconds":600,"clientLabel":label}).json()
    return {"Authorization":f"Bearer {s['token']}"}

def project(h,name="Notebook Project"):
    return client.post("/standalone/v1/projects",headers=h,json={"name":name}).json()["project"]

def test_status():
    d=client.get("/v1250/status").json()
    assert d["version"]=="12.5.0"
    assert d["capabilities"]["persistentNotebooks"] is True
    assert d["capabilities"]["calculationHistory"] is True

def test_notebook_and_note_entry():
    h=headers(); p=project(h)
    n=client.post("/standalone/v1/notebooks",headers=h,json={"projectId":p["id"],"title":"Research Notes"}).json()["notebook"]
    assert n["projectId"]==p["id"]
    e=client.post(f"/standalone/v1/notebooks/{n['id']}/entries",headers=h,json={"kind":"note","markdown":"First observation","pinned":True}).json()["entry"]
    assert e["ordinal"]==1 and e["pinned"] is True
    listed=client.get(f"/standalone/v1/notebooks/{n['id']}/entries",headers=h).json()
    assert listed["count"]==1

def test_calculation_reference_and_history():
    h=headers("history"); p=project(h,"History Project")
    calc=client.post("/standalone/v1/calculator/execute",headers=h,json={
      "calculationRequest":{"calculation":{"operation":"evaluate","expression":"6*7"},"requestedResultType":"numeric"},
      "projectId":p["id"],"saveResult":True,"title":"Forty Two"
    }).json()
    cid=calc["savedCalculation"]["id"]

    n=client.post("/standalone/v1/notebooks",headers=h,json={"projectId":p["id"],"title":"Lab Notebook"}).json()["notebook"]
    e=client.post(f"/standalone/v1/notebooks/{n['id']}/entries",headers=h,json={
      "kind":"calculation-reference","savedCalculationId":cid,"markdown":"Key result"
    }).json()["entry"]
    assert e["savedCalculationId"]==cid

    hist=client.get(f"/standalone/v1/projects/{p['id']}/history",headers=h).json()["history"]
    assert hist["count"]==1
    assert hist["items"][0]["id"]==cid

    timeline=client.get(f"/standalone/v1/projects/{p['id']}/timeline",headers=h).json()["timeline"]
    kinds={x["kind"] for x in timeline["items"]}
    assert "calculation" in kinds
    assert "notebook-entry" in kinds

def test_owner_isolation():
    h1=headers("one"); h2=headers("two"); p=project(h1,"Private")
    n=client.post("/standalone/v1/notebooks",headers=h1,json={"projectId":p["id"],"title":"Private Notebook"}).json()["notebook"]
    assert client.get(f"/standalone/v1/notebooks/{n['id']}/entries",headers=h2).status_code==404

def test_update_and_delete_entry():
    h=headers("edit"); p=project(h)
    n=client.post("/standalone/v1/notebooks",headers=h,json={"projectId":p["id"],"title":"Edit"}).json()["notebook"]
    e=client.post(f"/standalone/v1/notebooks/{n['id']}/entries",headers=h,json={"kind":"note","markdown":"draft"}).json()["entry"]
    u=client.patch(f"/standalone/v1/notebook-entries/{e['id']}",headers=h,json={"markdown":"revised","pinned":True}).json()["entry"]
    assert u["markdown"]=="revised" and u["pinned"] is True
    d=client.delete(f"/standalone/v1/notebook-entries/{e['id']}",headers=h).json()
    assert d["deletedEntryId"]==e["id"]

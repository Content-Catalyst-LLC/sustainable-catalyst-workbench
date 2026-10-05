import os
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def setup_module():
    os.environ["SCWB_SESSION_SECRET"]="v136-local-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"]="v136-local-link-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]="/tmp/scwb-v1360-test.sqlite3"
    try: os.remove("/tmp/scwb-v1360-test.sqlite3")
    except FileNotFoundError: pass

def token():
    return client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":3600,"clientLabel":"v136-test"
    }).json()["token"]

def test_status():
    d=client.get("/v1360/status").json()
    assert d["version"]=="13.6.0"
    assert d["timelineWorkspaceReady"] is True
    assert all(d["checks"].values())

def test_notebook_attachments_and_timeline():
    h={"Authorization":f"Bearer {token()}"}
    p=client.post("/standalone/v1/projects",headers=h,json={"name":"Timeline Project","description":"","metadata":{}}).json()["project"]
    rs=client.post("/standalone/v1/research-sessions",headers=h,json={
        "projectId":p["id"],"title":"Timeline Session","purpose":"Unified research record","tags":[],"metadata":{}
    }).json()["researchSession"]
    nb=client.post("/standalone/v1/notebooks",headers=h,json={
        "projectId":p["id"],"title":"Research Notebook","description":"","metadata":{}
    }).json()["notebook"]
    note=client.post(f"/standalone/v1/notebooks/{nb['id']}/structured-notes",headers=h,json={
        "title":"Observation","markdown":"Initial note","researchSessionId":rs["id"],"pinned":True,"metadata":{}
    }).json()["entry"]
    assert note["kind"]=="note"
    assert note["researchSessionId"]==rs["id"]

    g=client.post("/standalone/v1/graph-studio/graphs",headers=h,json={
        "projectId":p["id"],"researchSessionId":rs["id"],"title":"x squared",
        "graphType":"cartesian","series":[{"expression":"x**2"}],
        "domain":[-2,2],"yDomain":[-1,5],"samples":51,"metadata":{}
    }).json()["graph"]
    attached=client.post(f"/standalone/v1/notebooks/{nb['id']}/attach",headers=h,json={
        "objectType":"graph","objectId":g["id"],"title":"Graph evidence","note":"Attached graph",
        "researchSessionId":rs["id"],"pinned":False,"metadata":{}
    }).json()["attachment"]
    assert attached["graphId"]==g["id"]
    assert attached["kind"]=="graph-reference"

    entries=client.get(f"/standalone/v1/notebooks/{nb['id']}/research-entries",headers=h).json()
    assert entries["count"]==2

    project_tl=client.get(f"/standalone/v1/projects/{p['id']}/research-timeline",headers=h).json()["timeline"]
    assert any(x["kind"]=="graph" for x in project_tl["items"])
    assert any(x["kind"]=="notebook-entry" for x in project_tl["items"])

    session_tl=client.get(f"/standalone/v1/research-sessions/{rs['id']}/timeline",headers=h).json()["timeline"]
    assert session_tl["scope"]=="research-session"
    assert all(x["researchSessionId"]==rs["id"] for x in session_tl["items"])

    export=client.get(f"/standalone/v1/research-sessions/{rs['id']}/history-export",headers=h)
    assert export.status_code==200
    assert "# Timeline Session" in export.text
    assert "X-SC-Research-History-Hash" in export.headers

def test_owner_isolation():
    h1={"Authorization":f"Bearer {token()}"}
    h2={"Authorization":f"Bearer {token()}"}
    p=client.post("/standalone/v1/projects",headers=h1,json={"name":"P","description":"","metadata":{}}).json()["project"]
    r=client.get(f"/standalone/v1/projects/{p['id']}/research-timeline",headers=h2)
    assert r.status_code==404

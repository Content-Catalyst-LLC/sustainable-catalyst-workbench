import os
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def _token():
    d=client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":3600,"clientLabel":"v134-test"
    }).json()
    return d["token"]

def setup_module():
    os.environ["SCWB_SESSION_SECRET"]="v134-local-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"]="v134-local-link-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]="/tmp/scwb-v1340-test.sqlite3"
    try: os.remove("/tmp/scwb-v1340-test.sqlite3")
    except FileNotFoundError: pass

def test_status():
    d=client.get("/v1340/status").json()
    assert d["version"]=="13.4.0"
    assert d["projectWorkspaceReady"] is True
    assert all(d["checks"].values())

def test_persistent_research_session_lifecycle():
    h={"Authorization":f"Bearer {_token()}"}
    p=client.post("/standalone/v1/projects",headers=h,json={
        "name":"Persistent Session Project","description":"","metadata":{}
    }).json()["project"]
    s=client.post("/standalone/v1/research-sessions",headers=h,json={
        "projectId":p["id"],"title":"Accelerated Weathering Study",
        "purpose":"Keep calculator, graph, notebook and package work together.",
        "tags":["research","session"],"metadata":{"interfaceVersion":"13.4.0"}
    }).json()["researchSession"]
    assert s["projectId"]==p["id"]
    assert s["status"]=="active"

    listed=client.get(f"/standalone/v1/projects/{p['id']}/research-sessions",headers=h).json()
    assert listed["count"]==1
    assert listed["researchSessions"][0]["id"]==s["id"]

    updated=client.patch(f"/standalone/v1/research-sessions/{s['id']}",headers=h,json={
        "lastRoute":"calculator","purpose":"Updated purpose"
    }).json()["researchSession"]
    assert updated["lastRoute"]=="calculator"
    assert updated["purpose"]=="Updated purpose"

    a=client.post(f"/standalone/v1/research-sessions/{s['id']}/activity",headers=h,json={
        "kind":"calculation","label":"Calculated 6*7","objectType":"calculation",
        "objectId":"calc-1","route":"calculator","metadata":{"result":"42"}
    }).json()["activity"]
    assert a["sessionId"]==s["id"]

    activity=client.get(f"/standalone/v1/research-sessions/{s['id']}/activity",headers=h).json()
    assert activity["count"]==1

    summary=client.get(f"/standalone/v1/research-sessions/{s['id']}/summary",headers=h).json()["summary"]
    assert summary["resumable"] is True
    assert summary["counts"]["activities"]==1

def test_owner_isolation():
    h1={"Authorization":f"Bearer {_token()}"}
    h2={"Authorization":f"Bearer {_token()}"}
    p=client.post("/standalone/v1/projects",headers=h1,json={
        "name":"Owner 1","description":"","metadata":{}
    }).json()["project"]
    s=client.post("/standalone/v1/research-sessions",headers=h1,json={
        "projectId":p["id"],"title":"Private Session","purpose":"","tags":[],"metadata":{}
    }).json()["researchSession"]
    r=client.get(f"/standalone/v1/research-sessions/{s['id']}",headers=h2)
    assert r.status_code==404

import os
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def setup_module():
    os.environ["SCWB_SESSION_SECRET"]="v138-local-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"]="v138-local-link-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]="/tmp/scwb-v1380-test.sqlite3"
    try: os.remove("/tmp/scwb-v1380-test.sqlite3")
    except FileNotFoundError: pass

def token():
    return client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":3600,"clientLabel":"v138-test"
    }).json()["token"]

def test_status():
    d=client.get("/v1380/status").json()
    assert d["version"]=="13.8.0"
    assert d["unifiedWorkspaceReady"] is True
    assert all(d["checks"].values())

def test_unified_project_and_session_workspace():
    h={"Authorization":f"Bearer {token()}"}
    p=client.post("/standalone/v1/projects",headers=h,json={
        "name":"Unified Project","description":"","metadata":{}
    }).json()["project"]
    rs=client.post("/standalone/v1/research-sessions",headers=h,json={
        "projectId":p["id"],"title":"Unified Session","purpose":"One operating surface",
        "tags":[],"metadata":{}
    }).json()["researchSession"]

    proj=client.get(f"/standalone/v1/projects/{p['id']}/unified-workspace",headers=h).json()["workspace"]
    assert proj["projectId"]==p["id"]
    assert proj["counts"]["researchSessions"]==1
    assert len(proj["surfaces"])==4
    assert proj["wordpressRequired"] is False

    sess=client.get(f"/standalone/v1/research-sessions/{rs['id']}/unified-workspace",headers=h).json()["workspace"]
    assert sess["researchSessionId"]==rs["id"]
    assert sess["researchSession"]["projectId"]==p["id"]

    handoff=client.post(f"/standalone/v1/projects/{p['id']}/unified-workspace/handoff",headers=h,json={
        "target":"graphs","objectType":"graph","objectId":"example",
        "researchSessionId":rs["id"],"metadata":{"source":"workspace"}
    }).json()["handoff"]
    assert handoff["route"]=="/graphs"
    assert handoff["preservesProjectContext"] is True
    assert handoff["preservesResearchSessionContext"] is True

def test_owner_isolation():
    h1={"Authorization":f"Bearer {token()}"}
    h2={"Authorization":f"Bearer {token()}"}
    p=client.post("/standalone/v1/projects",headers=h1,json={
        "name":"Private Unified","description":"","metadata":{}
    }).json()["project"]
    assert client.get(f"/standalone/v1/projects/{p['id']}/unified-workspace",headers=h2).status_code==404

import os
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def setup_module():
    os.environ["SCWB_SESSION_SECRET"]="v137-local-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"]="v137-local-link-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]="/tmp/scwb-v1370-test.sqlite3"
    try: os.remove("/tmp/scwb-v1370-test.sqlite3")
    except FileNotFoundError: pass

def token():
    return client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":3600,"clientLabel":"v137-test"
    }).json()["token"]

def test_status():
    d=client.get("/v1370/status").json()
    assert d["version"]=="13.7.0"
    assert d["packageWorkspaceReady"] is True
    assert all(d["checks"].values())

def test_package_workspace_lifecycle():
    h={"Authorization":f"Bearer {token()}"}
    p=client.post("/standalone/v1/projects",headers=h,json={
        "name":"Repro Project","description":"","metadata":{}
    }).json()["project"]
    rs=client.post("/standalone/v1/research-sessions",headers=h,json={
        "projectId":p["id"],"title":"Repro Session","purpose":"","tags":[],"metadata":{}
    }).json()["researchSession"]

    calc_req={"calculation":{"operation":"evaluate","expression":"6*7"},"requestedResultType":"numeric","requireVerification":True,"requireProvenance":True}
    pkg=client.post("/standalone/v1/reproducibility/packages",headers=h,json={
        "projectId":p["id"],"calculationRequest":calc_req,
        "title":"42 Package","notes":"initial","metadata":{"interfaceVersion":"13.7.0"}
    }).json()["package"]

    updated=client.patch(f"/standalone/v1/reproducibility/workspace/{pkg['id']}",headers=h,json={
        "title":"Updated Package","notes":"updated","researchSessionId":rs["id"],
        "metadata":{"interfaceVersion":"13.7.0"}
    }).json()["package"]
    assert updated["researchSessionId"]==rs["id"]
    assert updated["title"]=="Updated Package"

    listed=client.get(f"/standalone/v1/projects/{p['id']}/reproducibility/workspace",headers=h).json()
    assert listed["count"]==1

    verified=client.post(f"/standalone/v1/reproducibility/workspace/{pkg['id']}/verify",headers=h).json()
    assert verified["verified"] is True

    replayed=client.post(f"/standalone/v1/reproducibility/workspace/{pkg['id']}/replay",headers=h,json={
        "comparisonMode":"result-only"
    }).json()
    assert replayed["comparison"]["comparisonMode"]=="result-only"
    assert "certificateHash" in replayed["comparison"]

    exported=client.get(f"/standalone/v1/reproducibility/workspace/{pkg['id']}/export",headers=h).json()
    assert exported["schema"]=="sc-workbench-reproducibility-package-export/1.0"
    assert exported["package"]["id"]==pkg["id"]
    assert "exportHash" in exported

def test_owner_isolation():
    h1={"Authorization":f"Bearer {token()}"}
    h2={"Authorization":f"Bearer {token()}"}
    p=client.post("/standalone/v1/projects",headers=h1,json={"name":"Private","description":"","metadata":{}}).json()["project"]
    pkg=client.post("/standalone/v1/reproducibility/packages",headers=h1,json={
        "projectId":p["id"],
        "calculationRequest":{"calculation":{"operation":"evaluate","expression":"2+2"},"requestedResultType":"numeric","requireVerification":True,"requireProvenance":True},
        "title":"Private Package","notes":"","metadata":{}
    }).json()["package"]
    assert client.get(f"/standalone/v1/reproducibility/workspace/{pkg['id']}",headers=h2).status_code==404

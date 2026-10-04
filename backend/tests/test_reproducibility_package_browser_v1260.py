import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
DB="/tmp/scwb-v1260-test.sqlite3"

def setup_module():
    Path(DB).unlink(missing_ok=True)
    os.environ["SCWB_SESSION_SECRET"]="v12.6-test-secret"
    os.environ["SCWB_PROJECT_STORE_PATH"]=DB

def teardown_module():
    os.environ.pop("SCWB_SESSION_SECRET",None)
    os.environ.pop("SCWB_PROJECT_STORE_PATH",None)
    for p in [DB,DB+"-wal",DB+"-shm"]: Path(p).unlink(missing_ok=True)

def headers(label="pkg"):
    s=client.post("/standalone/v1/auth/session/anonymous",json={"ttlSeconds":600,"clientLabel":label}).json()
    return {"Authorization":f"Bearer {s['token']}"}

def project(h):
    return client.post("/standalone/v1/projects",headers=h,json={"name":"Repro Project"}).json()["project"]

def package_payload(project_id):
    return {
      "projectId":project_id,
      "title":"Arithmetic Package",
      "notes":"deterministic replay",
      "calculationRequest":{
        "calculation":{"operation":"evaluate","expression":"2+3*4"},
        "requestedResultType":"numeric",
        "requireVerification":True,
        "requireProvenance":True
      }
    }

def test_status():
    d=client.get("/v1260/status").json()
    assert d["version"]=="12.6.0"
    assert d["capabilities"]["persistentPackageIndex"] is True
    assert d["canonicalReplayEngine"].startswith("v11.17")

def test_create_list_get_verify_replay():
    h=headers(); p=project(h)
    created=client.post("/standalone/v1/reproducibility/packages",headers=h,json=package_payload(p["id"])).json()["package"]
    assert created["projectId"]==p["id"]
    assert created["envelopeHash"]

    listed=client.get(f"/standalone/v1/projects/{p['id']}/reproducibility/packages",headers=h).json()
    assert listed["count"]==1

    fetched=client.get(f"/standalone/v1/reproducibility/packages/{created['id']}",headers=h).json()["package"]
    assert fetched["id"]==created["id"]

    verified=client.post(f"/standalone/v1/reproducibility/packages/{created['id']}/verify",headers=h).json()
    assert verified["verified"] is True

    replayed=client.post(f"/standalone/v1/reproducibility/packages/{created['id']}/replay",headers=h,json={"comparisonMode":"strict"}).json()
    assert replayed["certificate"]["reproducible"] is True
    assert replayed["certificate"]["divergences"]==[]

    after=client.get(f"/standalone/v1/reproducibility/packages/{created['id']}",headers=h).json()["package"]
    assert after["lastReplayStatus"]=="reproducible"
    assert after["lastReplayAt"] is not None

def test_owner_isolation():
    h1=headers("one"); h2=headers("two"); p=project(h1)
    pkg=client.post("/standalone/v1/reproducibility/packages",headers=h1,json=package_payload(p["id"])).json()["package"]
    assert client.get(f"/standalone/v1/reproducibility/packages/{pkg['id']}",headers=h2).status_code==404

def test_delete():
    h=headers("delete"); p=project(h)
    pkg=client.post("/standalone/v1/reproducibility/packages",headers=h,json=package_payload(p["id"])).json()["package"]
    d=client.delete(f"/standalone/v1/reproducibility/packages/{pkg['id']}",headers=h).json()
    assert d["deletedPackageId"]==pkg["id"]

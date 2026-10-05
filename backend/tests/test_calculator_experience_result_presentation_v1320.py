import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
DB="/tmp/scwb-v1320-test.sqlite3"
def setup_module():
    Path(DB).unlink(missing_ok=True)
    os.environ["SCWB_SESSION_SECRET"]="v132-test"
    os.environ["SCWB_DEEP_LINK_SECRET"]="v132-link"
    os.environ["SCWB_PROJECT_STORE_PATH"]=DB
    os.environ["SCWB_STANDALONE_APP_URL"]="https://workbench.example.test"
    os.environ["SCWB_PUBLIC_API_URL"]="https://workbench-api.example.test"
    os.environ["SCWB_ALLOWED_ORIGINS"]="https://workbench.example.test"
def teardown_module():
    for k in ["SCWB_SESSION_SECRET","SCWB_DEEP_LINK_SECRET","SCWB_PROJECT_STORE_PATH","SCWB_STANDALONE_APP_URL","SCWB_PUBLIC_API_URL","SCWB_ALLOWED_ORIGINS"]: os.environ.pop(k,None)
    for p in [DB,DB+"-wal",DB+"-shm"]: Path(p).unlink(missing_ok=True)
def token(): return client.post("/standalone/v1/auth/session/anonymous",json={"ttlSeconds":600,"clientLabel":"v1320"}).json()["token"]
def test_status():
    d=client.get("/v1320/status").json()
    assert d["version"]=="13.2.0" and d["experienceReady"] is True
def test_experience_contract():
    d=client.get("/standalone/v1/calculator/experience-contract").json()["experience"]
    assert d["canonicalComputationAuthority"]=="FastAPI" and all(d["features"].values())
def test_presentation_adapter():
    h={"Authorization":f"Bearer {token()}"}
    req={"calculation":{"operation":"evaluate","expression":"6*7"},"requestedResultType":"numeric","requireVerification":True,"requireProvenance":True}
    obj=client.post("/standalone/v1/calculator/execute",headers=h,json={"calculationRequest":req,"saveResult":False,"title":"42"}).json()["calculationObject"]
    d=client.post("/standalone/v1/calculator/presentation",headers=h,json={"calculationObject":obj,"title":"42"}).json()["presentation"]
    assert d["primaryResult"]["display"] in {"42.0","42"}
    assert d["execution"]["engine"]
    assert d["verification"]["status"]
    assert d["provenance"]["canonicalBackend"]=="FastAPI"

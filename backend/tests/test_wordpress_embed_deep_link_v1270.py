import os
from urllib.parse import urlparse,parse_qs
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def setup_module():
    os.environ["SCWB_DEEP_LINK_SECRET"]="v12.7-deep-link-test-secret"
    os.environ["SCWB_SESSION_SECRET"]="v12.7-session-test-secret"
    os.environ["SCWB_STANDALONE_APP_URL"]="https://workbench.example.test"

def teardown_module():
    for k in ["SCWB_DEEP_LINK_SECRET","SCWB_SESSION_SECRET","SCWB_STANDALONE_APP_URL"]:
        os.environ.pop(k,None)

def test_status_and_config():
    d=client.get("/v1270/status").json()
    assert d["version"]=="12.7.0"
    assert d["wordpressRequired"] is False
    assert d["capabilities"]["signedDeepLinks"] is True
    c=client.get("/standalone/v1/launch/config").json()["launch"]
    assert c["standaloneAppUrl"]=="https://workbench.example.test"
    assert c["deepLinks"]["authenticationEmbedded"] is False

def test_create_and_validate_project_launch():
    d=client.post("/standalone/v1/launch",json={
      "route":"/workspace","targetType":"project","targetId":"project-123",
      "source":"wordpress","embed":True,"ttlSeconds":600,
      "context":{"origin":"homepage"}
    }).json()
    assert d["launchDescriptor"]["authenticationEmbedded"] is False
    assert d["launchUrl"].startswith("https://workbench.example.test/workspace?")
    token=parse_qs(urlparse(d["launchUrl"]).query)["launch"][0]
    v=client.post("/standalone/v1/launch/validate",json={"token":token}).json()
    assert v["valid"] is True
    assert v["launchDescriptor"]["targetId"]=="project-123"
    assert v["launchDescriptor"]["embed"] is True

def test_tampered_launch_rejected():
    d=client.post("/standalone/v1/launch",json={"route":"/calculator"}).json()
    token=d["launchToken"]
    bad=token[:-1]+("A" if token[-1]!="A" else "B")
    r=client.post("/standalone/v1/launch/validate",json={"token":bad})
    assert r.status_code==400

def test_invalid_target_contract():
    r=client.post("/standalone/v1/launch",json={
      "route":"/packages","targetType":"package"
    })
    assert r.status_code==422

def test_session_remains_separate():
    s=client.post("/standalone/v1/auth/session/anonymous",json={"ttlSeconds":600}).json()
    r=client.get("/standalone/v1/launch/session-check",headers={
      "Authorization":f"Bearer {s['token']}"
    })
    assert r.status_code==200
    assert r.json()["subject"]["type"]=="anonymous"

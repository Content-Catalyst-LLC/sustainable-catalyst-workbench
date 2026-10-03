import os
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def setup_module():
    os.environ["SCWB_SESSION_SECRET"]="v12.1-test-secret-that-is-long-enough-for-tests"

def teardown_module():
    os.environ.pop("SCWB_SESSION_SECRET",None)

def test_status_and_config():
    s=client.get("/v1210/status").json()
    assert s["version"]=="12.1.0"
    assert s["sessionAuthority"]=="FastAPI"
    assert s["wordpressRequired"] is False
    assert s["capabilities"]["signedBearerSessions"] is True

    c=client.get("/standalone/v1/auth/config").json()["auth"]
    assert c["sessionTransport"]=="authorization-bearer"
    assert c["sessionSigning"]["algorithm"]=="HMAC-SHA256"
    assert c["sessionSigning"]["productionSecretConfigured"] is True
    assert c["modes"]["wordpressUserIdentity"]["enabled"] is False

def test_create_verify_anonymous_session():
    created=client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":600,
        "clientLabel":"pytest"
    }).json()
    assert created["ok"] is True
    assert created["tokenType"]=="Bearer"
    assert created["session"]["subject"]["type"]=="anonymous"
    assert created["session"]["subject"]["authenticated"] is False
    token=created["token"]

    verified=client.post("/standalone/v1/auth/session/verify",json={"token":token}).json()
    assert verified["valid"] is True
    assert verified["session"]["sessionId"]==created["session"]["sessionId"]

def test_bearer_me_endpoint():
    created=client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":600
    }).json()
    token=created["token"]
    me=client.get(
        "/standalone/v1/auth/session/me",
        headers={"Authorization":f"Bearer {token}"}
    )
    assert me.status_code==200
    d=me.json()
    assert d["session"]["subject"]["id"]==created["session"]["subject"]["id"]

def test_refresh_preserves_subject_and_session_id():
    created=client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":600,
        "clientLabel":"refresh-test"
    }).json()
    refreshed=client.post("/standalone/v1/auth/session/refresh",json={
        "token":created["token"],
        "ttlSeconds":1200
    }).json()
    assert refreshed["session"]["sessionId"]==created["session"]["sessionId"]
    assert refreshed["session"]["subject"]["id"]==created["session"]["subject"]["id"]
    assert refreshed["session"]["sessionGeneration"]==2
    assert refreshed["refreshedFromGeneration"]==1

def test_tampered_token_rejected():
    created=client.post("/standalone/v1/auth/session/anonymous",json={
        "ttlSeconds":600
    }).json()
    token=created["token"]
    tampered=token[:-1] + ("A" if token[-1]!="A" else "B")
    response=client.post("/standalone/v1/auth/session/verify",json={"token":tampered})
    assert response.status_code==401

def test_missing_bearer_rejected():
    response=client.get("/standalone/v1/auth/session/me")
    assert response.status_code==401

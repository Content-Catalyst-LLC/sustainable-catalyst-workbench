import pytest
from fastapi import HTTPException
from app import erw_v121 as m

def test_status_standalone():
    s=m.status()
    assert s["identityAuthority"]=="sustainable-catalyst"
    assert s["wordpressRequired"] is False
    assert s["crossProductSSO"] is False
def test_configuration_gate(monkeypatch):
    monkeypatch.delenv("SCWB_SESSION_SECRET",raising=False)
    monkeypatch.delenv("SCWB_IDENTITY_ENROLLMENT_KEY",raising=False)
    with pytest.raises(HTTPException) as e:m.configured()
    assert e.value.status_code==503
def test_enrollment_login(tmp_path,monkeypatch):
    monkeypatch.setenv("SCWB_SESSION_SECRET","test-signing-secret-not-for-production-000000")
    monkeypatch.setenv("SCWB_IDENTITY_ENROLLMENT_KEY","test-invitation-key-not-for-production-0000")
    monkeypatch.setenv("SCWB_IDENTITY_DB_PATH",str(tmp_path/"identities.sqlite3"))
    req=m.Enroll(username="Researcher_1",password="correct horse battery stable!",enrollmentKey="test-invitation-key-not-for-production-0000")
    r=m.enroll(req)
    assert r["username"]=="researcher_1"
    with pytest.raises(HTTPException) as e:m.enroll(req)
    assert e.value.status_code==409
    with pytest.raises(HTTPException) as e:m.login(m.Login(username="Researcher_1",password="wrong"))
    assert e.value.status_code==401
    session=m.login(m.Login(username="Researcher_1",password=req.password))
    assert m.owner_from_auth("Bearer "+session["token"])==r["identityId"]
def test_reject_anonymous(monkeypatch):
    monkeypatch.setattr(m.v1210,"require_session",lambda a:{"subject":{"id":"anon:a","type":"anonymous","authenticated":False}})
    with pytest.raises(HTTPException) as e:m.owner_from_auth("Bearer x")
    assert e.value.status_code==403
def test_username_validation():
    with pytest.raises(HTTPException):m.username("../broken")
def test_onboarding_page():
    body=m.onboarding_ui().body.decode()
    assert "Create/open Wexford research project" in body
    assert "WordPress" in body
    assert "https://" not in body
def test_no_cdr():assert m.status()["publicationEnabled"] is False

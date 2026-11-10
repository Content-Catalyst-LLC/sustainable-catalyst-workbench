import pytest
from fastapi import HTTPException
from app.erw_v110 import status,projects_for,project_for,figures_for,figure,explorer
from app.erw_v010 import PROJECT_KEY

def test_status():assert status()["extensionVersion"]=="1.1.0"
def test_private_status():assert status()["signedSessionRequired"]
def test_no_publish():assert status()["publicationEnabled"] is False
def test_no_verified_cdr():assert status()["verifiedCDR"] is False
def test_projects_filter(monkeypatch):
    from app import erw_v110 as m
    monkeypatch.setattr(m,"list_projects",lambda owner:[
      {"id":"a","metadata":{"researchId":PROJECT_KEY}},
      {"id":"b","metadata":{"researchId":"other"}}])
    assert [p["id"] for p in projects_for("user")]==["a"]
def test_wrong_project_404(monkeypatch):
    from app import erw_v110 as m
    monkeypatch.setattr(m,"get_project",lambda pid,owner:{"metadata":{}})
    with pytest.raises(HTTPException) as e:project_for("a","owner")
    assert e.value.status_code==404
def test_only_supported_schemas(monkeypatch):
    from app import erw_v110 as m
    monkeypatch.setattr(m,"get_project",lambda pid,owner:{"id":pid,"metadata":{"researchId":PROJECT_KEY}})
    monkeypatch.setattr(m,"list_calculations",lambda pid,owner:[
       {"id":"v","title":"visual","calculationObject":{"schema":"sc.erw.visual-research-package.v0.6.0","calculationObjectHash":"x"}},
       {"id":"z","title":"other","calculationObject":{"schema":"other"}}])
    r=figures_for("a","owner")
    assert len(r)==1 and not r[0]["digestConsistent"]
def test_browser_page():assert "Export SVG" in explorer().body.decode()
def test_explorer_has_no_external_js():assert "https://" not in explorer().body.decode()
def test_browser_caution():assert "not verified atmospheric" in explorer().body.decode()

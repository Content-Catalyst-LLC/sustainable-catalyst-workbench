import pytest
from fastapi import HTTPException
from app import erw_v122 as m

def test_status_truth():
    s=m.status()
    assert s["noTokenCopyPaste"] is True
    assert s["crossProductSSO"] is False
    assert s["nativeDocxExport"] is False
def test_authenticated_ui():
    html=m.build_page()
    assert 'Sign in and open my projects' in html
    assert 'id="token"' not in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "window.location.hash" not in html
    assert "refreshDrafts()" in html
    assert 'Import existing manuscript text' in html
    assert "project()" in html
    assert 'Verified CDR' not in html
def test_owned_context(monkeypatch):
    monkeypatch.setattr(m,"owner_from_auth",lambda a:"sc:owned")
    monkeypatch.setattr(m,"projects_for",lambda owner:[{"id":"p1","metadata":{"onboardingKey":"wexford-erw-v121"}}] if owner=="sc:owned" else [])
    out=m.context_route("Bearer simulated")
    assert out["projects"][0]["id"]=="p1"
def test_draft_filtering(monkeypatch):
    monkeypatch.setattr(m,"owner_from_auth",lambda a:"sc:owned")
    monkeypatch.setattr(m,"catalog",lambda pid,owner:[
        {"id":"good","schema":m.REPORT,"digestConsistent":True},
        {"id":"bad","schema":m.REPORT,"digestConsistent":False},
        {"id":"table","schema":"sc.erw.research-table.v1.2.0","digestConsistent":True}])
    out=m.drafts_route("p1","Bearer simulated")
    assert [x["id"] for x in out["drafts"]]==["good"]
def test_rejects_unauthorized(monkeypatch):
    def reject(auth):raise HTTPException(403,"account required")
    monkeypatch.setattr(m,"owner_from_auth",reject)
    with pytest.raises(HTTPException) as exc:m.context_route(None)
    assert exc.value.status_code==403
def test_report_response():
    response=m.report_ui()
    assert response.status_code==200
    assert b"Authenticated Research Report Workspace" in response.body


def test_snapshot_menu_collapses_identical_hashes():
    from app.erw_v122 import _unique_snapshots
    from app.erw_v120 import REPORT
    record={"schema":REPORT,"digestConsistent":True,"title":"Wexford report","hash":"a"*64}
    rows=[{**record,"id":"old"},{**record,"id":"new"}]
    output=_unique_snapshots(rows)
    assert len(output)==1
    assert output[0]["id"]=="new"
    assert "aaaaaaaaaa" in output[0]["title"]


def test_saved_object_selector_excludes_report_snapshots():
    page=m.build_page()
    assert "catalog=d.objects.filter(x=>x.schema!=='sc.erw.report-workspace.v1.2.0')" in page
    assert "await refreshDrafts()" in page
    assert "Saved report snapshots" in page

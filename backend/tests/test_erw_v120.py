import pytest
from fastapi import HTTPException
from app import erw_v120 as m

def test_status():
    assert m.status()["extensionVersion"]=="1.2.0"
    assert m.status()["nativeDocxExport"] is False
def test_table_shape(monkeypatch):
    monkeypatch.setattr(m,"project_for",lambda p,o:{"id":p})
    r=m.TableRequest(title="Evidence",columns=["A","B"],rows=[["1","2"]])
    obj=m.make_table("p","user",r)
    assert obj["schema"]==m.TABLE and obj["verifiedCDR"] is False
def test_wrong_columns(monkeypatch):
    monkeypatch.setattr(m,"project_for",lambda p,o:{"id":p})
    with pytest.raises(HTTPException):
        m.make_table("p","owner",m.TableRequest(title="Evidence",columns=["A","B"],rows=[["a"]]))
def test_duplicate_columns(monkeypatch):
    monkeypatch.setattr(m,"project_for",lambda p,o:{"id":p})
    with pytest.raises(HTTPException):
        m.make_table("p","owner",m.TableRequest(title="Evidence",columns=["A","A"],rows=[["a","b"]]))
def test_report(monkeypatch):
    monkeypatch.setattr(m,"project_for",lambda p,o:{"id":p})
    req=m.ReportRequest(title="ERW Research Report",sections=[m.Section(id="intro",heading="Introduction",text="Text")])
    assert m.make_report("p","owner",req)["publicationEnabled"] is False
def test_insert_section_guard(monkeypatch):
    monkeypatch.setattr(m,"project_for",lambda p,o:{"id":p})
    with pytest.raises(HTTPException):
        m.make_report("p","owner",m.ReportRequest(title="ERW Research Report",
          sections=[m.Section(id="intro",heading="Introduction")],
          inserts=[m.Insert(sectionId="missing",kind="table",
            source=m.SourceRef(calculationId="s",objectHash="a"*64))]))
def test_browser(): assert "Save table as project object" in m.report_ui().body.decode()
def test_no_external_js():assert "https://" not in m.report_ui().body.decode()

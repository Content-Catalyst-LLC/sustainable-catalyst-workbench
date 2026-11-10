from io import BytesIO
from zipfile import ZipFile
import pytest
from fastapi import HTTPException
from app import erw_v134 as ui
from app import erw_v134_export as exp

REPORT={"title":"Hypothetical Wexford Research Report","authors":["Researcher"],
 "sections":[{"id":"abstract","heading":"Abstract","text":"Illustrative experimental design."}],
 "inserts":[],"bibliography":"Reviewed references only."}

def test_native_docx_file():
    content=exp.make_docx(REPORT,"p","owner")
    assert content[:2]==b"PK"
    with ZipFile(BytesIO(content)) as z:
        body=z.read("word/document.xml")
    assert b"Hypothetical Wexford" in body
    assert b"Illustrative experimental design." in body

def test_native_pdf_file():
    content=exp.make_pdf(REPORT,"p","owner")
    assert content.startswith(b"%PDF-")
    assert len(content)>1000

def test_unsupported_insert_source(monkeypatch):
    monkeypatch.setattr(exp,"valid_source",lambda *args:{"schema":"bogus"})
    with pytest.raises(HTTPException):exp.source_parts("p","owner",{"kind":"unknown","source":{"calculationId":"id","objectHash":"a"*64}})

def test_requires_owned_report(monkeypatch):
    monkeypatch.setattr(exp,"project_for",lambda p,o:None)
    monkeypatch.setattr(exp,"get_calculation",lambda i,o:{"projectId":"foreign"})
    with pytest.raises(HTTPException) as exc:exp.get_report("myproject","draft","owner")
    assert exc.value.status_code==404

def test_native_export_routes_and_page():
    page=ui.build_page()
    assert "download-docx" in page and "download-pdf" in page
    assert "report-drafts" in page
    assert ui.report_route().status_code==200
    assert exp.status()["verifiedCDR"] is False
    assert exp.status()["nativeDocxExport"] is True
    assert exp.status()["nativePdfExport"] is True

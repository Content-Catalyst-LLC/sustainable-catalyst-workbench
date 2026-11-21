import pytest
from fastapi import HTTPException
from app import erw_v135 as audit
from app import erw_v135_ui as ui

SAMPLE={"calculationObjectHash":"abc123","title":"Wexford report",
 "sections":[{"id":"abstract","heading":"Abstract","text":"Research report text"}],
 "inserts":[],"authors":["Researcher"],"bibliography":"A source bibliography"}

def test_audit_never_certifies_publication(monkeypatch):
    monkeypatch.setattr(audit,"get_report",lambda *a:SAMPLE)
    monkeypatch.setattr(audit,"list_evidence",lambda *a:[])
    monkeypatch.setattr(audit,"list_sources",lambda *a:[])
    r=audit.audit("project","report","owner")
    assert r["publicationCertified"] is False
    assert r["publicationEnabled"] is False
    assert r["verifiedCDR"] is False
    assert "evidence-coverage" in r["unresolvedGates"]
    assert "human-document-review" in r["unresolvedGates"]

def test_export_smoke_does_not_equal_certification(monkeypatch):
    monkeypatch.setattr(audit,"get_report",lambda *a:SAMPLE)
    monkeypatch.setattr(audit,"list_evidence",lambda *a:[{"sectionId":"abstract"}])
    monkeypatch.setattr(audit,"list_sources",lambda *a:[{"sourceId":"id"}])
    monkeypatch.setattr(audit,"make_docx",lambda *a:b"PK"+b"0"*800)
    monkeypatch.setattr(audit,"make_pdf",lambda *a:b"%PDF-"+b"0"*800)
    r=audit.audit("project","report","owner",render=True)
    assert all(r["rendered"].values())
    assert r["publicationCertified"] is False
    assert "pdf-page-text-verification" in r["unresolvedGates"]

def test_linked_source_failure_flags_gate(monkeypatch):
    report={**SAMPLE,"inserts":[{"sectionId":"abstract","kind":"figure"}]}
    monkeypatch.setattr(audit,"get_report",lambda *a:report)
    monkeypatch.setattr(audit,"list_evidence",lambda *a:[])
    monkeypatch.setattr(audit,"list_sources",lambda *a:[])
    monkeypatch.setattr(audit,"source_parts",lambda *a:(_ for _ in ()).throw(HTTPException(409,"source changed")))
    r=audit.audit("project","report","owner")
    assert "source-integrity" in r["unresolvedGates"]

def test_page_and_status():
    html=ui.build_page()
    assert "publication-audit" in html
    assert "audit-run" in html
    assert "render=true" in html
    assert ui.report_route().status_code==200
    assert audit.status()["publicationCertified"] is False

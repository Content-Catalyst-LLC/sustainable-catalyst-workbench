import pytest
from fastapi import HTTPException
from app import erw_v133 as ui
from app import erw_v133_evidence as m

def sample():
    return m.EvidenceRequest(sourceId="s"*36,sectionId="abstract",
       claim="Weathering may affect modeled capacity",
       pageReference="p. 8",excerpt="Researcher excerpt",
       evidenceClass="literature-derived",assessment="context")

def test_evidence_uses_pdf_source_hash(monkeypatch):
    monkeypatch.setattr(m,"project_for",lambda p,o:{"id":p})
    monkeypatch.setattr(m,"source_record",lambda s,p,o:{"sha256":"a"*64})
    obj=m.claim_record("project","owner",sample())
    assert obj["sourceSha256"]=="a"*64
    assert obj["pageTextExtracted"] is False
    assert obj["claimScientificallyVerified"] is False
    assert obj["verifiedCDR"] is False
    assert obj["calculationObjectHash"]

def test_cross_project_sources_rejected(monkeypatch):
    monkeypatch.setattr(m,"project_for",lambda p,o:{"id":p})
    def reject(*args):raise HTTPException(404,"Not in project")
    monkeypatch.setattr(m,"source_record",reject)
    with pytest.raises(HTTPException) as e:m.claim_record("other","owner",sample())
    assert e.value.status_code==404

def test_inspection_rejects_invalid_object(monkeypatch):
    monkeypatch.setattr(m,"owner_from_auth",lambda auth:"owner")
    monkeypatch.setattr(m,"project_for",lambda p,o:{"id":p})
    monkeypatch.setattr(m,"get_calculation",lambda i,o:{"projectId":"elsewhere","calculationObject":{}})
    with pytest.raises(HTTPException) as e:m.detail("p","e","Bearer x")
    assert e.value.status_code==404

def test_canvas_has_source_and_claim_review():
    page=ui.build_page()
    assert 'id="evidence-claim"' in page
    assert 'id="evidence-page"' in page
    assert 'id="evidence-checked"' in page
    assert "Machine verified: NO" in page
    assert "Upload source paper" in page

def test_release_truthfulness():
    assert m.status()["machinePdfTextInspection"] is False
    assert m.status()["claimVerification"] is False
    assert m.status()["publicationEnabled"] is False
    assert ui.report_route().status_code==200

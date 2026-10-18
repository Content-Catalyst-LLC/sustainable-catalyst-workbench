import pytest
from fastapi import HTTPException
from app import erw_v132 as ui
from app import erw_v132_sources as src

def test_harvard_requires_review():
    result=src.harvard(src.CitationFields(authors=["Smith, A."],year=2024,title="Research"))
    assert result["reference"] is None

def test_harvard_required_fields():
    result=src.harvard(src.CitationFields(verifiedByResearcher=True))
    assert result["reference"] is None and "Missing required" in result["warnings"][0]

def test_harvard_approved():
    fields=src.CitationFields(authors=["Smith, A.","Jones, B."],year=2024,title="A Study",
     journal="Journal of Research",volume="2",pages="14-20",doi="10.1234/test",verifiedByResearcher=True)
    result=src.harvard(fields)
    assert "(Smith, A. and Jones, B., 2024)"==result["inText"]
    assert "https://doi.org/10.1234/test" in result["reference"]

def test_pdf_bounds():
    with pytest.raises(HTTPException):src.validate_pdf(b"invalid")
    with pytest.raises(HTTPException):src.validate_pdf(b"%PDF-1.7 only start")
    assert len(src.validate_pdf(b"%PDF-1.4\nbody\n%%EOF"))==64

def test_ownership_guard(monkeypatch):
    monkeypatch.setattr(src,"project_for",lambda project_id,owner:None)
    monkeypatch.setattr(src,"get_calculation",lambda source_id,owner:{"projectId":"another","calculationObject":{}})
    with pytest.raises(HTTPException) as exc:src.source_record("s","p","owner")
    assert exc.value.status_code==404

def test_canvas():
    page=ui.build_page()
    assert 'id="pdfupload"' in page
    assert 'id="citeauthors"' in page
    assert 'id="citereviewed"' in page
    assert 'id="citeinsert"' in page
    assert 'Signed Workbench session token' not in page

def test_status_truth():
    s=ui.status()
    assert s["pdfSourceUpload"] is True
    assert s["externalMetadataVerification"] is False
    assert s["nativeDocxExport"] is False
    assert s["verifiedCDR"] is False

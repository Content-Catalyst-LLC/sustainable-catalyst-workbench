import io
import zipfile
import pytest
from fastapi import HTTPException
from app import erw_v131 as ui
from app import erw_v131_import as imp

def sample_docx():
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("word/document.xml",'''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body><w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Abstract</w:t></w:r></w:p>
<w:p><w:r><w:t>Evidence-based manuscript paragraph.</w:t></w:r></w:p></w:body></w:document>''')
    return b.getvalue()

def test_extract_word_paragraphs():
    sections,count=imp.extract_docx(sample_docx())
    assert count==2
    assert sections[0]["heading"]=="Abstract"
    assert "Evidence-based" in sections[0]["text"]

def test_reject_invalid_document():
    with pytest.raises(HTTPException) as e:imp.extract_docx(b"not a word file")
    assert e.value.status_code==422

def test_reject_legacy_doc():
    with pytest.raises(HTTPException):imp.safe_filename("../manuscript.doc")
    assert imp.safe_filename("../../Manuscript.docx")=="Manuscript.docx"

def test_browser_canvas_assembly():
    html=ui.build_page()
    assert 'id="wordfile"' in html
    assert 'id="uploadword"' in html
    assert "scFigureHtml(insert)" in html
    assert "Saved report snapshots" in html
    assert "sourceId" not in html or "DOCX" in html

def test_release_status_is_precise():
    s=ui.status()
    assert s["completedDocxUpload"]
    assert s["sourceBasedSvgFigures"]
    assert not s["nativeDocxExport"]
    assert not s["nativePdfExport"]
    assert not s["verifiedCDR"]
    assert not s["publicationEnabled"]

def test_page_route():
    assert ui.report_route().status_code==200

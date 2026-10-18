from app import erw_v130 as m

def test_build_canvas():
    page=m.canvas_page()
    assert 'Scientific document canvas' in page
    assert 'id="document-outline"' in page
    assert 'id="readmode"' in page
    assert 'id="editmode"' in page
    assert 'Signed Workbench session token' not in page
    assert 'Sign in and open my projects' in page
    assert 'Save draft snapshot' in page
    assert '<style id="sc-document-canvas-theme">' in page
    assert page.rfind('id="sc-canvas-controls"') > page.find('id="document-outline"')
    assert page.rstrip().endswith('</html>')

def test_scientific_limitations():
    s=m.status()
    assert s["nativeDocxExport"] is False
    assert s["nativePdfExport"] is False
    assert s["pdfSourceUpload"] is False
    assert s["publicationEnabled"] is False
    assert s["verifiedCDR"] is False

def test_route():
    result=m.report_route()
    assert result.status_code==200
    assert b'Document preview' in result.body

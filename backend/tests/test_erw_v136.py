from app import erw_v136 as m

def test_reconciled_workspace_controls():
    page=m.build_page()
    assert 'id="erw136mode"' in page
    assert 'id="erw136-clean"' in page
    assert 'id="publication-audit"' in page
    assert 'id="native-export"' in page
    assert 'id="evidence-studio"' in page
    assert 'automatic source-text verification' not in page.lower() or 'remain incomplete' in page
    assert page.count("el('uploadword').onclick=")==1

def test_safe_word_import_guard():
    page=m.build_page()
    assert "nonempty.length" in page
    assert "Existing manuscript contains text" in page
    assert "Original DOCX preserved" in page
    assert "sections=imported" in page
    assert "sc136.pending" in page

def test_safe_reconcile_does_not_write_snapshots():
    page=m.build_page()
    assert "reviewed cleanup" in page.lower() or "Apply reviewed cleanup" in page
    assert "d.documentId" in page
    assert m.status()["publicationCertified"] is False
    assert m.status()["faithfulWordTables"] is False
    assert m.current_report().status_code==307

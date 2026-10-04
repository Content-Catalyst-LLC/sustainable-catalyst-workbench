from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release():
    assert 'APP_VERSION = "12.5.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="12.5.0"' in m
    assert "from app.v1250 import router as v1250_router" in m

def test_routes():
    p=(ROOT/"backend/app/v1250.py").read_text()
    assert "/standalone/v1/notebooks" in p
    assert "/history" in p
    assert "/timeline" in p
    assert "calculation-reference" in p

def test_client():
    p=(ROOT/"standalone-client/notebook-history.js").read_text()
    assert "StandaloneNotebookHistoryClient" in p
    assert "createNotebook" in p
    assert "projectHistory" in p
    assert "projectTimeline" in p

def test_app():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    assert '"/history"' in p
    assert "loadHistory" in p
    assert "createNotebook" in p
    assert "notebook-history" in p

def test_wordpress():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1250-notebook-calculation-history.php").read_text()
    assert "wordpressRequired = false" in p
    assert "WordPress does not own notebook or history persistence" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.5.0" in c
    assert "d.get('version')=='12.5.0'" in c

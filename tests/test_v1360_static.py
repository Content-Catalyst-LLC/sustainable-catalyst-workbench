import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_router():
    assert 'APP_VERSION = "13.6.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert '# Static release identity marker: version="13.6.0"' in m
    assert "from app.v1360 import router as v1360_router" in m

def test_backend_contract():
    p=(ROOT/"backend/app/v1360.py").read_text()
    for x in ["structured-notes","/attach","research-timeline","history-export",
              "graphAttachments","packageAttachments","timelineHashes"]:
        assert x in p

def test_frontend_timeline():
    s=(ROOT/"standalone-app/app-shell.js").read_text()
    for x in ["researchTimeline","loadResearchTimeline","Notebook & Research Timeline",
              "timeline-scope","timeline-filter","addNotebookNote","attachSelectedObject"]:
        assert x in s

def test_manifest():
    d=json.loads((ROOT/"standalone-app/version.json").read_text())
    assert d["version"]=="13.6.0"
    assert d["interface"]=="notebook-history-research-timeline-workspace"

def test_client():
    p=(ROOT/"standalone-client/research-timeline.js").read_text()
    assert "ResearchTimelineClient" in p
    assert "notebookEntries" in p
    assert "attach" in p

def test_wp_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "Version: 13.6.0" in p
    assert "scwb-v1360-notebook-history-research-timeline.php" in p

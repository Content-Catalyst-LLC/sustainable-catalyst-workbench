import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity_and_router():
    assert 'APP_VERSION = "13.4.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert '# Static release identity marker: version="13.4.0"' in m
    assert "from app.v1340 import router as v1340_router" in m
    assert "app.include_router(v1340_router)" in m

def test_backend_session_contract():
    p=(ROOT/"backend/app/v1340.py").read_text()
    for x in [
        "scwb_research_sessions","scwb_research_session_activity",
        "/standalone/v1/research-sessions",
        "/summary","/activity","projectWorkspaceReady"
    ]:
        assert x in p

def test_frontend_workspace_integration():
    s=(ROOT/"standalone-app/app-shell.js").read_text()
    for x in [
        "researchSessions","researchSessionId","loadResearchSessions",
        "createResearchSession","activateResearchSession",
        "research-session-select","Project Workspace"
    ]:
        assert x in s

def test_version_manifest():
    d=json.loads((ROOT/"standalone-app/version.json").read_text())
    assert d["version"]=="13.4.0"
    assert d["interface"]=="project-workspace-persistent-research-sessions"

def test_client_adapter():
    p=(ROOT/"standalone-client/research-sessions.js").read_text()
    assert "ResearchSessionsClient" in p
    assert "appendActivity" in p
    assert "summary" in p

def test_wordpress_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "Version: 13.4.0" in p
    assert "scwb-v1340-project-workspace-research-sessions.php" in p

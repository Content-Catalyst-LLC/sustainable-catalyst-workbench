from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "12.2.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="12.2.0"' in m
    assert "from app.v1220 import router as v1220_router" in m
    assert "app.include_router(v1220_router)" in m

def test_store_routes():
    p=(ROOT/"backend/app/v1220.py").read_text()
    assert "/standalone/v1/projects" in p
    assert "/standalone/v1/calculations" in p
    assert "sqliteWalPersistence" in p
    assert "sessionSubjectOwnership" in p
    assert "PRAGMA journal_mode=WAL" in p

def test_standalone_client():
    p=(ROOT/"standalone-client/project-store.js").read_text()
    assert "StandaloneProjectStoreClient" in p
    assert "createProject" in p
    assert "saveCalculation" in p
    assert "listCalculations" in p

def test_app_shell_workspace_enabled():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    assert "loadProjects" in p
    assert "createProject" in p
    assert "workspace-projects" in p
    assert 'sessionStorage.getItem("scwb.session.token")' in p

def test_wordpress_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1220-persistent-calculation-project-store.php").read_text()
    assert "wordpressRequired = false" in p
    assert "WordPress is not the persistence authority" in p
    assert "/standalone/v1/store/status" in p

def test_compose_persistence():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.2.0" in c
    assert "d.get('version')=='12.2.0'" in c
    assert "SCWB_PROJECT_STORE_PATH" in c
    assert "./data:/data" in c

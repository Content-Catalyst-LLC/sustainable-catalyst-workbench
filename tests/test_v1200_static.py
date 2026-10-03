from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "12.0.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="12.0.0"' in m
    assert "from app.v1200 import router as v1200_router" in m
    assert "app.include_router(v1200_router)" in m

def test_backend_shell_routes():
    p=(ROOT/"backend/app/v1200.py").read_text()
    assert "/standalone/v1/app-manifest" in p
    assert "/standalone/v1/app-routes" in p
    assert "/standalone/v1/app-shell" in p
    assert '"standalone-primary"' in p

def test_standalone_app_files():
    for rel in ["index.html","app-shell.js","app-shell.css","config.js"]:
        assert (ROOT/"standalone-app"/rel).exists()
    h=(ROOT/"standalone-app/index.html").read_text()
    assert 'id="sc-workbench-app"' in h
    assert "app-shell.js" in h

def test_wordpress_optional_adapter():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1200-standalone-application-shell.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/standalone/v1/app-manifest" in p
    assert "Authoritative application shell is standalone" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.0.0" in c
    assert "d.get('version')=='12.0.0'" in c

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_release_identity_v10101():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert 'APP_VERSION = "10.10.1"' in release
    assert 'version="10.10.1"' in main
    assert "from app.v10101 import router as v10101_router" in main
    assert "app.include_router(v10101_router)" in main
    assert "Version: 10.10.1" in plugin
    assert "SCWB_VERSION', '10.10.1" in plugin

def test_wordpress_v10101_is_adapter_only():
    p = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v10101-wordpress-dependency-routing-isolation.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/decoupling/dependencies" in p
    assert "/decoupling/routes" in p
    assert "/v10101/status" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_compose_tracks_current_release():
    c = (ROOT / "compose.yml").read_text()
    assert "sustainable-catalyst-workbench:10.10.1" in c
    assert "d.get('version')=='10.10.1'" in c

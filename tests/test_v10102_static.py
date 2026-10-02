from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_v10102():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert 'APP_VERSION = "10.10.2"' in release
    assert 'version="10.10.2"' in main
    assert "from app.v10102 import router as v10102_router" in main
    assert "app.include_router(v10102_router)" in main
    assert "Version: 10.10.2" in plugin
    assert "SCWB_VERSION', '10.10.2" in plugin


def test_standalone_contract_markers():
    p = (ROOT / "backend/app/v10102.py").read_text()
    assert '"/standalone/v1/health"' in p
    assert '"/standalone/v1/bootstrap"' in p
    assert '"/standalone/v1/api-contract"' in p
    assert '"/standalone/v1/compatibility"' in p
    assert '"wordpressRequired": False' in p
    assert '"wordpressNonceRequired": False' in p


def test_wordpress_is_optional_proxy_only():
    p = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v10102-standalone-runtime-contract-stabilization.php").read_text()
    assert "wordpressRequired = false" in p
    assert "Authoritative computation remains in FastAPI" in p
    assert "/standalone/v1/bootstrap" in p
    assert "/standalone/v1/api-contract" in p


def test_compose_tracks_current_release():
    c = (ROOT / "compose.yml").read_text()
    assert "sustainable-catalyst-workbench:10.10.2" in c
    assert "d.get('version')=='10.10.2'" in c

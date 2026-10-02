from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_v10120():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()

    assert 'APP_VERSION = "10.12.0"' in release
    assert 'version="10.12.0"' in main
    assert "from app.v10120 import router as v10120_router" in main
    assert "app.include_router(v10120_router)" in main
    assert "Version: 10.12.0" in plugin
    assert "SCWB_VERSION', '10.12.0" in plugin


def test_production_certification_routes_exist():
    p = (ROOT / "backend/app/v10120.py").read_text()
    assert "/certification/v10" in p
    assert "/certification/v10/releases" in p
    assert "/certification/v10/contracts" in p
    assert "/certification/v10/probe" in p
    assert "v11 Universal Calculation Engine" in p


def test_wordpress_adapter_is_proxy_only():
    p = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v10120-production-certification-v10-consolidation.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/certification/v10" in p
    assert "Authoritative computation remains in FastAPI" in p


def test_standalone_certification_helper_exists():
    p = (ROOT / "standalone-client/certify-v10-production.js").read_text()
    assert "certifyWorkbenchV10Production" in p
    assert "/certification/v10" in p
    assert "/certification/v10/probe" in p
    assert "wp_rest" not in p


def test_compose_tracks_current_release():
    c = (ROOT / "compose.yml").read_text()
    assert "sustainable-catalyst-workbench:10.12.0" in c
    assert "d.get('version')=='10.12.0'" in c

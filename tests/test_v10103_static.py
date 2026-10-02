from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_v10103():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert 'APP_VERSION = "10.10.3"' in release
    assert 'version="10.10.3"' in main
    assert "from app.v10103 import router as v10103_router" in main
    assert "app.include_router(v10103_router)" in main
    assert "Version: 10.10.3" in plugin
    assert "SCWB_VERSION', '10.10.3" in plugin


def test_client_adapter_module_exists():
    client = (ROOT / "standalone-client/workbench-api.js").read_text()
    assert "class SustainableCatalystWorkbenchAPI" in client
    assert "/standalone/v1/client/config" in client
    assert "/standalone/v1/client/compute" in client
    assert "X-Request-ID" in client
    assert "wpApiSettings" not in client
    assert "wp_rest" not in client


def test_wordpress_adapter_is_proxy_only():
    p = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v10103-standalone-client-api-adapter.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/standalone/v1/client/config" in p
    assert "/standalone/v1/client/compute" in p
    assert "Authoritative computation remains in FastAPI" in p


def test_compose_tracks_current_release():
    c = (ROOT / "compose.yml").read_text()
    assert "sustainable-catalyst-workbench:10.10.3" in c
    assert "d.get('version')=='10.10.3'" in c

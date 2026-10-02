from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_v10104():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()

    assert 'APP_VERSION = "10.10.4"' in release
    assert 'version="10.10.4"' in main
    assert "from app.v10104 import router as v10104_router" in main
    assert "app.include_router(v10104_router)" in main
    assert "Version: 10.10.4" in plugin
    assert "SCWB_VERSION', '10.10.4" in plugin


def test_certification_module_is_backend_owned():
    p = (ROOT / "backend/app/v10104.py").read_text()
    assert "/certification/dual-mode" in p
    assert "wordpressRequired" in p
    assert "canonicalRuntime" in p
    assert "FastAPI" in p


def test_wordpress_certification_adapter_is_proxy_only():
    p = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v10104-dual-mode-certification.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/certification/dual-mode" in p
    assert "Authoritative computation remains in FastAPI" in p


def test_standalone_certification_helper_exists():
    p = (ROOT / "standalone-client/certify-dual-mode.js").read_text()
    assert "certifyWorkbenchDualMode" in p
    assert "/certification/dual-mode" in p
    assert "/standalone/v1/client/config" in p
    assert "wp_rest" not in p


def test_compose_tracks_current_release():
    c = (ROOT / "compose.yml").read_text()
    assert "sustainable-catalyst-workbench:10.10.4" in c
    assert "d.get('version')=='10.10.4'" in c

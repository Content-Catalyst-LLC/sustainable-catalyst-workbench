from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_v10110():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()

    assert 'APP_VERSION = "10.11.0"' in release
    assert 'version="10.11.0"' in main
    assert "from app.v10110 import router as v10110_router" in main
    assert "app.include_router(v10110_router)" in main
    assert "Version: 10.11.0" in plugin
    assert "SCWB_VERSION', '10.11.0" in plugin


def test_package_module_contains_portable_replay_contract():
    p = (ROOT / "backend/app/v10110.py").read_text()
    assert "/computational-packages/build" in p
    assert "/computational-packages/replay" in p
    assert "/computational-packages/verify" in p
    assert "packageHash" in p
    assert "manifestHash" in p
    assert "environmentHash" in p
    assert "wordpressRequired" in p


def test_standalone_package_helper_exists():
    p = (ROOT / "standalone-client/reproducible-package.js").read_text()
    assert "buildComputationalPackage" in p
    assert "verifyComputationalPackage" in p
    assert "replayComputationalPackage" in p
    assert "/computational-packages/build" in p
    assert "wp_rest" not in p


def test_wordpress_adapter_is_proxy_only():
    p = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v10110-reproducible-computational-package.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/computational-packages/" in p
    assert "array('build', 'replay', 'verify')" in p
    assert "Authoritative computation remains in FastAPI" in p


def test_compose_tracks_current_release():
    c = (ROOT / "compose.yml").read_text()
    assert "sustainable-catalyst-workbench:10.11.0" in c
    assert "d.get('version')=='10.11.0'" in c

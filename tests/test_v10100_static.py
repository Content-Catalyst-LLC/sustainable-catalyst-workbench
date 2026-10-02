from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_release_identity():
    assert 'APP_VERSION = "10.10.0"' in (ROOT/"backend/app/release.py").read_text()
    assert 'version="10.10.0"' in (ROOT/"backend/app/main.py").read_text()
    plugin=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "Version: 10.10.0" in plugin
    assert "define('SCWB_VERSION', '10.10.0')" in plugin


def test_router_wired():
    main=(ROOT/"backend/app/main.py").read_text()
    assert "from app.v10100 import router as v10100_router" in main
    assert "app.include_router(v10100_router)" in main


def test_wordpress_is_adapter_not_runtime():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v10100-hybrid-numerical-runtime.php").read_text()
    assert "/numerical/compute" in p
    assert "/standalone/bootstrap" in p
    assert "wordpressRequired" in p

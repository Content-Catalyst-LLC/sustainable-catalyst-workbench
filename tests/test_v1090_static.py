from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "10.9.0"' in (ROOT/"backend/app/release.py").read_text()
    assert 'version="10.9.0"' in (ROOT/"backend/app/main.py").read_text()
    plugin=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "Version: 10.9.0" in plugin
    assert "define('SCWB_VERSION', '10.9.0')" in plugin

def test_router_wired():
    main=(ROOT/"backend/app/main.py").read_text()
    assert "from app.v1090 import router as v1090_router" in main
    assert "app.include_router(v1090_router)" in main

def test_wordpress_module_wired():
    plugin=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert "scwb-v1090-agent-computational-graph-workspace.php" in plugin

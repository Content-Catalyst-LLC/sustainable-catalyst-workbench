from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release():
    assert 'APP_VERSION = "12.6.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="12.6.0"' in m
    assert "from app.v1260 import router as v1260_router" in m

def test_backend():
    p=(ROOT/"backend/app/v1260.py").read_text()
    assert "/standalone/v1/reproducibility/packages" in p
    assert "capture_replay" in p
    assert "ReplayEnvelope" in p
    assert "deterministicReplay" in p

def test_client():
    p=(ROOT/"standalone-client/reproducibility-browser.js").read_text()
    assert "StandaloneReproducibilityBrowserClient" in p
    assert "createPackage" in p
    assert "verifyPackage" in p
    assert "replayPackage" in p

def test_app():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    assert '"/packages"' in p
    assert "loadPackages" in p
    assert "verifyPackage" in p
    assert "replayPackage" in p
    assert "reproducibility-packages" in p

def test_wordpress():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1260-reproducibility-package-browser.php").read_text()
    assert "wordpressRequired = false" in p
    assert "WordPress does not own reproducibility package state" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.6.0" in c
    assert "d.get('version')=='12.6.0'" in c

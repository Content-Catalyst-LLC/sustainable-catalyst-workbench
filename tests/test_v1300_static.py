from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_and_router():
    assert 'APP_VERSION = "13.0.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="13.0.0"' in m
    assert "from app.v1300 import router as v1300_router" in m
    assert "app.include_router(v1300_router)" in m

def test_functional_shell():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    for term in [
        "/standalone/v1/projects",
        "/standalone/v1/calculator/execute",
        "/standalone/v1/renderer/view-spec",
        "/standalone/v1/notebooks",
        "/history",
        "/reproducibility/packages",
        "/standalone/v1/launch/validate",
    ]: assert term in p

def test_real_interface_controls():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    for term in ["Create Notebook","Execute","Render graph","Capture last calculation","Saved calculations"]:
        assert term in p

def test_no_wordpress_dependency():
    p=(ROOT/"backend/app/v1300.py").read_text()
    assert '"wordpressRequired": False' in p
    assert '"canonicalBackend": "FastAPI"' in p

def test_config():
    assert 'version:"13.0.0"' in (ROOT/"standalone-app/config.js").read_text()

def test_functional_client():
    p=(ROOT/"standalone-client/functional-interface.js").read_text()
    assert "FunctionalStandaloneInterfaceClient" in p
    assert "/standalone/v1/interface/readiness" in p

from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "11.13.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="11.13.0"' in m
    assert "from app.v11130 import router as v11130_router" in m
    assert "app.include_router(v11130_router)" in m

def test_routes():
    p=(ROOT/"backend/app/v11130.py").read_text()
    assert "/calculation-engine/v1/discrete-math" in p
    assert "chineseRemainderTheorem" in p
    assert "shortestPathBfs" in p

def test_wordpress():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v11130-number-theory-discrete-mathematics.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/discrete-math" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone():
    p=(ROOT/"standalone-client/discrete-math-engine.js").read_text()
    assert "discreteMath" in p
    assert "discreteMathCalculationObject" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.13.0" in c
    assert "d.get('version')=='11.13.0'" in c

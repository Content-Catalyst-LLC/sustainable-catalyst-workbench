from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "11.10.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="11.10.0"' in m
    assert "from app.v11100 import router as v11100_router" in m
    assert "app.include_router(v11100_router)" in m

def test_routes_and_capabilities():
    p=(ROOT/"backend/app/v11100.py").read_text()
    assert "/calculation-engine/v1/optimization" in p
    assert "mixedIntegerLinearProgramming" in p
    assert "constraintFeasibilityDiagnostics" in p

def test_wordpress_adapter():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v11100-optimization-mathematical-programming.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/optimization" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone_client():
    p=(ROOT/"standalone-client/optimization-engine.js").read_text()
    assert "optimization" in p
    assert "optimizationCalculationObject" in p
    assert "/calculation-engine/v1/optimization" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.10.0" in c
    assert "d.get('version')=='11.10.0'" in c

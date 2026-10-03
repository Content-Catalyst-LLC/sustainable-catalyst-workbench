from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "11.15.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="11.15.0"' in m
    assert "from app.v11150 import router as v11150_router" in m
    assert "app.include_router(v11150_router)" in m

def test_routes():
    p=(ROOT/"backend/app/v11150.py").read_text()
    assert "/calculation-engine/v1/uncertainty" in p
    assert "covarianceAwarePropagation" in p
    assert "monteCarloConvergenceDiagnostics" in p

def test_wordpress():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v11150-uncertainty-propagation-monte-carlo.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/uncertainty" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone():
    p=(ROOT/"standalone-client/uncertainty-engine.js").read_text()
    assert "uncertaintyAnalysis" in p
    assert "uncertaintyCalculationObject" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.15.0" in c
    assert "d.get('version')=='11.15.0'" in c

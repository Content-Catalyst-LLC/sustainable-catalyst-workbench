from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "11.14.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="11.14.0"' in m
    assert "from app.v11140 import router as v11140_router" in m
    assert "app.include_router(v11140_router)" in m

def test_routes():
    p=(ROOT/"backend/app/v11140.py").read_text()
    assert "/calculation-engine/v1/complex-analysis" in p
    assert "highPrecisionSpecialFunctions" in p
    assert "circularContourIntegration" in p

def test_wordpress():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v11140-complex-analysis-special-functions.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/complex-analysis" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone():
    p=(ROOT/"standalone-client/complex-analysis.js").read_text()
    assert "complexAnalysis" in p
    assert "complexAnalysisCalculationObject" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.14.0" in c
    assert "d.get('version')=='11.14.0'" in c

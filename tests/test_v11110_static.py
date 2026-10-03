from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "11.11.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="11.11.0"' in m
    assert "from app.v11110 import router as v11110_router" in m
    assert "app.include_router(v11110_router)" in m

def test_routes():
    p=(ROOT/"backend/app/v11110.py").read_text()
    assert "/calculation-engine/v1/numerical-analysis" in p
    assert "convergenceOrderEstimation" in p
    assert "conditioningAnalysis" in p

def test_wordpress():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v11110-numerical-analysis-laboratory.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/numerical-analysis" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone():
    p=(ROOT/"standalone-client/numerical-analysis.js").read_text()
    assert "numericalAnalysis" in p
    assert "numericalAnalysisCalculationObject" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.11.0" in c
    assert "d.get('version')=='11.11.0'" in c

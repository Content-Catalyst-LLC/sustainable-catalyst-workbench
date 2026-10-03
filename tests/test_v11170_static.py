from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "11.17.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="11.17.0"' in m
    assert "from app.v11170 import router as v11170_router" in m
    assert "app.include_router(v11170_router)" in m

def test_routes():
    p=(ROOT/"backend/app/v11170.py").read_text()
    assert "/calculation-engine/v1/reproducibility/capture" in p
    assert "/calculation-engine/v1/reproducibility/replay" in p
    assert "/calculation-engine/v1/reproducibility/compare" in p
    assert "structuredDivergenceReporting" in p

def test_wordpress():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v11170-calculation-provenance-replay-reproducibility.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/reproducibility/" in p
    assert "array('capture','replay','compare','calculation-object')" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone():
    p=(ROOT/"standalone-client/reproducibility.js").read_text()
    assert "captureReplayEnvelope" in p
    assert "replayCalculation" in p
    assert "compareCalculationObjects" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.17.0" in c
    assert "d.get('version')=='11.17.0'" in c

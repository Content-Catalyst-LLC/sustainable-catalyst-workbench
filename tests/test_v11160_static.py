from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "11.16.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="11.16.0"' in m
    assert "from app.v11160 import router as v11160_router" in m
    assert "app.include_router(v11160_router)" in m

def test_routes():
    p=(ROOT/"backend/app/v11160.py").read_text()
    assert "/calculation-engine/v1/graphing" in p
    assert "rendererNeutralViewSpec" in p
    assert "calculationObjectVisualizations" in p

def test_wordpress():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v11160-interactive-graphing-linked-views.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/graphing" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone():
    p=(ROOT/"standalone-client/mathematical-views.js").read_text()
    assert "mathematicalViews" in p
    assert "mathematicalViewsCalculationObject" in p
    assert "linkGroup" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.16.0" in c
    assert "d.get('version')=='11.16.0'" in c

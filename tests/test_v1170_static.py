from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_release_identity_v1170():
    release=(ROOT/"backend/app/release.py").read_text()
    main=(ROOT/"backend/app/main.py").read_text()
    plugin=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert 'APP_VERSION = "11.7.0"' in release
    assert 'version="11.7.0"' in main
    assert "from app.v1170 import router as v1170_router" in main
    assert "app.include_router(v1170_router)" in main
    assert "Version: 11.7.0" in plugin
    assert "SCWB_VERSION', '11.7.0" in plugin

def test_quantity_routes_exist():
    p=(ROOT/"backend/app/v1170.py").read_text()
    assert "/calculation-engine/v1/quantities" in p
    assert "/calculation-engine/v1/quantities/calculation-object" in p
    assert "dimensionConsistencyChecks" in p
    assert "derivedQuantities" in p

def test_wordpress_adapter_proxy_only():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1170-units-dimensions-physical-quantities.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/quantities" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone_quantity_client_exists():
    p=(ROOT/"standalone-client/physical-quantities.js").read_text()
    assert "physicalQuantity" in p
    assert "/calculation-engine/v1/quantities" in p
    assert "physicalQuantityCalculationObject" in p
    assert "wp_rest" not in p

def test_compose_tracks_current_release():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.7.0" in c
    assert "d.get('version')=='11.7.0'" in c

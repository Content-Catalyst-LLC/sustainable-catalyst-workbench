from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_v1100():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()

    assert 'APP_VERSION = "11.0.0"' in release
    assert 'version="11.0.0"' in main
    assert "from app.v1100 import router as v1100_router" in main
    assert "app.include_router(v1100_router)" in main
    assert "Version: 11.0.0" in plugin
    assert "SCWB_VERSION', '11.0.0" in plugin


def test_unified_calculation_engine_contract():
    p = (ROOT / "backend/app/v1100.py").read_text()
    assert "sc-workbench-calculation-object/1.0" in p
    assert "/calculation-engine/v1/schema" in p
    assert "/calculation-engine/v1/normalize" in p
    assert "/calculation-engine/v1/plan" in p
    assert "/calculation-engine/v1/compute" in p
    assert "calculationObjectHash" in p


def test_wordpress_adapter_is_proxy_only():
    p = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1100-unified-calculation-engine.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/" in p
    assert "Authoritative computation remains in FastAPI" in p


def test_standalone_calculation_client_exists():
    p = (ROOT / "standalone-client/calculation-engine.js").read_text()
    assert "computeCalculationObject" in p
    assert "/calculation-engine/v1/compute" in p
    assert "/calculation-engine/v1/plan" in p
    assert "wp_rest" not in p


def test_compose_tracks_current_release():
    c = (ROOT / "compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.0.0" in c
    assert "d.get('version')=='11.0.0'" in c

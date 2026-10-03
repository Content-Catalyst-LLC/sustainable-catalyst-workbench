from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_release_identity_v1180():
    release=(ROOT/"backend/app/release.py").read_text()
    main=(ROOT/"backend/app/main.py").read_text()
    plugin=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert 'APP_VERSION = "11.8.0"' in release
    assert 'version="11.8.0"' in main
    assert "from app.v1180 import router as v1180_router" in main
    assert "app.include_router(v1180_router)" in main
    assert "Version: 11.8.0" in plugin
    assert "SCWB_VERSION', '11.8.0" in plugin

def test_statistics_routes_exist():
    p=(ROOT/"backend/app/v1180.py").read_text()
    assert "/calculation-engine/v1/statistics" in p
    assert "/calculation-engine/v1/statistics/calculation-object" in p
    assert "deterministicRandomSampling" in p
    assert "linearRegression" in p

def test_wordpress_adapter_proxy_only():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1180-probability-statistics-engine.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/statistics" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone_statistics_client_exists():
    p=(ROOT/"standalone-client/probability-statistics.js").read_text()
    assert "probabilityStatistics" in p
    assert "/calculation-engine/v1/statistics" in p
    assert "probabilityStatisticsCalculationObject" in p
    assert "wp_rest" not in p

def test_compose_tracks_current_release():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.8.0" in c
    assert "d.get('version')=='11.8.0'" in c

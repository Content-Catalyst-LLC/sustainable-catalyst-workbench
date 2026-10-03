from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity_v1160():
    release=(ROOT/"backend/app/release.py").read_text()
    main=(ROOT/"backend/app/main.py").read_text()
    plugin=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()
    assert 'APP_VERSION = "11.6.0"' in release
    assert 'version="11.6.0"' in main
    assert "from app.v1160 import router as v1160_router" in main
    assert "app.include_router(v1160_router)" in main
    assert "Version: 11.6.0" in plugin
    assert "SCWB_VERSION', '11.6.0" in plugin

def test_dynamics_routes_and_julia_runner():
    p=(ROOT/"backend/app/v1160.py").read_text()
    assert "/calculation-engine/v1/dynamics" in p
    assert "/calculation-engine/v1/dynamics/calculation-object" in p
    assert "localStabilityAnalysis" in p
    assert (ROOT/"backend/julia-runtime/dynamics_runner.jl").exists()

def test_wordpress_adapter_proxy_only():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1160-differential-equations-dynamical-systems.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/dynamics" in p
    assert "Authoritative computation remains in FastAPI" in p

def test_standalone_client_exists():
    p=(ROOT/"standalone-client/dynamics-engine.js").read_text()
    assert "dynamics" in p
    assert "/calculation-engine/v1/dynamics" in p
    assert "dynamicsCalculationObject" in p
    assert "wp_rest" not in p

def test_compose_current_release():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.6.0" in c
    assert "d.get('version')=='11.6.0'" in c

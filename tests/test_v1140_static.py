from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_v1140():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()

    assert 'APP_VERSION = "11.4.0"' in release
    assert 'version="11.4.0"' in main
    assert "from app.v1140 import router as v1140_router" in main
    assert "app.include_router(v1140_router)" in main
    assert "Version: 11.4.0" in plugin
    assert "SCWB_VERSION', '11.4.0" in plugin


def test_linear_algebra_routes_exist():
    p = (ROOT / "backend/app/v1140.py").read_text()
    assert "/calculation-engine/v1/linear-algebra" in p
    assert "/calculation-engine/v1/linear-algebra/calculation-object" in p
    assert "tensorContraction" in p
    assert "characteristicPolynomial" in p


def test_wordpress_adapter_is_proxy_only():
    p = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1140-linear-algebra-matrix-tensor.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/linear-algebra" in p
    assert "Authoritative computation remains in FastAPI" in p


def test_standalone_linear_client_exists():
    p = (ROOT / "standalone-client/linear-algebra-engine.js").read_text()
    assert "linearAlgebra" in p
    assert "/calculation-engine/v1/linear-algebra" in p
    assert "linearAlgebraCalculationObject" in p
    assert "wp_rest" not in p


def test_compose_tracks_current_release():
    c = (ROOT / "compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.4.0" in c
    assert "d.get('version')=='11.4.0'" in c

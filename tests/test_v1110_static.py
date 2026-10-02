from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_identity_v1110():
    release = (ROOT / "backend/app/release.py").read_text()
    main = (ROOT / "backend/app/main.py").read_text()
    plugin = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php").read_text()

    assert 'APP_VERSION = "11.1.0"' in release
    assert 'version="11.1.0"' in main
    assert "from app.v1110 import router as v1110_router" in main
    assert "app.include_router(v1110_router)" in main
    assert "Version: 11.1.0" in plugin
    assert "SCWB_VERSION', '11.1.0" in plugin


def test_symbolic_routes_exist():
    p = (ROOT / "backend/app/v1110.py").read_text()
    assert "/calculation-engine/v1/symbolic/algebra" in p
    assert "/calculation-engine/v1/symbolic/calculation-object" in p
    assert "identity-check" in p
    assert "solve-system" in p
    assert "polynomialRoots" in p


def test_wordpress_adapter_is_proxy_only():
    p = (ROOT / "wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1110-advanced-symbolic-algebra.php").read_text()
    assert "wordpressRequired = false" in p
    assert "/calculation-engine/v1/symbolic/" in p
    assert "Authoritative computation remains in FastAPI" in p


def test_standalone_symbolic_client_exists():
    p = (ROOT / "standalone-client/symbolic-algebra.js").read_text()
    assert "symbolicAlgebra" in p
    assert "/calculation-engine/v1/symbolic/algebra" in p
    assert "symbolicCalculationObject" in p
    assert "wp_rest" not in p


def test_compose_tracks_current_release():
    c = (ROOT / "compose.yml").read_text()
    assert "sustainable-catalyst-workbench:11.1.0" in c
    assert "d.get('version')=='11.1.0'" in c

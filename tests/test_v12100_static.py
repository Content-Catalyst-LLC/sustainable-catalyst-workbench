from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_release():
    assert 'APP_VERSION = "12.10.0"' in (ROOT/"backend/app/release.py").read_text()
    m = (ROOT/"backend/app/main.py").read_text()
    assert 'version="12.10.0"' in m
    assert "from app.v12100 import router as v12100_router" in m
    assert "app.include_router(v12100_router)" in m

def test_backend_contract():
    p = (ROOT/"backend/app/v12100.py").read_text()
    assert "/standalone/v1/production/deployment-manifest" in p
    assert "/standalone/v1/production/environment" in p
    assert "/standalone/v1/production/certification" in p
    assert "/standalone/v1/production/readiness" in p
    assert "WordPress-Optional Production Workbench" in p

def test_standalone_client():
    p = (ROOT/"standalone-client/production-readiness.js").read_text()
    assert "StandaloneProductionReadinessClient" in p
    assert "deploymentManifest" in p
    assert "environment" in p
    assert "certification" in p
    assert "readiness" in p

def test_standalone_app():
    p = (ROOT/"standalone-app/app-shell.js").read_text()
    assert "loadProductionReadiness" in p
    assert "PRODUCTION READY" in p
    assert "productionReadiness" in p
    assert "remainingProductionActions" in p

def test_wordpress_adapter_optional_only():
    p = (ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v12100-wordpress-optional-production-workbench.php").read_text()
    assert "wordpressRequired = false" in p
    assert "optional compatibility adapter only" in p
    for term in [
        "update_option(",
        "update_user_meta(",
        "set_transient(",
        "wp_insert_post(",
    ]:
        assert term not in p

def test_compose():
    c = (ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.10.0" in c
    assert "d.get('version')=='12.10.0'" in c
    assert "SCWB_PUBLIC_API_URL" in c

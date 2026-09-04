from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'wordpress-plugin' / 'sustainable-catalyst-workbench'


def test_v560_backend_route_runtime_and_container_identity():
    main = (ROOT / 'backend' / 'app' / 'main.py').read_text()
    compose = (ROOT / 'compose.yml').read_text()
    backend = (ROOT / 'backend' / 'app' / 'v560.py').read_text()
    assert 'version="5.6.0"' in main
    assert 'from app.v560 import router as v560_router' in main
    assert 'app.include_router(v560_router)' in main
    assert 'sustainable-catalyst-workbench:5.6.0' in compose
    assert 'VERSION = "5.6.0"' in backend
    for marker in ['numerical-root-finding', 'adaptive-quadrature', 'initial-value-ode-solving', 'bounded-multivariable-optimization', 'canonical-numerical-objects']:
        assert marker in backend


def test_v560_wordpress_contract_and_studio_registration():
    main = (PLUGIN / 'sustainable-catalyst-workbench.php').read_text()
    php = (PLUGIN / 'includes' / 'scwb-v560-numerical-scientific-computing.php').read_text()
    catalog = (PLUGIN / 'includes' / 'scwb-v301-production-reliability.php').read_text()
    primary = (PLUGIN / 'includes' / 'scwb-primary-shortcode.php').read_text()
    assert 'Version: 5.6.0' in main
    assert "define('SCWB_VERSION', '5.6.0')" in main
    assert 'SCWB_V560_PLUGIN_FILE' in main
    assert "const VERSION = '5.6.0'" in php
    assert 'sc_workbench_numerical_methods' in php
    assert "'numerical' => array" in catalog
    assert 'sc_workbench_numerical_methods' in catalog
    assert "const VERSION = '5.6.0'" in primary


def test_v560_browser_numerical_runtime_contract():
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v560.js').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v560.css').read_text()
    for marker in ["VERSION='5.6.0'", "'/v560/root'", "'/v560/integrate'", "'/v560/ode'", "'/v560/linear-algebra'", "'/v560/optimize'", 'numericalObjectHash']:
        assert marker in js or marker in (ROOT / 'backend' / 'app' / 'v560.py').read_text()
    assert 'eval(' not in js
    assert 'new Function(' not in js
    assert 'scrollIntoView(' not in js
    assert 'window.scrollTo(' not in js
    for marker in ['.scwb-v560__layout', '.scwb-v560__tabs', '.scwb-v560__visual', '.scwb-v560__metrics']:
        assert marker in css


def test_v560_settings_connection_test_includes_numerical_computing():
    php = (PLUGIN / 'includes' / 'scwb-v531-settings-backend-repair.php').read_text()
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v531-admin.js').read_text()
    assert "'/v560/status'" in php
    assert 'data-scwb-v531-check="numericalComputing"' in php
    assert 'numericalComputing' in js


def test_v560_execution_boundary_remains_restricted():
    backend = (ROOT / 'backend' / 'app' / 'v560.py').read_text()
    assert 'RestrictedSympyParser' in backend
    assert 'arbitraryCodeExecutionAuthorized' in backend
    assert 'pythonEvalAuthorized' in backend
    assert 'remoteShellAuthorized' in backend
    assert 'eval(' not in backend
    assert 'exec(' not in backend

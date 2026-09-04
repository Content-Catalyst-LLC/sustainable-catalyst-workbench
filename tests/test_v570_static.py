from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'wordpress-plugin' / 'sustainable-catalyst-workbench'


def test_v570_backend_route_runtime_and_container_identity():
    main = (ROOT / 'backend' / 'app' / 'main.py').read_text()
    compose = (ROOT / 'compose.yml').read_text()
    backend = (ROOT / 'backend' / 'app' / 'v570.py').read_text()
    assert 'version="5.7.0"' in main
    assert 'from app.v570 import router as v570_router' in main
    assert 'app.include_router(v570_router)' in main
    assert 'sustainable-catalyst-workbench:5.7.0' in compose
    assert 'VERSION = "5.7.0"' in backend
    for marker in ['fft-spectrum-analysis', 'digital-filter-design', 'root-locus', 'state-space-analysis', 'pid-closed-loop-simulation', 'canonical-signals-control-objects']:
        assert marker in backend


def test_v570_wordpress_contract_and_studio_registration():
    main = (PLUGIN / 'sustainable-catalyst-workbench.php').read_text()
    php = (PLUGIN / 'includes' / 'scwb-v570-signals-systems-control-mathematics.php').read_text()
    catalog = (PLUGIN / 'includes' / 'scwb-v301-production-reliability.php').read_text()
    primary = (PLUGIN / 'includes' / 'scwb-primary-shortcode.php').read_text()
    assert 'Version: 5.7.0' in main
    assert "define('SCWB_VERSION', '5.7.0')" in main
    assert 'SCWB_V570_PLUGIN_FILE' in main
    assert "const VERSION = '5.7.0'" in php
    assert 'sc_workbench_signals_systems_controls' in php
    assert "'signals' => array" in catalog
    assert 'sc_workbench_signals_systems_controls' in catalog
    assert "const VERSION = '5.7.0'" in primary
    assert 'data-scwb-version="5.7.0"' in primary


def test_v570_browser_runtime_contract_and_viewport_safety():
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v570.js').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v570.css').read_text()
    for marker in ["VERSION='5.7.0'", "'/v570/spectrum'", "'/v570/filter-design'", "'/v570/transfer-function'", "'/v570/root-locus'", "'/v570/state-space'", "'/v570/pid'", "'/v570/convolve'", 'signalsControlObjectHash']:
        assert marker in js or marker in (ROOT / 'backend' / 'app' / 'v570.py').read_text()
    for forbidden in ['eval(', 'new Function(', 'scrollIntoView(', 'window.scrollTo(']:
        assert forbidden not in js
    for marker in ['.scwb-v570__layout', '.scwb-v570__tabs', '.scwb-v570__visual', '.scwb-v570__metrics']:
        assert marker in css


def test_v570_settings_connection_test_includes_signals_control():
    php = (PLUGIN / 'includes' / 'scwb-v531-settings-backend-repair.php').read_text()
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v531-admin.js').read_text()
    assert "'/v570/status'" in php
    assert 'data-scwb-v531-check="signalsControl"' in php
    assert 'signalsControl' in js


def test_v570_execution_boundary_remains_numeric_and_restricted():
    backend = (ROOT / 'backend' / 'app' / 'v570.py').read_text()
    for marker in ['arbitraryCodeExecutionAuthorized', 'pythonEvalAuthorized', 'remoteShellAuthorized', 'deviceExecutionAuthorized']:
        assert marker in backend
    assert 'eval(' not in backend
    assert 'exec(' not in backend

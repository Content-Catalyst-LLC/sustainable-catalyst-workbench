from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'wordpress-plugin' / 'sustainable-catalyst-workbench'


def test_v580_backend_route_runtime_and_container_identity():
    main = (ROOT / 'backend' / 'app' / 'main.py').read_text()
    compose = (ROOT / 'compose.yml').read_text()
    backend = (ROOT / 'backend' / 'app' / 'v580.py').read_text()
    assert 'version="5.8.0"' in main or 'version="5.9.0"' in main or 'version="6.0.0"' in main or 'version="6.0.1"' in main or 'version="6.1.0"' in main or 'version="6.2.0"' in main or 'version="6.4.0"' in main or 'version="6.5.0"' in main or 'version="6.6.0"' in main or 'version="6.7.0"' in main or 'version="6.8.0"' in main or 'version="8.1.0"' in main
    assert 'from app.v580 import router as v580_router' in main
    assert 'app.include_router(v580_router)' in main
    assert 'sustainable-catalyst-workbench:5.8.0' in compose or 'sustainable-catalyst-workbench:5.9.0' in compose or 'sustainable-catalyst-workbench:6.0.0' in compose or 'sustainable-catalyst-workbench:6.0.1' in compose or 'sustainable-catalyst-workbench:6.1.0' in compose or 'sustainable-catalyst-workbench:6.2.0' in compose or 'sustainable-catalyst-workbench:6.4.0' in compose or 'sustainable-catalyst-workbench:6.5.0' in compose or 'sustainable-catalyst-workbench:6.6.0' in compose or 'sustainable-catalyst-workbench:6.7.0' in compose or 'sustainable-catalyst-workbench:6.8.0' in compose or 'sustainable-catalyst-workbench:8.1.0' in compose
    assert 'VERSION = "5.8.0"' in backend
    for marker in ['resistor-network-analysis','rlc-impedance-analysis','adc-dac-quantization','pwm-timer-planning','sampling-nyquist-analysis','i2c-spi-uart-planning','sensor-transfer-models','gpio-allocation-planning','export-only-embedded-scaffolds','canonical-electronics-embedded-objects']:
        assert marker in backend


def test_v580_wordpress_contract_and_studio_registration():
    main = (PLUGIN / 'sustainable-catalyst-workbench.php').read_text()
    php = (PLUGIN / 'includes' / 'scwb-v580-electronics-embedded-systems.php').read_text()
    catalog = (PLUGIN / 'includes' / 'scwb-v301-production-reliability.php').read_text()
    primary = (PLUGIN / 'includes' / 'scwb-primary-shortcode.php').read_text()
    assert 'Version: 5.8.0' in main or 'Version: 5.9.0' in main or 'Version: 6.0.0' in main or 'Version: 6.0.1' in main or 'Version: 6.1.0' in main or 'Version: 6.2.0' in main or 'Version: 6.4.0' in main or 'Version: 6.5.0' in main or 'Version: 6.6.0' in main or 'Version: 6.7.0' in main or 'Version: 6.8.0' in main or 'Version: 8.1.0' in main
    assert "define('SCWB_VERSION', '5.8.0')" in main or "define('SCWB_VERSION', '5.9.0')" in main or "define('SCWB_VERSION', '6.0.0')" in main or "define('SCWB_VERSION', '6.0.1')" in main or "define('SCWB_VERSION', '6.1.0')" in main or "define('SCWB_VERSION', '6.2.0')" in main or "define('SCWB_VERSION', '6.4.0')" in main or "define('SCWB_VERSION', '6.5.0')" in main or "define('SCWB_VERSION', '6.6.0')" in main or "define('SCWB_VERSION', '6.7.0')" in main or "define('SCWB_VERSION', '6.8.0')" in main or "define('SCWB_VERSION', '8.1.0')" in main
    assert 'SCWB_V580_PLUGIN_FILE' in main
    assert "const VERSION = '5.8.0'" in php
    assert 'sc_workbench_electronics_embedded' in php
    assert "'electronics' => array" in catalog
    assert 'sc_workbench_electronics_embedded' in catalog
    assert "const VERSION = '5.8.0'" in primary or "const VERSION = '5.9.0'" in primary or "const VERSION = '6.0.0'" in primary or "const VERSION = '6.0.1'" in primary
    assert 'data-scwb-version="5.8.0"' in primary or 'data-scwb-version="5.9.0"' in primary or 'data-scwb-version="6.0.0"' in primary or 'data-scwb-version="6.0.1"' in primary


def test_v580_browser_runtime_contract_and_viewport_safety():
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v580.js').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v580.css').read_text()
    backend = (ROOT / 'backend' / 'app' / 'v580.py').read_text()
    for marker in ["VERSION='5.8.0'", "'/v580/resistor-network'", "'/v580/adc-dac'", "'/v580/pwm-timer'", "'/v580/sampling'", "'/v580/bus-plan'", "'/v580/sensor-model'", "'/v580/gpio-plan'", "'/v580/prototype-scaffold'", 'electronicsEmbeddedObjectHash']:
        assert marker in js or marker in backend
    for forbidden in ['eval(', 'new Function(', 'scrollIntoView(', 'window.scrollTo(']:
        assert forbidden not in js
    for marker in ['.scwb-v580__layout', '.scwb-v580__tabs', '.scwb-v580__visual', '.scwb-v580__metrics']:
        assert marker in css


def test_v580_settings_connection_test_includes_electronics_embedded():
    php = (PLUGIN / 'includes' / 'scwb-v531-settings-backend-repair.php').read_text()
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v531-admin.js').read_text()
    assert "'/v580/status'" in php
    assert 'data-scwb-v531-check="electronicsEmbedded"' in php
    assert 'electronicsEmbedded' in js


def test_v580_execution_boundary_remains_analysis_and_export_only():
    backend = (ROOT / 'backend' / 'app' / 'v580.py').read_text()
    for marker in ['arbitraryCodeExecutionAuthorized','pythonEvalAuthorized','remoteShellAuthorized','deviceExecutionAuthorized','automaticDeviceProgrammingAuthorized','serialPortAccessAuthorized','gpioAccessAuthorized','jtagAccessAuthorized']:
        assert marker in backend
    assert 'eval(' not in backend
    assert 'exec(' not in backend
    assert 'serial.Serial' not in backend
    assert '/dev/tty' not in backend

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'wordpress-plugin' / 'sustainable-catalyst-workbench'


def test_v590_backend_route_runtime_and_container_identity():
    main = (ROOT / 'backend' / 'app' / 'main.py').read_text()
    compose = (ROOT / 'compose.yml').read_text()
    backend = (ROOT / 'backend' / 'app' / 'v590.py').read_text()
    assert 'version="5.9.0"' in main or 'version="6.0.0"' in main or 'version="6.0.1"' in main or 'version="6.1.0"' in main or 'version="6.2.0"' in main or 'version="6.4.0"' in main or 'version="6.5.0"' in main or 'version="6.6.0"' in main or 'version="6.7.0"' in main or 'version="6.8.0"' in main or 'version="8.1.0"' in main
    assert 'from app.v590 import router as v590_router' in main
    assert 'app.include_router(v590_router)' in main
    assert 'sustainable-catalyst-workbench:5.9.0' in compose or 'sustainable-catalyst-workbench:6.0.0' in compose or 'sustainable-catalyst-workbench:6.0.1' in compose or 'sustainable-catalyst-workbench:6.1.0' in compose or 'sustainable-catalyst-workbench:6.2.0' in compose or 'sustainable-catalyst-workbench:6.4.0' in compose or 'sustainable-catalyst-workbench:6.5.0' in compose or 'sustainable-catalyst-workbench:6.6.0' in compose or 'sustainable-catalyst-workbench:6.7.0' in compose or 'sustainable-catalyst-workbench:6.8.0' in compose or 'sustainable-catalyst-workbench:8.1.0' in compose
    assert 'VERSION = "5.9.0"' in backend
    for marker in ['truth-tables','boolean-minimization','karnaugh-maps','finite-state-machine-validation','digital-timing-waveforms','verilog-scaffolds','pynq-overlay-scaffolds','canonical-digital-logic-objects']:
        assert marker in backend


def test_v590_wordpress_contract_and_studio_registration():
    main = (PLUGIN / 'sustainable-catalyst-workbench.php').read_text()
    php = (PLUGIN / 'includes' / 'scwb-v590-fpga-pynq-digital-logic.php').read_text()
    catalog = (PLUGIN / 'includes' / 'scwb-v301-production-reliability.php').read_text()
    primary = (PLUGIN / 'includes' / 'scwb-primary-shortcode.php').read_text()
    assert 'Version: 5.9.0' in main or 'Version: 6.0.0' in main or 'Version: 6.0.1' in main or 'Version: 6.1.0' in main or 'Version: 6.2.0' in main or 'Version: 6.4.0' in main or 'Version: 6.5.0' in main or 'Version: 6.6.0' in main or 'Version: 6.7.0' in main or 'Version: 6.8.0' in main or 'Version: 8.1.0' in main
    assert "define('SCWB_VERSION', '5.9.0')" in main or "define('SCWB_VERSION', '6.0.0')" in main or "define('SCWB_VERSION', '6.0.1')" in main or "define('SCWB_VERSION', '6.1.0')" in main or "define('SCWB_VERSION', '6.2.0')" in main or "define('SCWB_VERSION', '6.4.0')" in main or "define('SCWB_VERSION', '6.5.0')" in main or "define('SCWB_VERSION', '6.6.0')" in main or "define('SCWB_VERSION', '6.7.0')" in main or "define('SCWB_VERSION', '6.8.0')" in main or "define('SCWB_VERSION', '8.1.0')" in main
    assert 'SCWB_V590_PLUGIN_FILE' in main
    assert "const VERSION = '5.9.0'" in php
    assert 'sc_workbench_digital_logic' in php
    assert "'digital-logic' => array" in catalog
    assert 'sc_workbench_digital_logic' in catalog
    assert "const VERSION = '5.9.0'" in primary or "const VERSION = '6.0.0'" in primary or "const VERSION = '6.0.1'" in primary
    assert 'data-scwb-version="5.9.0"' in primary or 'data-scwb-version="6.0.0"' in primary or 'data-scwb-version="6.0.1"' in primary


def test_v590_browser_runtime_contract_and_viewport_safety():
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v590.js').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v590.css').read_text()
    backend = (ROOT / 'backend' / 'app' / 'v590.py').read_text()
    for marker in ["VERSION='5.9.0'", 'truthTable', 'minimize', 'karnaugh', 'fsm', 'timing', 'hdlScaffold', 'resourceEstimate', 'pynqOverlay', 'digitalLogicObjectHash']:
        assert marker in js or marker in backend
    for route in ['/truth-table','/minimize','/karnaugh','/fsm','/timing','/hdl-scaffold','/resource-estimate','/pynq-overlay']:
        assert route in backend
    for forbidden in ['eval(', 'new Function(', 'scrollIntoView(', 'window.scrollTo(']:
        assert forbidden not in js
    for marker in ['.scwb-v590__layout', '.scwb-v590__tabs', '.scwb-v590__visual', '.scwb-v590__metrics']:
        assert marker in css


def test_v590_settings_connection_test_includes_digital_logic():
    php = (PLUGIN / 'includes' / 'scwb-v531-settings-backend-repair.php').read_text()
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v531-admin.js').read_text()
    assert "'/v590/status'" in php
    assert 'data-scwb-v531-check="digitalLogic"' in php
    assert 'digitalLogic' in js


def test_v590_execution_boundary_blocks_synthesis_and_programming():
    backend = (ROOT / 'backend' / 'app' / 'v590.py').read_text()
    for marker in ['arbitraryCodeExecutionAuthorized','pythonEvalAuthorized','remoteShellAuthorized','synthesisExecutionAuthorized','bitstreamGenerationAuthorized','bitstreamProgrammingAuthorized','jtagAccessAuthorized','deviceExecutionAuthorized']:
        assert marker in backend
    assert 'eval(' not in backend
    assert 'exec(' not in backend
    assert 'subprocess' not in backend
    assert 'os.system' not in backend

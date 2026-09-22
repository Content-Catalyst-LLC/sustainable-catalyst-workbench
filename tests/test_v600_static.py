from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'wordpress-plugin' / 'sustainable-catalyst-workbench'


def test_v600_backend_route_runtime_and_container_identity():
    main = (ROOT / 'backend' / 'app' / 'main.py').read_text()
    compose = (ROOT / 'compose.yml').read_text()
    backend = (ROOT / 'backend' / 'app' / 'v600.py').read_text()
    assert 'version="6.0.1"' in main or 'version="6.1.0"' in main or 'version="6.2.0"' in main or 'version="6.4.0"' in main or 'version="6.5.0"' in main or 'version="6.6.0"' in main or 'version="6.7.0"' in main or 'version="6.8.0"' in main or 'version="6.13.0"' in main
    assert 'from app.v600 import router as v600_router' in main
    assert 'app.include_router(v600_router)' in main
    assert 'sustainable-catalyst-workbench:6.0.1' in compose or 'sustainable-catalyst-workbench:6.1.0' in compose or 'sustainable-catalyst-workbench:6.2.0' in compose or 'sustainable-catalyst-workbench:6.4.0' in compose or 'sustainable-catalyst-workbench:6.5.0' in compose or 'sustainable-catalyst-workbench:6.6.0' in compose or 'sustainable-catalyst-workbench:6.7.0' in compose or 'sustainable-catalyst-workbench:6.8.0' in compose or 'sustainable-catalyst-workbench:6.13.0' in compose
    assert 'VERSION = "6.0.1"' in backend
    for marker in ['canonical-computational-projects','shared-project-variables','linked-computational-objects','computational-provenance','append-only-project-history','portable-computational-exports','cross-platform-handoff-packets']:
        assert marker in backend


def test_v600_wordpress_contract_and_studio_registration():
    main = (PLUGIN / 'sustainable-catalyst-workbench.php').read_text()
    php = (PLUGIN / 'includes' / 'scwb-v600-unified-computational-workbench.php').read_text()
    catalog = (PLUGIN / 'includes' / 'scwb-v301-production-reliability.php').read_text()
    primary = (PLUGIN / 'includes' / 'scwb-primary-shortcode.php').read_text()
    assert 'Version: 6.0.1' in main or 'Version: 6.1.0' in main or 'Version: 6.2.0' in main or 'Version: 6.4.0' in main or 'Version: 6.5.0' in main or 'Version: 6.6.0' in main or 'Version: 6.7.0' in main or 'Version: 6.8.0' in main or 'Version: 6.13.0' in main
    assert "define('SCWB_VERSION', '6.0.1')" in main or "define('SCWB_VERSION', '6.1.0')" in main or "define('SCWB_VERSION', '6.2.0')" in main or "define('SCWB_VERSION', '6.4.0')" in main or "define('SCWB_VERSION', '6.5.0')" in main or "define('SCWB_VERSION', '6.6.0')" in main or "define('SCWB_VERSION', '6.7.0')" in main or "define('SCWB_VERSION', '6.8.0')" in main or "define('SCWB_VERSION', '6.13.0')" in main
    assert 'SCWB_V600_PLUGIN_FILE' in main
    assert "const VERSION = '6.0.1'" in php
    assert 'sc_workbench_computational_project' in php
    assert "'computational-project' => array" in catalog
    assert "const VERSION = '6.0.1'" in primary
    assert 'data-scwb-version="6.0.1"' in primary
    assert "'studio' => 'computational-project'" in primary


def test_v600_browser_runtime_contract_and_viewport_safety():
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v600.js').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v600.css').read_text()
    for marker in ["VERSION='6.0.1'", 'projectBuild', 'variablesResolve', 'linksValidate', 'historyBuild', 'exportBuild', 'handoffBuild', 'localStorage']:
        assert marker in js
    for forbidden in ['eval(', 'new Function(', 'scrollIntoView(', 'window.scrollTo(']:
        assert forbidden not in js
    for marker in ['.scwb-v600__layout', '.scwb-v600__graph', '.scwb-v600__metrics', '.scwb-v600__handoff']:
        assert marker in css


def test_v600_settings_connection_test_includes_unified_computational():
    php = (PLUGIN / 'includes' / 'scwb-v531-settings-backend-repair.php').read_text()
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v531-admin.js').read_text()
    assert "'/v601/status'" in php
    assert 'data-scwb-v531-check="unifiedComputational"' in php
    assert 'unifiedComputational' in js


def test_v600_execution_boundary_blocks_autonomous_actions():
    backend = (ROOT / 'backend' / 'app' / 'v600.py').read_text()
    for marker in ['automaticExecutionAuthorized','automaticPublicationAuthorized','automaticCertificationAuthorized','automaticDeviceProgrammingAuthorized','automaticDestructiveSynchronizationAuthorized','remoteShellAuthorized','arbitraryCodeExecutionAuthorized']:
        assert marker in backend
    assert 'subprocess' not in backend
    assert 'os.system' not in backend
    assert 'eval(' not in backend
    assert 'exec(' not in backend

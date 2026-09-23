from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'wordpress-plugin' / 'sustainable-catalyst-workbench'


def test_v601_backend_identity_route_and_container():
    main = (ROOT / 'backend' / 'app' / 'main.py').read_text()
    backend = (ROOT / 'backend' / 'app' / 'v601.py').read_text()
    compose = (ROOT / 'compose.yml').read_text()
    assert 'version="6.0.1"' in main or 'version="6.1.0"' in main or 'version="6.2.0"' in main or 'version="6.4.0"' in main or 'version="6.5.0"' in main or 'version="6.6.0"' in main or 'version="6.7.0"' in main or 'version="6.8.0"' in main or 'version="8.1.0"' in main
    assert 'from app.v601 import router as v601_router' in main
    assert 'app.include_router(v601_router)' in main
    assert 'VERSION = "6.0.1"' in backend
    assert 'prefix="/v601"' in backend
    assert 'sustainable-catalyst-workbench:6.0.1' in compose or 'sustainable-catalyst-workbench:6.1.0' in compose or 'sustainable-catalyst-workbench:6.2.0' in compose or 'sustainable-catalyst-workbench:6.4.0' in compose or 'sustainable-catalyst-workbench:6.5.0' in compose or 'sustainable-catalyst-workbench:6.6.0' in compose or 'sustainable-catalyst-workbench:6.7.0' in compose or 'sustainable-catalyst-workbench:6.8.0' in compose or 'sustainable-catalyst-workbench:8.1.0' in compose


def test_v601_wordpress_identity_and_native_experience():
    main = (PLUGIN / 'sustainable-catalyst-workbench.php').read_text()
    primary = (PLUGIN / 'includes' / 'scwb-primary-shortcode.php').read_text()
    experience = (PLUGIN / 'includes' / 'scwb-v601-unified-experience-hardening.php').read_text()
    assert 'Version: 6.0.1' in main or 'Version: 6.1.0' in main or 'Version: 6.2.0' in main or 'Version: 6.4.0' in main or 'Version: 6.5.0' in main or 'Version: 6.6.0' in main or 'Version: 6.7.0' in main or 'Version: 6.8.0' in main or 'Version: 8.1.0' in main
    assert "define('SCWB_VERSION', '6.0.1')" in main or "define('SCWB_VERSION', '6.1.0')" in main or "define('SCWB_VERSION', '6.2.0')" in main or "define('SCWB_VERSION', '6.4.0')" in main or "define('SCWB_VERSION', '6.5.0')" in main or "define('SCWB_VERSION', '6.6.0')" in main or "define('SCWB_VERSION', '6.7.0')" in main or "define('SCWB_VERSION', '6.8.0')" in main or "define('SCWB_VERSION', '8.1.0')" in main
    assert 'scwb-v601-unified-experience-hardening.php' in main
    assert "const VERSION = '6.0.1'" in primary
    assert 'data-scwb-version="6.0.1"' in primary
    assert 'sc_workbench_experience' in experience
    assert 'sc_workbench_homepage_instrument' not in experience
    assert 'data-scwb-v601-experience' in experience


def test_v601_grouped_navigation_and_local_interface_state():
    primary = (PLUGIN / 'includes' / 'scwb-primary-shortcode.php').read_text()
    js = (PLUGIN / 'assets' / 'js' / 'scwb-primary-repair.js').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'scwb-primary-repair.css').read_text()
    for marker in ['data-scwb-studio-search','data-scwb-studio-filter','data-scwb-favorite','studio_group','Favorites','Recent']:
        assert marker in primary
    for marker in ["VERSION = '6.0.1'", 'favoritesKey', 'recentsKey', 'applyFilter', 'scwb:studio-activated', 'scwb:visual-resize']:
        assert marker in js
    assert 'max-height:min(72vh,720px)' in css
    assert 'overflow-y:auto' in css


def test_v601_graph_hardening_contract():
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v540.js').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v601.css').read_text()
    for marker in ['ResizeObserver','scwb:studio-activated','scwb:panel-visible','scwb:visual-resize','fullscreenchange','visibilitychange','redrawStable']:
        assert marker in js
    assert 'position:relative!important;top:auto!important' in css
    assert 'overflow:visible!important' in css
    for forbidden in ['window.scrollTo(', 'scrollIntoView(', 'new Function(']:
        assert forbidden not in js


def test_v601_v600_project_layout_no_fixed_whitespace_floor():
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v600.css').read_text()
    assert 'min-height:720px' not in css
    assert 'max-height:680px' in css
    assert 'overscroll-behavior:contain' in css


def test_v601_settings_uses_patch_status_route():
    settings = (PLUGIN / 'includes' / 'scwb-v531-settings-backend-repair.php').read_text()
    assert "'/v601/status'" in settings
    assert 'UNIFIED EXPERIENCE' in settings


def test_v601_security_boundary_stays_non_executing():
    backend = (ROOT / 'backend' / 'app' / 'v601.py').read_text()
    for marker in ['automaticCodeExecutionAuthorized','remoteShellAuthorized','automaticDeviceProgrammingAuthorized']:
        assert marker in backend
    for forbidden in ['subprocess', 'os.system', 'eval(', 'exec(']:
        assert forbidden not in backend

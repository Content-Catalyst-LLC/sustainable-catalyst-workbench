from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'wordpress-plugin' / 'sustainable-catalyst-workbench'


def test_v550_backend_route_runtime_and_container_identity():
    main = (ROOT / 'backend' / 'app' / 'main.py').read_text()
    compose = (ROOT / 'compose.yml').read_text()
    backend = (ROOT / 'backend' / 'app' / 'v550.py').read_text()
    assert 'from app.v550 import router as v550_router' in main
    assert 'app.include_router(v550_router)' in main
    assert 'sustainable-catalyst-workbench:5.5.0' in compose
    assert 'VERSION = "5.5.0"' in backend
    for marker in ['draggable-points', 'affine-transformations', 'expression-linked-loci', 'canonical-geometry-objects']:
        assert marker in backend


def test_v550_wordpress_contract_and_studio_registration():
    main = (PLUGIN / 'sustainable-catalyst-workbench.php').read_text()
    php = (PLUGIN / 'includes' / 'scwb-v550-dynamic-geometry.php').read_text()
    catalog = (PLUGIN / 'includes' / 'scwb-v301-production-reliability.php').read_text()
    primary = (PLUGIN / 'includes' / 'scwb-primary-shortcode.php').read_text()
    assert 'Version: 5.5.0' in main
    assert "define('SCWB_VERSION', '5.5.0')" in main
    assert 'SCWB_V550_PLUGIN_FILE' in main
    assert "const VERSION = '5.5.0'" in php
    assert 'sc_workbench_dynamic_geometry' in php
    assert "'geometry' => array" in catalog
    assert 'sc_workbench_dynamic_geometry' in catalog
    assert "const VERSION = '5.5.0'" in primary


def test_v550_browser_dynamic_interaction_contract():
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v550.js').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v550.css').read_text()
    for marker in ['pointerdown', 'pointermove', 'pointerup', "post(root,'construction'", "post(root,'transform'", "post(root,'locus'", 'finalizePolygon', 'geometryObjectHash']:
        assert marker in js
    assert 'eval(' not in js
    assert 'new Function(' not in js
    assert 'scrollIntoView(' not in js
    assert 'window.scrollTo(' not in js
    for marker in ['.scwb-v550__canvas-wrap', '.scwb-v550__measurements', '.scwb-v550__history', '.scwb-v550__transform-grid']:
        assert marker in css


def test_v550_settings_connection_test_includes_dynamic_geometry():
    php = (PLUGIN / 'includes' / 'scwb-v531-settings-backend-repair.php').read_text()
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v531-admin.js').read_text()
    assert "'/v550/status'" in php
    assert 'data-scwb-v531-check="dynamicGeometry"' in php
    assert 'dynamicGeometry' in js


def test_v550_execution_boundary_remains_restricted():
    backend = (ROOT / 'backend' / 'app' / 'v550.py').read_text()
    assert 'RestrictedSympyParser' in backend
    assert 'arbitraryCodeExecutionAuthorized' in backend
    assert 'pythonEvalAuthorized' in backend
    assert 'remoteShellAuthorized' in backend
    assert 'eval(' not in backend
    assert 'exec(' not in backend

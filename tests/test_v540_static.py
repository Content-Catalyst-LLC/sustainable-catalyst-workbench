from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'wordpress-plugin' / 'sustainable-catalyst-workbench'


def test_v540_backend_route_and_runtime_identity():
    main = (ROOT / 'backend' / 'app' / 'main.py').read_text()
    compose = (ROOT / 'compose.yml').read_text()
    assert 'version="5.4.0"' in main or 'version="5.5.0"' in main or 'version="5.6.0"' in main or 'version="5.7.0"' in main
    assert 'from app.v540 import router as v540_router' in main
    assert 'app.include_router(v540_router)' in main
    assert 'sustainable-catalyst-workbench:5.4.0' in compose or 'sustainable-catalyst-workbench:5.5.0' in compose or 'sustainable-catalyst-workbench:5.6.0' in compose or 'sustainable-catalyst-workbench:5.7.0' in compose


def test_v540_wordpress_advanced_graph_contract():
    main = (PLUGIN / 'sustainable-catalyst-workbench.php').read_text()
    php = (PLUGIN / 'includes' / 'scwb-v540-advanced-graph-mathematics.php').read_text()
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v540.js').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v540.css').read_text()
    assert 'Version: 5.4.0' in main or 'Version: 5.5.0' in main or 'Version: 5.6.0' in main or 'Version: 5.7.0' in main
    assert 'SCWB_V540_PLUGIN_FILE' in main
    assert "const VERSION = '5.4.0'" in php
    for marker in [
        'sc_workbench_advanced_graph_mathematics', 'EXPRESSION STACK', 'Piecewise functions',
        'Tangent at x', 'Inequality / region', 'Value table', 'Fullscreen',
    ]:
        assert marker in php
    for marker in ['multi-graph', 'pairwise', 'nearestTrace', 'is-panning', 'loadTable', 'domainMin', 'region']:
        assert marker in js
    for marker in ['.scwb-v540__series-stack', '.scwb-v540__analysis', '.scwb-v540__table', '.scwb-v540__trace']:
        assert marker in css


def test_v540_settings_connection_test_includes_advanced_graph():
    php = (PLUGIN / 'includes' / 'scwb-v531-settings-backend-repair.php').read_text()
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v531-admin.js').read_text()
    assert "'/v540/status'" in php
    assert 'data-scwb-v531-check="advancedGraph"' in php
    assert 'advancedGraph' in js


def test_v540_restricted_execution_boundary():
    backend = (ROOT / 'backend' / 'app' / 'v540.py').read_text()
    assert 'RestrictedSympyParser' in backend
    assert 'arbitraryCodeExecutionAuthorized' in backend
    assert 'pythonEvalAuthorized' in backend
    assert 'remoteShellAuthorized' in backend
    assert 'eval(' not in backend
    assert 'exec(' not in backend

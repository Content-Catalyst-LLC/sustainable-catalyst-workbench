from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'wordpress-plugin' / 'sustainable-catalyst-workbench'


def test_v533_scroll_guard_contract():
    js = (PLUGIN / 'assets' / 'js' / 'sc-workbench-v532.js').read_text()
    assert 'centerRailButton' in js
    assert "rail.scrollTo({left:Math.max(0,target),behavior:'smooth'})" in js
    assert 'render(false)' in js
    assert 'scrollIntoView' not in js
    assert 'window.scrollTo' not in js
    assert 'location.hash' not in js


def test_v533_homepage_integration_contract():
    php = (PLUGIN / 'includes' / 'scwb-v533-integration-hardening.php').read_text()
    css = (PLUGIN / 'assets' / 'css' / 'sc-workbench-v533.css').read_text()
    assert "const VERSION = '5.3.3'" in php
    assert 'viewportScrollGuard' in php
    assert 'render_legacy_showcase_guard' in php
    assert 'sc_workbench_homepage_instrument' in php
    assert '.cch-workbench-showcase__inner' in css
    assert '.cc-home-v4 > .scwb-v533-home' in css
    assert 'overflow-y: hidden' in css


def test_v533_backend_compatibility_line_remains_available():
    main=(ROOT / 'backend' / 'app' / 'main.py').read_text()
    assert 'from app.v530 import router as v530_router' in main
    assert 'sustainable-catalyst-workbench:' in (ROOT / 'compose.yml').read_text()

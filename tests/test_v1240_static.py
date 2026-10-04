from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release():
    assert 'APP_VERSION = "12.4.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="12.4.0"' in m
    assert "from app.v1240 import router as v1240_router" in m

def test_backend_routes():
    p=(ROOT/"backend/app/v1240.py").read_text()
    assert "/standalone/v1/renderer/config" in p
    assert "/standalone/v1/renderer/view-spec" in p
    assert "execute_graphing" in p

def test_renderer_client():
    p=(ROOT/"standalone-client/mathematical-renderer.js").read_text()
    assert "StandaloneMathematicalRendererClient" in p
    assert "viewSpec" in p

def test_browser_renderer():
    p=(ROOT/"standalone-app/math-renderer.js").read_text()
    assert "renderMathematicalViews" in p
    assert "renderCartesian" in p
    assert "renderImplicit" in p
    assert "renderLinkedTable" in p
    assert "createElementNS" in p

def test_app_integration():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    assert "requestGraphView" in p
    assert 'id="calculator-graph"' in p
    assert "renderMathematicalViews" in p

def test_wordpress_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1240-standalone-mathematical-view-renderer.php").read_text()
    assert "wordpressRequired = false" in p
    assert "WordPress does not own mathematical rendering" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.4.0" in c
    assert "d.get('version')=='12.4.0'" in c

from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_identity():
    assert 'APP_VERSION = "12.3.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="12.3.0"' in m
    assert "from app.v1230 import router as v1230_router" in m
    assert "app.include_router(v1230_router)" in m

def test_browser_cors_methods():
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"]' in m

def test_workspace_routes():
    p=(ROOT/"backend/app/v1230.py").read_text()
    assert "/standalone/v1/calculator/config" in p
    assert "/standalone/v1/calculator/execute" in p
    assert "build_calculation_object" in p
    assert "save_calculation" in p
    assert "oneStepExecuteAndSave" in p

def test_standalone_client():
    p=(ROOT/"standalone-client/calculator-workspace.js").read_text()
    assert "StandaloneCalculatorWorkspaceClient" in p
    assert "execute" in p
    assert "executeAndSave" in p

def test_app_shell_calculator_ui():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    assert 'id="calculator-expression"' in p
    assert 'id="calculator-operation"' in p
    assert 'id="calculator-project"' in p
    assert "executeCalculator" in p
    assert "saveResult" in p

def test_wordpress_optional():
    p=(ROOT/"wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v1230-standalone-calculator-workspace.php").read_text()
    assert "wordpressRequired = false" in p
    assert "WordPress does not own calculator execution" in p
    assert "/standalone/v1/calculator/config" in p

def test_compose():
    c=(ROOT/"compose.yml").read_text()
    assert "sustainable-catalyst-workbench:12.3.0" in c
    assert "d.get('version')=='12.3.0'" in c

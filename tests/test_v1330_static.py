import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_release_router_and_version():
    assert 'APP_VERSION = "13.3.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="13.3.0"' in m
    assert "from app.v1330 import router as v1330_router" in m
    assert "app.include_router(v1330_router)" in m

def test_frontend_assets():
    assert (ROOT/"standalone-app/math-input.js").exists()
    shell=(ROOT/"standalone-app/app-shell.js").read_text()
    for x in ["paletteHtml","insertAtCursor","/standalone/v1/calculator/normalize","normalizedExpression","originalExpression"]:
        assert x in shell

def test_version_manifest():
    d=json.loads((ROOT/"standalone-app/version.json").read_text())
    assert d["version"]=="13.3.0"
    assert d["interface"]=="advanced-calculator-input-mathematical-notation"

def test_normalization_guardrail():
    p=(ROOT/"backend/app/v1330.py").read_text()
    assert "implicitMultiplicationIsNotInferred" in p
    assert "originalInputPreserved" in p
    assert "normalizationIsDerivedRepresentation" in p

def test_client():
    p=(ROOT/"standalone-client/math-input.js").read_text()
    assert "MathematicalNotationClient" in p
    assert "/standalone/v1/calculator/normalize" in p

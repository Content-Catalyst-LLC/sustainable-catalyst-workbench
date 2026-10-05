import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_release_and_router():
    assert 'APP_VERSION = "13.2.0"' in (ROOT/"backend/app/release.py").read_text()
    m=(ROOT/"backend/app/main.py").read_text()
    assert 'version="13.2.0"' in m and "from app.v1320 import router as v1320_router" in m
def test_frontend_version():
    assert json.loads((ROOT/"standalone-app/version.json").read_text())["version"]=="13.2.0"
def test_result_presentation_ui():
    p=(ROOT/"standalone-app/app-shell.js").read_text()
    for t in ["answerCard","primaryResult","Copy result","Technical calculation object","recent.expressions","calc-guess"]: assert t in p
def test_presentation_client():
    assert "CalculationPresentationClient" in (ROOT/"standalone-client/calculation-presentation.js").read_text()
def test_backend_adapter():
    p=(ROOT/"backend/app/v1320.py").read_text()
    assert "/standalone/v1/calculator/presentation" in p and "canonicalComputationAuthority" in p

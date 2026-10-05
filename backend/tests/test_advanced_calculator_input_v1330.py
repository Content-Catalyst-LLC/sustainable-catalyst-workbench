import os
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def setup_module():
    os.environ["SCWB_SESSION_SECRET"]="v133-test-session-secret"
    os.environ["SCWB_DEEP_LINK_SECRET"]="v133-test-link-secret"
    os.environ["SCWB_STANDALONE_APP_URL"]="https://workbench.example.test"
    os.environ["SCWB_PUBLIC_API_URL"]="https://workbench-api.example.test"
    os.environ["SCWB_ALLOWED_ORIGINS"]="https://workbench.example.test"

def test_status_and_contract():
    d=client.get("/v1330/status").json()
    assert d["version"]=="13.3.0"
    assert d["inputExperienceReady"] is True
    assert all(d["checks"].values())
    c=client.get("/standalone/v1/calculator/input-contract").json()["input"]
    assert c["originalInputCanonical"] is True
    assert c["normalizedInputDerived"] is True
    assert c["features"]["cursorAwareInsertion"] is True

def normalize(expression):
    r=client.post("/standalone/v1/calculator/normalize",json={"expression":expression})
    assert r.status_code==200
    return r.json()["normalization"]

def test_common_unicode_notation_normalizes_deterministically():
    d=normalize("√(x² + π) ÷ 2")
    assert d["originalExpression"]=="√(x² + π) ÷ 2"
    assert d["normalizedExpression"]=="sqrt(x**2 + pi) / 2"
    assert d["changed"] is True
    assert d["transformations"]
    assert d["principles"]["normalizationIsDerivedRepresentation"] is True

def test_caret_and_function_aliases():
    d=normalize("ln(x^2) + arcsin(y)")
    assert d["normalizedExpression"]=="log(x**2) + asin(y)"

def test_ambiguous_implicit_multiplication_is_not_silently_inferred():
    d=normalize("2x + 1")
    assert d["normalizedExpression"]=="2x + 1"
    assert "implicit-multiplication-not-expanded" in d["ambiguities"]

def test_plain_expression_is_stable():
    d=normalize("sin(x) + 2*3")
    assert d["normalizedExpression"]=="sin(x) + 2*3"
    assert d["changed"] is False

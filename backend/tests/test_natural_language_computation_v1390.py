from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v1390/status").json()
    assert d["version"]=="13.9.0"
    assert d["naturalLanguageFoundationReady"] is True
    assert d["checks"]["directExecutionDisabled"] is True
    assert all(d["checks"].values())

def interpret(text):
    r=client.post("/standalone/v1/natural-language/interpret",json={"text":text,"mode":"conservative"})
    assert r.status_code==200
    return r.json()["interpretation"]

def test_evaluate_and_symbolic_intents():
    e=interpret("calculate 2 + 3 * 4")
    assert e["intent"]=="evaluate"
    assert e["proposedCalculationRequest"]["calculation"]["expression"]=="2 + 3 * 4"
    assert e["proposedCalculationRequest"]["requestedResultType"]=="numeric"
    assert e["executionAllowed"] is False
    assert e["requiresConfirmation"] is True

    d=interpret("differentiate x^3 + 2*x with respect to x")
    assert d["intent"]=="differentiate"
    assert d["proposedCalculationRequest"]["calculation"]["operation"]=="differentiate"
    assert d["proposedCalculationRequest"]["calculation"]["variable"]=="x"
    assert "**3" in d["proposedCalculationRequest"]["calculation"]["expression"]

    s=interpret("solve x + 2 = 5 for x")
    assert s["intent"]=="solve"
    assert s["proposedCalculationRequest"]["calculation"]["variable"]=="x"
    assert "=" in s["proposedCalculationRequest"]["calculation"]["expression"]

def test_ambiguity_is_not_guessed():
    d=interpret("calculate 2x + 1")
    assert "implicit-multiplication-not-expanded" in d["ambiguities"]
    assert d["executionAllowed"] is False

    u=interpret("tell me something mathematical")
    assert u["intent"] is None
    assert u["proposedCalculationRequest"] is None
    assert "unrecognized-natural-language-intent" in u["ambiguities"]

def test_contract_preserves_authority():
    d=client.get("/standalone/v1/natural-language/contract").json()["naturalLanguage"]
    assert d["features"]["canonicalCalculationAuthorityPreserved"] is True
    assert d["features"]["directExecutionDisabled"] is True
    assert d["features"]["unifiedWorkspacePreserved"] is True

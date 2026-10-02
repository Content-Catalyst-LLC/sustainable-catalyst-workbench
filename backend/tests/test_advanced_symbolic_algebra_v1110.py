from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v1110_status():
    data = client.get("/v1110/status").json()
    assert data["ok"] is True
    assert data["version"] == "11.1.0"
    assert data["engine"] == "sympy"
    assert data["wordpressRequired"] is False
    assert data["capabilities"]["calculationObjectExtension"] is True


def test_expand_and_factor():
    expand = client.post("/calculation-engine/v1/symbolic/algebra", json={
        "expression": "(x + 1)**3",
        "variable": "x",
        "operation": "expand",
    }).json()
    assert expand["result"] == "x**3 + 3*x**2 + 3*x + 1"

    factor = client.post("/calculation-engine/v1/symbolic/algebra", json={
        "expression": "x**2 - 1",
        "variable": "x",
        "operation": "factor",
    }).json()
    assert factor["result"] == "(x - 1)*(x + 1)"


def test_rational_algebra():
    cancel = client.post("/calculation-engine/v1/symbolic/algebra", json={
        "expression": "(x**2 - 1)/(x - 1)",
        "variable": "x",
        "operation": "cancel",
    }).json()
    assert cancel["result"] == "x + 1"

    together = client.post("/calculation-engine/v1/symbolic/algebra", json={
        "expression": "1/x + 1/(x + 1)",
        "variable": "x",
        "operation": "together",
    }).json()
    assert "x*(x + 1)" in together["result"]


def test_polynomial_intelligence():
    roots = client.post("/calculation-engine/v1/symbolic/algebra", json={
        "expression": "x**3 - x",
        "variable": "x",
        "operation": "roots",
    }).json()
    assert roots["result"]["-1"] == 1
    assert roots["result"]["0"] == 1
    assert roots["result"]["1"] == 1

    coeff = client.post("/calculation-engine/v1/symbolic/algebra", json={
        "expression": "2*x**3 - 4*x + 7",
        "variable": "x",
        "operation": "coefficients",
    }).json()
    assert coeff["result"] == ["2", "0", "-4", "7"]


def test_identity_check():
    data = client.post("/calculation-engine/v1/symbolic/algebra", json={
        "expression": "(x + 1)**2 = x**2 + 2*x + 1",
        "variable": "x",
        "operation": "identity-check",
    }).json()
    assert data["result"] is True
    assert data["details"]["simplifiedDifference"] == "0"


def test_symbolic_system():
    data = client.post("/calculation-engine/v1/symbolic/algebra", json={
        "expression": "x + y = 5",
        "variables": ["x", "y"],
        "operation": "solve-system",
        "equations": ["x + y = 5", "x - y = 1"],
    }).json()
    assert data["result"] == [{"x": "3", "y": "2"}]


def test_calculation_object_extension():
    payload = {
        "calculationObjectRequest": {
            "calculation": {
                "operation": "simplify",
                "expression": "(x**2 - 1)/(x - 1)",
                "variable": "x"
            },
            "assumptions": [{"symbol": "x", "assumption": "real"}],
            "domain": "real",
            "requestedResultType": "symbolic"
        },
        "symbolicAlgebra": {
            "expression": "(x**2 - 1)/(x - 1)",
            "variable": "x",
            "operation": "cancel"
        }
    }
    data = client.post(
        "/calculation-engine/v1/symbolic/calculation-object",
        json=payload
    ).json()
    assert data["ok"] is True
    assert data["extensions"]["symbolicAlgebra"]["result"] == "x + 1"
    assert data["result"]["symbolicAlgebra"] == "x + 1"
    assert data["executionPlan"]["symbolicAlgebra"]["engine"] == "sympy"
    assert data["calculationObjectHash"]

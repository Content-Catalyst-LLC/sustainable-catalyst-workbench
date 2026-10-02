from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v1120_status():
    data = client.get("/v1120/status").json()
    assert data["ok"] is True
    assert data["version"] == "11.2.0"
    assert data["engine"] == "sympy"
    assert data["wordpressRequired"] is False
    assert data["capabilities"]["partialDerivatives"] is True


def test_higher_order_derivative():
    data = client.post("/calculation-engine/v1/calculus", json={
        "expression": "x**5",
        "operation": "differentiate",
        "variable": "x",
        "order": 3,
    }).json()
    assert data["result"] == "60*x**2"
    assert data["details"]["order"] == 3


def test_partial_derivative():
    data = client.post("/calculation-engine/v1/calculus", json={
        "expression": "x**2*y + sin(y)",
        "operation": "partial-derivative",
        "variable": "x",
        "variables": ["x", "y"],
        "orders": {"x": 1, "y": 1},
    }).json()
    assert data["result"] == "2*x"


def test_definite_integral():
    data = client.post("/calculation-engine/v1/calculus", json={
        "expression": "x**2",
        "operation": "definite-integral",
        "variable": "x",
        "lower": 0,
        "upper": 3,
    }).json()
    assert data["result"] == "9"
    assert data["details"]["bounds"] == ["0", "3"]


def test_limit():
    data = client.post("/calculation-engine/v1/calculus", json={
        "expression": "sin(x)/x",
        "operation": "limit",
        "variable": "x",
        "point": 0,
    }).json()
    assert data["result"] == "1"


def test_taylor():
    data = client.post("/calculation-engine/v1/calculus", json={
        "expression": "exp(x)",
        "operation": "taylor",
        "variable": "x",
        "expansionPoint": 0,
        "seriesOrder": 5,
    }).json()
    assert data["result"] == "x**4/24 + x**3/6 + x**2/2 + x + 1"


def test_extrema():
    data = client.post("/calculation-engine/v1/calculus", json={
        "expression": "x**2 - 4*x + 1",
        "operation": "extrema",
        "variable": "x",
    }).json()
    assert data["result"][0]["point"] == "2"
    assert data["result"][0]["value"] == "-3"
    assert data["result"][0]["classification"] == "local-minimum"


def test_calculus_calculation_object_extension():
    payload = {
        "calculationObjectRequest": {
            "calculation": {
                "operation": "differentiate",
                "expression": "x**3",
                "variable": "x"
            },
            "domain": "real",
            "requestedResultType": "symbolic"
        },
        "calculus": {
            "expression": "x**3",
            "operation": "differentiate",
            "variable": "x",
            "order": 2
        }
    }
    data = client.post(
        "/calculation-engine/v1/calculus/calculation-object",
        json=payload
    ).json()
    assert data["ok"] is True
    assert data["extensions"]["calculus"]["result"] == "6*x"
    assert data["result"]["calculus"] == "6*x"
    assert data["executionPlan"]["calculus"]["engine"] == "sympy"
    assert data["provenance"]["calculusResultHash"]
    assert data["calculationObjectHash"]

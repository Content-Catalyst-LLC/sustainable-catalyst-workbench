from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v1130_status():
    data = client.get("/v1130/status").json()
    assert data["ok"] is True
    assert data["version"] == "11.3.0"
    assert data["wordpressRequired"] is False
    assert data["capabilities"]["residualDiagnostics"] is True


def test_exact_equation():
    data = client.post("/calculation-engine/v1/solver", json={
        "operation": "solve-exact",
        "equation": "x**2 = 4",
        "variable": "x",
        "domain": "real",
    }).json()
    assert data["result"] == "{-2, 2}"


def test_numeric_equation_with_residual():
    data = client.post("/calculation-engine/v1/solver", json={
        "operation": "solve-numeric",
        "equation": "cos(x) = x",
        "variable": "x",
        "initialGuess": 0.7,
    }).json()
    assert data["method"] == "sympy-nsolve"
    assert data["verification"]["residualAcceptable"] is True


def test_symbolic_system_verification():
    data = client.post("/calculation-engine/v1/solver", json={
        "operation": "solve-system",
        "equations": ["x + y = 5", "x - y = 1"],
        "variables": ["x", "y"],
    }).json()
    assert data["result"] == [{"x": "3", "y": "2"}]
    assert data["verification"]["allResidualsZero"] is True


def test_inequality():
    data = client.post("/calculation-engine/v1/solver", json={
        "operation": "solve-inequality",
        "equation": "x**2 < 4",
        "variable": "x",
    }).json()
    assert "Interval.open(-2, 2)" in data["result"]


def test_root_isolation():
    data = client.post("/calculation-engine/v1/solver", json={
        "operation": "isolate-roots",
        "equation": "x**3 - x = 0",
        "variable": "x",
    }).json()
    assert len(data["result"]) == 3
    assert data["details"]["degree"] == 3


def test_solution_verification():
    data = client.post("/calculation-engine/v1/solver", json={
        "operation": "verify-solution",
        "equation": "x**2 = 9",
        "variable": "x",
        "solution": 3,
    }).json()
    assert data["result"] is True
    assert data["verification"]["residual"] == "0"


def test_solver_calculation_object_extension():
    payload = {
        "calculationObjectRequest": {
            "calculation": {
                "operation": "solve",
                "expression": "x**2 - 4",
                "variable": "x"
            },
            "domain": "real",
            "requestedResultType": "symbolic"
        },
        "solver": {
            "operation": "solve-exact",
            "equation": "x**2 = 4",
            "variable": "x",
            "domain": "real"
        }
    }
    data = client.post(
        "/calculation-engine/v1/solver/calculation-object",
        json=payload
    ).json()
    assert data["ok"] is True
    assert data["extensions"]["solverLaboratory"]["result"] == "{-2, 2}"
    assert data["result"]["solverLaboratory"] == "{-2, 2}"
    assert data["executionPlan"]["solverLaboratory"]["engine"] == "sympy"
    assert data["provenance"]["solverResultHash"]
    assert data["calculationObjectHash"]

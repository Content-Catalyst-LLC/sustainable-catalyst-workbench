from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _request():
    return {
        "calculation": {
            "operation": "differentiate",
            "expression": "x**3 + 2*x",
            "variable": "x"
        },
        "assumptions": [
            {"symbol": "x", "assumption": "real"}
        ],
        "domain": "real",
        "objective": "Differentiate polynomial",
        "requestedResultType": "symbolic",
        "requireVerification": True,
        "requireProvenance": True
    }


def test_v1100_status():
    data = client.get("/v1100/status").json()
    assert data["ok"] is True
    assert data["version"] == "11.0.0"
    assert data["wordpressRequired"] is False
    assert data["canonicalCalculationObject"] == "sc-workbench-calculation-object/1.0"
    assert data["activeRuntimes"] == ["python"]
    assert "julia" in data["reservedRuntimes"]


def test_schema_contract():
    data = client.get("/calculation-engine/v1/schema").json()
    assert data["ok"] is True
    assert data["objectType"] == "calculation"
    assert "executionPlan" in data["requiredSections"]
    assert "provenance" in data["requiredSections"]
    assert data["futureRuntimeModel"]["julia"] == "reserved"
    assert data["futureRuntimeModel"]["haskell"] == "reserved-verification"


def test_normalization_is_deterministic():
    a = client.post("/calculation-engine/v1/normalize", json=_request()).json()
    b = client.post("/calculation-engine/v1/normalize", json=_request()).json()
    assert a["normalized"]["inputHash"] == b["normalized"]["inputHash"]
    assert a["normalized"]["assumptions"][0]["symbol"] == "x"


def test_execution_plan_uses_current_canonical_runtime():
    data = client.post("/calculation-engine/v1/plan", json=_request()).json()
    plan = data["executionPlan"]
    assert plan["selectedRuntime"] == "python"
    assert plan["selectedEngine"] == "sympy"
    assert plan["methodFamily"] == "symbolic"
    assert plan["futureRuntimeSlots"]["julia"]["enabled"] is False
    assert plan["executionPlanHash"]


def test_compute_returns_calculation_object():
    data = client.post("/calculation-engine/v1/compute", json=_request()).json()
    assert data["ok"] is True
    assert data["schema"] == "sc-workbench-calculation-object/1.0"
    assert data["objectType"] == "calculation"
    assert data["result"]["value"]["expression"] == "3*x**2 + 2"
    assert data["verification"]["checks"]["executionSucceeded"] is True
    assert data["verification"]["checks"]["runtimeMatchesPlan"] is True
    assert data["provenance"]["canonicalBackend"] == "FastAPI"
    assert data["wordpressRequired"] is False
    assert data["calculationObjectHash"]


def test_calculation_object_hash_is_deterministic():
    a = client.post("/calculation-engine/v1/compute", json=_request()).json()
    b = client.post("/calculation-engine/v1/compute", json=_request()).json()
    assert a["calculationObjectHash"] == b["calculationObjectHash"]


def test_requested_future_runtime_falls_back_without_overclaiming():
    req = _request()
    req["preferredRuntime"] = "julia"
    data = client.post("/calculation-engine/v1/plan", json=req).json()
    plan = data["executionPlan"]
    assert plan["selectedRuntime"] == "python"
    assert "Julia requested but not active" in plan["runtimeNote"]

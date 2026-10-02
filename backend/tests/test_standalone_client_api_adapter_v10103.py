from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v10103_status():
    r = client.get("/v10103/status")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["version"] == "10.10.3"
    assert data["standaloneClientReady"] is True
    assert data["wordpressRequired"] is False
    assert data["clientNamespace"] == "/standalone/v1/client"


def test_client_config_is_wordpress_independent():
    data = client.get("/standalone/v1/client/config").json()
    assert data["wordpressRequired"] is False
    assert data["transport"]["wordpressNonceRequired"] is False
    assert data["clientRules"]["clientMayRunOutsideWordPress"] is True
    assert data["routes"]["compute"]["path"] == "/standalone/v1/client/compute"


def test_adapter_contract_does_not_duplicate_math_engine():
    data = client.get("/standalone/v1/client/adapter").json()
    assert data["guarantees"]["sameValidationModelsAsCanonicalRuntime"] is True
    assert data["guarantees"]["sameCalculationExecutionFunction"] is True
    assert data["guarantees"]["adapterDoesNotDuplicateMathEngine"] is True
    assert data["guarantees"]["wordPressIndependent"] is True


def test_client_compute_uses_canonical_runtime():
    r = client.post("/standalone/v1/client/compute", json={
        "operation": "exact",
        "expression": "2/3 + 1/6",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["result"]["exact"] == "5/6"
    assert data["wordpressRequired"] is False
    assert data["clientAdapter"]["kind"] == "compute"
    assert data["clientAdapter"]["namespace"] == "/standalone/v1/client"


def test_client_plan_uses_canonical_planner():
    r = client.post("/standalone/v1/client/plan", json={
        "operation": "differentiate",
        "expression": "x**2",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "sympy" in data["engines"]
    assert data["clientAdapter"]["kind"] == "plan"


def test_client_capabilities_wraps_existing_capabilities():
    r = client.get("/standalone/v1/client/capabilities")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["capabilities"]["symbolicDifferentiation"] is True
    assert data["clientAdapter"]["kind"] == "capabilities"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_v10101_status_declares_backend_authority():
    data = client.get("/v10101/status").json()
    assert data["ok"] is True
    assert data["version"] == "10.10.1"
    assert data["backendFirst"] is True
    assert data["wordpressRequired"] is False
    assert data["canonicalApplication"] == "FastAPI"
    assert data["dependencyInventoryReady"] is True
    assert data["routingIsolationReady"] is True

def test_dependency_inventory_makes_wordpress_optional():
    data = client.get("/decoupling/dependencies").json()
    assert data["backendRequired"] is True
    assert data["wordpressRequired"] is False
    wp = data["dependencyGroups"]["optionalAdapters"][0]
    assert wp["name"] == "wordpress"
    assert wp["required"] is False
    assert wp["authoritativeComputation"] is False
    assert wp["canonicalState"] is False
    assert data["stateOwnership"]["wordpressStateCanonical"] is False

def test_routing_policy_keeps_compute_in_backend():
    data = client.get("/decoupling/routes").json()
    assert data["canonicalRouteOwner"] == "backend"
    compute = next(x for x in data["backendRoutes"] if x["path"] == "/numerical/compute")
    assert compute["method"] == "POST"
    assert compute["authoritative"] is True
    assert data["isolationRules"]["wordpressMayExecuteAuthoritativeMath"] is False
    assert data["isolationRules"]["standaloneClientMayCallBackendDirectly"] is True
    assert data["migrationRules"]["newComputationRoutesMustLandInBackendFirst"] is True

def test_wordpress_adapter_contract_is_removable():
    data = client.get("/decoupling/adapters/wordpress").json()
    assert data["required"] is False
    assert data["capabilities"]["executeAuthoritativeMath"] is False
    assert data["capabilities"]["ownCanonicalRuntimeState"] is False
    assert data["removalTest"]["backendStartsWithoutWordPress"] is True
    assert data["removalTest"]["numericalComputeAvailableWithoutWordPress"] is True

def test_v10100_compute_remains_available_after_isolation_release():
    r = client.post("/numerical/compute", json={"operation": "exact", "expression": "1/3 + 1/6"})
    assert r.status_code == 200
    data = r.json()
    assert data["result"]["exact"] == "1/2"
    assert data["wordpressRequired"] is False

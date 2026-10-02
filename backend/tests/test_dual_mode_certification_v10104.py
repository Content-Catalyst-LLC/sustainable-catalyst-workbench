from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v10104_status_passes():
    r = client.get("/v10104/status")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["version"] == "10.10.4"
    assert data["certification"] == "pass"
    assert data["wordpressRequired"] is False
    assert data["standaloneCertified"] is True
    assert data["wordpressAdapterCertified"] is True


def test_dual_mode_certification_boundaries():
    data = client.get("/certification/dual-mode").json()
    assert data["ok"] is True
    assert data["modes"]["standalone"]["canonical"] is True
    assert data["modes"]["wordpressAdapter"]["canonical"] is False
    assert data["checks"]["backendCanonical"] is True
    assert data["checks"]["wordpressNotRequired"] is True
    assert data["checks"]["sameCalculationExecution"] is True
    assert data["certifiedBoundaries"]["wordpressCanBeRemovedWithoutChangingCalculationContracts"] is True


def test_route_equivalence_maps_same_backend_capabilities():
    data = client.get("/certification/dual-mode/routes").json()
    assert data["ok"] is True
    compute = next(x for x in data["mappings"] if x["capability"] == "compute")
    assert compute["standalone"]["path"] == "/standalone/v1/client/compute"
    assert compute["wordpressAdapter"]["path"] == "/wp-json/sc-workbench/v1/v10103/compute"
    assert compute["canonicalOwner"] == "backend"
    assert data["rules"]["wordpressExecutesAuthoritativeMath"] is False


def test_dual_mode_probe_uses_canonical_execution():
    data = client.get("/certification/dual-mode/probe").json()
    assert data["ok"] is True
    assert data["checks"]["exactResultStable"] is True
    assert data["checks"]["wordpressRequiredFalse"] is True
    assert data["checks"]["runtimeVersionCurrent"] is True


def test_standalone_client_compute_still_works():
    r = client.post("/standalone/v1/client/compute", json={
        "operation": "exact",
        "expression": "3/4 + 1/8",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["result"]["exact"] == "7/8"
    assert data["wordpressRequired"] is False

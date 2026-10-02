from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_v10102_status_is_standalone_ready():
    r = client.get("/v10102/status")
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert d["version"] == "10.10.2"
    assert d["standaloneReady"] is True
    assert d["wordpressRequired"] is False
    assert d["canonicalClientNamespace"] == "/standalone/v1"


def test_standalone_health_is_client_agnostic():
    d = client.get("/standalone/v1/health").json()
    assert d["ok"] is True
    assert d["readiness"] == "ready"
    assert d["authoritativeRuntime"] == "FastAPI"
    assert d["wordpressRequired"] is False
    assert d["checks"]["api"] is True
    assert d["checks"]["symbolic"] is True
    assert d["checks"]["numeric"] is True


def test_standalone_bootstrap_points_to_stable_namespace():
    d = client.get("/standalone/v1/bootstrap").json()
    assert d["canonicalClientNamespace"] == "/standalone/v1"
    assert d["wordpressRequired"] is False
    assert d["migration"]["standaloneFrontendCanLaunchWithoutWordPress"] is True
    assert d["migration"]["runtimeStateOwnedByBackend"] is True
    assert d["api"]["compute"]["path"] == "/numerical/compute"
    assert d["compatibility"]["legacyBootstrapSupported"] is True


def test_api_contract_has_stable_transport_and_breaking_change_policy():
    d = client.get("/standalone/v1/api-contract").json()
    assert d["contractVersion"] == "1.0"
    assert d["transport"]["wordpressNonceRequired"] is False
    assert d["clientRules"]["mayRunOutsideWordPress"] is True
    assert d["clientRules"]["mustNotExecuteAuthoritativeMath"] is True
    assert d["responseRules"]["breakingChangesRequireNewContractVersion"] is True
    assert d["stableRoutes"]["health"]["path"] == "/standalone/v1/health"


def test_compatibility_keeps_legacy_bootstrap_without_making_it_canonical():
    d = client.get("/standalone/v1/compatibility").json()
    legacy = d["legacyAliases"]["/standalone/bootstrap"]
    assert legacy["status"] == "supported-legacy-alias"
    assert legacy["replacement"] == "/standalone/v1/bootstrap"
    assert d["policy"]["breakingRouteChangesRequireNewNamespace"] is True


def test_v10100_legacy_bootstrap_still_works():
    r = client.get("/standalone/bootstrap")
    assert r.status_code == 200
    d = r.json()
    assert d["wordpressRequired"] is False

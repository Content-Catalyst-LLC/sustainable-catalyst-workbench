from fastapi.testclient import TestClient

from app.main import app
from app.v640 import CORE_RUNTIME_CONTRACT, SCHEMA, core_config


def client():
    return TestClient(app)


def test_health_is_core_gateway_compatible(monkeypatch):
    monkeypatch.delenv("SCWB_REQUIRE_SERVICE_TOKEN", raising=False)
    response = client().get("/health", headers={"X-Request-ID": "core-health-640"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["product"] == "workbench"
    assert body["version"] in {"6.4.0", "6.5.0", "6.6.0", "6.8.0", "6.12.0", "9.2.0"}
    assert body["coreCompatible"] is True
    assert body["runtimeContractTarget"] == CORE_RUNTIME_CONTRACT
    assert response.headers["X-Request-ID"] == "core-health-640"
    assert response.headers["X-SC-Workbench-Version"] in {"6.4.0", "6.5.0", "6.6.0", "6.8.0", "6.12.0", "9.2.0"}


def test_runtime_and_capabilities_boundaries():
    c = client()
    runtime = c.get("/runtime").json()
    caps = c.get("/capabilities").json()
    assert runtime["executionRole"] == "specialist-computation-plane"
    assert runtime["orchestrationRole"] == "platform-core"
    assert runtime["boundaries"]["coreMayExecuteWorkbenchCodeDirectly"] is False
    assert runtime["boundaries"]["workbenchMayDispatchToCoreAutomatically"] is False
    assert "platform-core-gateway-health" in caps["capabilities"]
    assert caps["coreIntegration"]["connectivityFoundation"] is True
    assert caps["coreIntegration"]["unifiedRuntimeContractAdapter"] is True


def test_core_status_never_returns_secrets(monkeypatch):
    monkeypatch.setenv("SCWB_CORE_URL", "http://platform-core:8080")
    monkeypatch.setenv("SCWB_CORE_API_KEY", "not-for-output")
    monkeypatch.setenv("SCWB_SERVICE_TOKEN", "shared-not-for-output")
    monkeypatch.setenv("SCWB_REQUIRE_SERVICE_TOKEN", "false")
    r = client().get(
        "/integration/core/status",
        headers={
            "X-Request-ID": "req-640",
            "X-SC-Gateway-Service": "workbench",
            "X-SC-Core-Version": "3.0.0",
            "X-SC-Service-Token": "shared-not-for-output",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["schema"] == SCHEMA
    assert body["configuration"]["coreUrlConfigured"] is True
    assert body["configuration"]["coreApiKeyConfigured"] is True
    assert body["configuration"]["serviceTokenConfigured"] is True
    assert body["requestContext"]["coreVersion"] == "3.0.0"
    assert body["requestContext"]["serviceTokenPresented"] is True
    encoded = r.text
    assert "not-for-output" not in encoded
    assert "shared-not-for-output" not in encoded


def test_service_token_can_be_required(monkeypatch):
    monkeypatch.setenv("SCWB_REQUIRE_SERVICE_TOKEN", "true")
    monkeypatch.setenv("SCWB_SERVICE_TOKEN", "correct-token")
    c = client()
    assert c.get("/integration/core/status").status_code == 401
    assert c.get("/integration/core/status", headers={"X-SC-Service-Token": "wrong"}).status_code == 401
    ok = c.get("/integration/core/status", headers={"X-SC-Service-Token": "correct-token"})
    assert ok.status_code == 200
    assert ok.json()["security"]["serviceTokenComparedConstantTime"] is True


def test_required_service_token_misconfiguration_is_visible(monkeypatch):
    monkeypatch.setenv("SCWB_REQUIRE_SERVICE_TOKEN", "true")
    monkeypatch.delenv("SCWB_SERVICE_TOKEN", raising=False)
    c = client()
    h = c.get("/health")
    assert h.status_code == 200
    assert h.json()["ok"] is False
    assert h.json()["readiness"] == "configuration-error"
    protected = c.get("/integration/core/status")
    assert protected.status_code == 503


def test_core_config_defaults_do_not_enable_outbound_dispatch(monkeypatch):
    for key in [
        "SCWB_CORE_URL",
        "SCWB_CORE_API_KEY",
        "SCWB_CORE_ENABLED",
        "SCWB_CORE_REQUIRED",
        "SCWB_REQUIRE_SERVICE_TOKEN",
        "SCWB_SERVICE_TOKEN",
    ]:
        monkeypatch.delenv(key, raising=False)
    cfg = core_config()
    assert cfg["coreUrlConfigured"] is False
    assert cfg["outboundDispatchEnabled"] is False

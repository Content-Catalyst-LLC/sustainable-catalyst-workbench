from fastapi.testclient import TestClient

from app.main import app


def test_code_studio_manifest_preserves_runner_boundary():
    client = TestClient(app)
    response = client.get("/code-studio/manifest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["version"] == "1.9.1"
    assert payload["phase"] == "editor-first-browser-runtime-pack"
    assert payload["execution_enabled"] is True
    assert payload["runner_contract"]["implementation"] == "go"
    assert payload["runner_contract"]["arbitrary_shell"] is False
    assert payload["safety"]["fastapi_executes_user_code"] is False


def test_health_reports_v190():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "1.9.1"

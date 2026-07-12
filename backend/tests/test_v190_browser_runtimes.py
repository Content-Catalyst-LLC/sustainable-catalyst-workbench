from fastapi.testclient import TestClient

from app.main import app


def test_browser_runtime_manifest_is_local_and_available() -> None:
    client = TestClient(app)
    response = client.get("/code-studio/manifest")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "1.9.1"
    assert payload["phase"] == "editor-first-browser-runtime-pack"
    assert payload["execution_enabled"] is True
    assert payload["execution_location"] == "visitor-browser"
    assert {item["id"] for item in payload["browser_runtimes"]} == {"javascript", "python", "r", "sql"}
    assert all(item["status"] == "available" for item in payload["browser_runtimes"])
    assert payload["safety"]["fastapi_executes_user_code"] is False
    assert payload["safety"]["wordpress_executes_user_code"] is False
    assert payload["storage"]["project_upload_default"] is False

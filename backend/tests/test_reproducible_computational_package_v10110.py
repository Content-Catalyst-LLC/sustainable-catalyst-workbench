from fastapi.testclient import TestClient

from app.main import app
from app.release import APP_VERSION

client = TestClient(app)


def _package():
    r = client.post("/computational-packages/build", json={
        "calculation": {
            "operation": "exact",
            "expression": "1/3 + 1/6"
        },
        "metadata": {
            "title": "Fraction reproducibility test",
            "author": "Sustainable Catalyst"
        }
    })
    assert r.status_code == 200
    return r.json()


def test_v10110_status():
    r = client.get("/v10110/status")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["version"] == APP_VERSION
    assert data["wordpressRequired"] is False
    assert data["capabilities"]["replayVerification"] is True


def test_package_build_captures_reproducibility_fields():
    data = _package()
    assert data["ok"] is True
    assert data["schema"] == "sc-workbench-reproducible-computational-package/1.0"
    assert data["result"]["result"]["exact"] == "1/2"
    assert data["manifest"]["calculationResultHash"] == data["result"]["calculationHash"]
    assert data["environment"]["workbenchVersion"] == APP_VERSION
    assert data["replay"]["expectedCalculationHash"] == data["result"]["calculationHash"]
    assert data["provenance"]["wordpressRequired"] is False
    assert data["packageHash"]


def test_same_request_produces_same_package_hash():
    a = _package()
    b = _package()
    assert a["packageHash"] == b["packageHash"]
    assert a["manifest"]["manifestHash"] == b["manifest"]["manifestHash"]


def test_manifest_verification():
    package = _package()
    r = client.post("/computational-packages/verify", json={
        "package": package,
        "mode": "manifest"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["checks"]["manifestHashMatches"] is True


def test_replay_verification():
    package = _package()
    r = client.post("/computational-packages/verify", json={
        "package": package,
        "mode": "replay"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["replay"]["checks"]["calculationHashMatches"] is True
    assert data["replay"]["checks"]["resultMatches"] is True


def test_tampered_manifest_fails():
    package = _package()
    package["manifest"]["calculationInputHash"] = "tampered"
    r = client.post("/computational-packages/verify", json={
        "package": package,
        "mode": "manifest"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert data["checks"]["manifestHashMatches"] is False

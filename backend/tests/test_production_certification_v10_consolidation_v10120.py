from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v10120_status_passes():
    r = client.get("/v10120/status")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["version"] == "10.12.0"
    assert data["certification"] == "pass"
    assert data["wordpressRequired"] is False
    assert data["v10Consolidated"] is True
    assert data["nextMajorProgram"] == "v11 Universal Calculation Engine"


def test_v10_release_manifest_is_consolidated():
    data = client.get("/certification/v10/releases").json()
    assert data["ok"] is True
    assert data["series"] == "10.x"
    assert data["releaseCount"] >= 17
    versions = [x["version"] for x in data["releases"]]
    assert "10.0.0" in versions
    assert "10.10.4" in versions
    assert "10.11.0" in versions
    assert "10.12.0" in versions
    assert data["consolidation"]["wordpressRequired"] is False


def test_v10_contract_consolidation():
    data = client.get("/certification/v10/contracts").json()
    assert data["ok"] is True
    assert data["canonicalBackend"] == "FastAPI"
    assert data["wordpressRequired"] is False
    assert data["contracts"]["standaloneApi"]["namespace"] == "/standalone/v1"
    assert data["contracts"]["standaloneClient"]["namespace"] == "/standalone/v1/client"
    assert data["contracts"]["numericalRuntime"]["backendFirst"] is True
    assert data["rules"]["packagesPreserveReplayAndProvenance"] is True


def test_v10_production_probe():
    data = client.get("/certification/v10/probe").json()
    assert data["ok"] is True
    assert data["checks"]["runtimeHealthReady"] is True
    assert data["checks"]["dualModeCertificationPass"] is True
    assert data["checks"]["packageReplayVerificationPass"] is True
    assert data["sample"]["exactResult"] == "4"
    assert data["sample"]["packageHash"]
    assert data["sample"]["manifestHash"]


def test_v10_production_certification_passes():
    data = client.get("/certification/v10").json()
    assert data["ok"] is True
    assert data["certification"] == "pass"
    assert all(data["checks"].values())
    assert data["certifiedArchitecture"]["standaloneApplicationReady"] is True
    assert data["certifiedArchitecture"]["wordpressAdapterOptional"] is True
    assert data["certifiedArchitecture"]["reproducibleComputationalPackagesReady"] is True
    assert data["certifiedArchitecture"]["v10SeriesConsolidated"] is True

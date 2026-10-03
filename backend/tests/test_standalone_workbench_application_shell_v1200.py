from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v1200/status").json()
    assert d["version"]=="12.0.0"
    assert d["applicationMode"]=="standalone-primary"
    assert d["wordpressRequired"] is False
    assert d["capabilities"]["standaloneApplicationShell"] is True

def test_manifest():
    d=client.get("/standalone/v1/app-manifest").json()
    assert d["ok"] is True
    m=d["manifest"]
    assert m["version"]=="12.0.0"
    assert m["canonicalBackend"]=="FastAPI"
    assert m["wordpressRequired"] is False
    assert m["shell"]["calculatorRoute"]=="/calculator"
    assert m["manifestHash"]

def test_routes():
    d=client.get("/standalone/v1/app-routes").json()
    assert d["ok"] is True
    r=d["routeRegistry"]
    assert r["defaultRoute"]=="/calculator"
    paths=[x["path"] for x in r["routes"]]
    assert "/calculator" in paths
    assert "/graphs" in paths
    assert "/settings" in paths

def test_shell_contract():
    d=client.get("/standalone/v1/app-shell").json()
    assert d["ok"] is True
    s=d["shell"]
    assert s["architecture"]["wordpressRequired"] is False
    assert s["architecture"]["directBackendApi"] is True
    assert s["architecture"]["authoritativeComputationInBrowser"] is False
    assert "/standalone/v1/bootstrap" in s["startup"]["requiredChecks"]

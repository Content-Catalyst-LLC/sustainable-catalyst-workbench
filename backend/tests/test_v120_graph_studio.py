from fastapi.testclient import TestClient
from app.main import app
from app.engines.graph_studio_engine import graph_studio_analyzer

client = TestClient(app)


def test_graph_studio_engine_detects_sliders_and_graphs():
    res = graph_studio_analyzer({"input": "y = a*sin(b*x)", "variable": "x", "x_min": -3.14, "x_max": 3.14, "parameters": {"a": 2, "b": 3}})
    assert res["ok"] is True
    assert res["tool"] == "Graph Studio"
    assert res["graphs"]
    assert "svg" in res["graphs"][0]
    controls = res["graph_controls"]["parameters"]
    names = {c["name"] for c in controls}
    assert {"a", "b"}.issubset(names)
    assert res["values"]["parameters"]["a"] == 2
    assert res["values"]["parameters"]["b"] == 3


def test_graph_studio_api_endpoint():
    response = client.post("/graph/studio", json={"input": "f(x)=A*exp(-k*x)*sin(omega*x)", "parameters": {"A": 2, "k": 0.2, "omega": 1.5}})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["graphs"]
    names = {c["name"] for c in data["graph_controls"]["parameters"]}
    assert {"A", "k", "omega"}.issubset(names)

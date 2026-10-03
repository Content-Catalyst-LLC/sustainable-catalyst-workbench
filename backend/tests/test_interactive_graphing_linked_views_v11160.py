from fastapi.testclient import TestClient
import math
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v11160/status").json()
    assert d["version"]=="11.16.0"
    assert d["capabilities"]["rendererNeutralViewSpec"] is True
    assert d["capabilities"]["linkedZoomPanSelection"] is True

def test_function_plot():
    d=client.post("/calculation-engine/v1/graphing",json={
        "operation":"function-plot",
        "expression":"x**2-1",
        "domain":[-2,2],
        "samples":101
    }).json()
    assert d["result"]["viewCount"]>=1
    view=d["result"]["views"][0]
    assert view["kind"]=="cartesian-function"
    assert len(view["series"][0]["x"])==101
    roots=d["verification"]["rootsOnDomain"]
    assert any(abs(r+1)<1e-8 for r in roots)
    assert any(abs(r-1)<1e-8 for r in roots)

def test_linked_function_study():
    d=client.post("/calculation-engine/v1/graphing",json={
        "operation":"linked-function-study",
        "expression":"x**3-3*x",
        "domain":[-3,3],
        "samples":121,
        "includeDerivative":True,
        "includeIntegral":True,
        "linkGroup":"study-a"
    }).json()
    kinds=[v["kind"] for v in d["result"]["views"]]
    assert "cartesian-function" in kinds
    assert "derivative" in kinds
    assert "accumulated-integral" in kinds
    assert "linked-table" in kinds
    assert all(v["linkGroup"]=="study-a" for v in d["result"]["views"])

def test_parametric_circle():
    d=client.post("/calculation-engine/v1/graphing",json={
        "operation":"parametric-plot",
        "expression":"cos(t)",
        "expressionY":"sin(t)",
        "parameter":"t",
        "domain":[0,6.283185307179586],
        "samples":101
    }).json()
    s=d["result"]["views"][0]["series"][0]
    assert abs(s["x"][0]-1.0)<1e-12
    assert abs(s["y"][0])<1e-12

def test_polar_circle():
    d=client.post("/calculation-engine/v1/graphing",json={
        "operation":"polar-plot",
        "expression":"2",
        "parameter":"t",
        "domain":[0,6.283185307179586],
        "samples":101
    }).json()
    s=d["result"]["views"][0]["series"][0]
    assert abs(s["radius"][0]-2.0)<1e-12
    assert abs(s["x"][0]-2.0)<1e-12

def test_implicit_field():
    d=client.post("/calculation-engine/v1/graphing",json={
        "operation":"implicit-field",
        "expression":"x**2+y**2-1",
        "domain":[-2,2],
        "yDomain":[-2,2],
        "gridSize":51
    }).json()
    assert d["verification"]["gridShape"]==[51,51]
    view=d["result"]["views"][0]
    assert view["field"]["contourLevel"]==0.0

def test_calculation_object_visualizations():
    payload={
      "calculationObjectRequest":{
        "calculation":{"operation":"evaluate","expression":"1"},
        "requestedResultType":"numeric"
      },
      "graphing":{
        "operation":"function-plot",
        "expression":"sin(x)",
        "domain":[0,6.283185307179586],
        "samples":101
      }
    }
    d=client.post("/calculation-engine/v1/graphing/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["extensions"]["mathematicalViews"]["engine"]=="sympy-numpy-linked-view-spec"
    assert len(d["visualizations"])>=1
    assert d["executionPlan"]["mathematicalViews"]["operation"]=="function-plot"
    assert d["provenance"]["mathematicalViewsResultHash"]

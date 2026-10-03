from fastapi.testclient import TestClient
import math
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v11110/status").json()
    assert d["version"]=="11.11.0"
    assert d["capabilities"]["rootMethodComparison"] is True
    assert "adaptive-quad" in d["methods"]

def test_root_study():
    d=client.post("/calculation-engine/v1/numerical-analysis",json={
        "operation":"root-study",
        "expression":"x**2-2",
        "variable":"x",
        "bracket":[1,2],
        "initialGuess":1.5,
        "secondGuess":2.0,
        "tolerance":1e-12
    }).json()
    methods=d["result"]["methods"]
    for name in ["bisection","brentq","newton","secant"]:
        assert methods[name]["converged"] is True
        assert abs(methods[name]["root"]-math.sqrt(2)) < 1e-9

def test_differentiation():
    d=client.post("/calculation-engine/v1/numerical-analysis",json={
        "operation":"differentiate","expression":"sin(x)","point":0.3,"step":1e-5
    }).json()
    assert abs(d["result"]["central"]-math.cos(0.3)) < 1e-9
    assert d["verification"]["centralImprovesFirstOrderAtSmallStep"] is True

def test_integration():
    d=client.post("/calculation-engine/v1/numerical-analysis",json={
        "operation":"integrate","expression":"sin(x)","interval":[0,3.141592653589793],
        "samples":101,"exactValue":2.0
    }).json()
    assert abs(d["result"]["adaptiveQuad"]-2.0) < 1e-10
    assert d["result"]["absoluteErrors"]["simpson"] < d["result"]["absoluteErrors"]["trapezoid"]

def test_interpolation():
    d=client.post("/calculation-engine/v1/numerical-analysis",json={
        "operation":"interpolate",
        "xValues":[0,1,2],
        "yValues":[0,1,4],
        "evaluationPoints":[1.5]
    }).json()
    assert abs(d["result"]["polynomial"][0]-2.25) < 1e-12
    assert d["verification"]["interpolatesNodes"] is True

def test_convergence_study():
    d=client.post("/calculation-engine/v1/numerical-analysis",json={
        "operation":"convergence-study",
        "expression":"sin(x)",
        "point":0.3,
        "steps":[0.1,0.05,0.025,0.0125]
    }).json()
    assert d["result"]["meanObservedOrder"] > 1.8

def test_conditioning():
    d=client.post("/calculation-engine/v1/numerical-analysis",json={
        "operation":"conditioning","matrix":[[1,0],[0,1e-8]]
    }).json()
    assert abs(d["result"]["conditionNumber2"]-1e8) < 1e2
    assert d["verification"]["finiteConditionNumber"] is True

def test_calculation_object():
    payload={
      "calculationObjectRequest":{
        "calculation":{"operation":"evaluate","expression":"1"},
        "requestedResultType":"numeric"
      },
      "numericalAnalysis":{
        "operation":"differentiate",
        "expression":"x**2",
        "point":3,
        "step":1e-5
      }
    }
    d=client.post("/calculation-engine/v1/numerical-analysis/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["extensions"]["numericalAnalysis"]["engine"]=="sympy-numpy-scipy"
    assert d["executionPlan"]["numericalAnalysis"]["operation"]=="differentiate"
    assert d["provenance"]["numericalAnalysisResultHash"]

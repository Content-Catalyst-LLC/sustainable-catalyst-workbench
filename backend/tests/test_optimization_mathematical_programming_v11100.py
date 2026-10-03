from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)


def test_status():
    d=client.get("/v11100/status").json()
    assert d["ok"] is True
    assert d["version"]=="11.10.0"
    assert d["capabilities"]["mixedIntegerLinearProgramming"] is True


def test_scalar_bounded_minimize():
    d=client.post("/calculation-engine/v1/optimization",json={
        "operation":"scalar-minimize",
        "objective":"(x-3)**2 + 2",
        "variable":"x",
        "bounds":[[-10,10]]
    }).json()
    assert d["result"]["success"] is True
    assert abs(d["result"]["solution"]["x"]-3.0)<1e-6
    assert abs(d["result"]["objectiveValue"]-2.0)<1e-8


def test_multivariate_minimize():
    d=client.post("/calculation-engine/v1/optimization",json={
        "operation":"multivariate-minimize",
        "objective":"(x-2)**2 + (y+1)**2",
        "variables":["x","y"],
        "initialGuess":[0,0]
    }).json()
    assert d["result"]["success"] is True
    assert abs(d["result"]["solution"]["x"]-2.0)<1e-5
    assert abs(d["result"]["solution"]["y"]+1.0)<1e-5


def test_constrained_minimize():
    d=client.post("/calculation-engine/v1/optimization",json={
        "operation":"constrained-minimize",
        "objective":"x**2 + y**2",
        "variables":["x","y"],
        "initialGuess":[0.5,0.5],
        "constraints":[{"kind":"eq","expression":"x+y-1"}]
    }).json()
    assert d["result"]["success"] is True
    assert abs(d["result"]["solution"]["x"]-0.5)<1e-5
    assert abs(d["result"]["solution"]["y"]-0.5)<1e-5
    assert d["verification"]["feasible"] is True


def test_linear_program():
    d=client.post("/calculation-engine/v1/optimization",json={
        "operation":"linear-program",
        "coefficients":[3,2],
        "variables":["x","y"],
        "sense":"maximize",
        "A_ub":[[1,1],[1,0],[0,1]],
        "b_ub":[4,2,3],
        "bounds":[[0,None],[0,None]]
    }).json()
    assert d["result"]["success"] is True
    assert abs(d["result"]["objectiveValue"]-10.0)<1e-8


def test_mixed_integer_program():
    d=client.post("/calculation-engine/v1/optimization",json={
        "operation":"mixed-integer-linear-program",
        "coefficients":[5,4],
        "variables":["x","y"],
        "sense":"maximize",
        "A_ub":[[6,4]],
        "b_ub":[24],
        "bounds":[[0,1],[0,1]],
        "integrality":[1,1]
    }).json()
    assert d["result"]["success"] is True
    assert abs(d["result"]["objectiveValue"]-9.0)<1e-8
    assert d["verification"]["integerVariablesIntegral"] is True


def test_gradient_hessian():
    d=client.post("/calculation-engine/v1/optimization",json={
        "operation":"symbolic-gradient-hessian",
        "objective":"x**2 + x*y + 3*y**2",
        "variables":["x","y"]
    }).json()
    assert d["result"]["gradient"]==["2*x + y","x + 6*y"]
    assert d["result"]["hessian"]==[["2","1"],["1","6"]]


def test_calculation_object():
    payload={
      "calculationObjectRequest":{
        "calculation":{"operation":"evaluate","expression":"1"},
        "requestedResultType":"numeric"
      },
      "optimization":{
        "operation":"scalar-minimize",
        "objective":"(x-3)**2",
        "variable":"x",
        "bounds":[[-10,10]]
      }
    }
    d=client.post("/calculation-engine/v1/optimization/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["extensions"]["optimization"]["engine"]=="sympy-scipy-optimize"
    assert d["executionPlan"]["optimization"]["operation"]=="scalar-minimize"
    assert d["provenance"]["optimizationResultHash"]

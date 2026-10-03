from fastapi.testclient import TestClient
import math
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v11150/status").json()
    assert d["version"]=="11.15.0"
    assert d["capabilities"]["covarianceAwarePropagation"] is True
    assert d["capabilities"]["seededMonteCarlo"] is True

def test_first_order_independent():
    d=client.post("/calculation-engine/v1/uncertainty",json={
        "operation":"first-order-independent",
        "expression":"x*y",
        "variables":["x","y"],
        "means":[10,2],
        "standardDeviations":[0.5,0.1]
    }).json()
    # var=(y*sx)^2 + (x*sy)^2 = (2*.5)^2 + (10*.1)^2 = 2
    assert abs(d["result"]["nominalValue"]-20.0)<1e-12
    assert abs(d["result"]["outputVariance"]-2.0)<1e-12
    assert abs(d["result"]["outputStandardDeviation"]-math.sqrt(2))<1e-12

def test_first_order_covariance():
    d=client.post("/calculation-engine/v1/uncertainty",json={
        "operation":"first-order-covariance",
        "expression":"x+y",
        "variables":["x","y"],
        "means":[1,2],
        "covarianceMatrix":[[1,0.5],[0.5,4]]
    }).json()
    assert abs(d["result"]["outputVariance"]-6.0)<1e-12

def test_seeded_monte_carlo_is_reproducible():
    payload={
        "operation":"monte-carlo",
        "expression":"x+y",
        "inputs":[
            {"name":"x","mean":10,"standardDeviation":1,"distribution":"normal"},
            {"name":"y","mean":5,"standardDeviation":0.5,"distribution":"normal"}
        ],
        "samples":5000,
        "seed":123
    }
    a=client.post("/calculation-engine/v1/uncertainty",json=payload).json()
    b=client.post("/calculation-engine/v1/uncertainty",json=payload).json()
    assert a["result"]["output"]["mean"]==b["result"]["output"]["mean"]
    assert a["result"]["output"]["standardDeviation"]==b["result"]["output"]["standardDeviation"]
    assert a["verification"]["deterministicWhenSeeded"] is True

def test_monte_carlo_summary_close_to_analytic():
    d=client.post("/calculation-engine/v1/uncertainty",json={
        "operation":"monte-carlo",
        "expression":"x+y",
        "inputs":[
            {"name":"x","mean":10,"standardDeviation":1,"distribution":"normal"},
            {"name":"y","mean":5,"standardDeviation":2,"distribution":"normal"}
        ],
        "samples":20000,
        "seed":42
    }).json()
    assert abs(d["result"]["output"]["mean"]-15.0)<0.08
    assert abs(d["result"]["output"]["standardDeviation"]-math.sqrt(5))<0.08

def test_uniform_and_triangular_sampling():
    d=client.post("/calculation-engine/v1/uncertainty",json={
        "operation":"monte-carlo",
        "expression":"u+t",
        "inputs":[
            {"name":"u","mean":0,"standardDeviation":1,"distribution":"uniform","lower":-1,"upper":1},
            {"name":"t","mean":1,"standardDeviation":0.2,"distribution":"triangular","lower":0.5,"upper":1.5,"mode":1}
        ],
        "samples":5000,
        "seed":9
    }).json()
    assert d["result"]["output"]["count"]==5000
    assert d["verification"]["finiteOutputs"] is True

def test_convergence():
    d=client.post("/calculation-engine/v1/uncertainty",json={
        "operation":"monte-carlo-convergence",
        "expression":"x**2",
        "inputs":[
            {"name":"x","mean":0,"standardDeviation":1,"distribution":"normal"}
        ],
        "samples":10000,
        "seed":77,
        "convergenceBatches":5
    }).json()
    assert len(d["result"]["convergence"])==5
    assert d["verification"]["deterministicWhenSeeded"] is True

def test_calculation_object():
    payload={
      "calculationObjectRequest":{
        "calculation":{"operation":"evaluate","expression":"1"},
        "requestedResultType":"numeric"
      },
      "uncertaintyAnalysis":{
        "operation":"first-order-independent",
        "expression":"x+y",
        "variables":["x","y"],
        "means":[1,2],
        "standardDeviations":[0.1,0.2]
      }
    }
    d=client.post("/calculation-engine/v1/uncertainty/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["extensions"]["uncertaintyPropagation"]["engine"]=="sympy-numpy-scipy-uncertainty"
    assert d["executionPlan"]["uncertaintyPropagation"]["operation"]=="first-order-independent"
    assert d["provenance"]["uncertaintyPropagationResultHash"]
    assert d["uncertainty"]["operation"]=="first-order-independent"

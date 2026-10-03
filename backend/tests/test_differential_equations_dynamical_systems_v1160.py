from fastapi.testclient import TestClient
from unittest.mock import patch
import math

from app.main import app

client=TestClient(app)


def test_v1160_status():
    d=client.get("/v1160/status").json()
    assert d["ok"] is True
    assert d["version"]=="11.6.0"
    assert d["engines"]["structuredScientificRuntime"]=="julia"
    assert d["capabilities"]["localStabilityAnalysis"] is True


def test_general_numerical_ivp_exponential_decay():
    d=client.post("/calculation-engine/v1/dynamics",json={
        "operation":"numerical-ivp",
        "equations":["-y"],
        "stateVariables":["y"],
        "initialState":[1.0],
        "timeSpan":[0.0,1.0],
        "samples":21
    }).json()
    assert d["runtime"]=="python"
    assert abs(d["result"]["finalState"][0]-math.exp(-1)) < 1e-6
    assert d["verification"]["success"] is True


def test_equilibria_and_jacobian():
    eq=client.post("/calculation-engine/v1/dynamics",json={
        "operation":"equilibria",
        "equations":["x*(1-x)"],
        "stateVariables":["x"]
    }).json()
    assert {"x":"0"} in eq["result"]
    assert {"x":"1"} in eq["result"]

    j=client.post("/calculation-engine/v1/dynamics",json={
        "operation":"jacobian",
        "equations":["x*(1-x)"],
        "stateVariables":["x"]
    }).json()
    assert j["result"]==[["1 - 2*x"]]


def test_local_stability():
    d=client.post("/calculation-engine/v1/dynamics",json={
        "operation":"stability",
        "equations":["x*(1-x)"],
        "stateVariables":["x"],
        "equilibriumPoint":[1.0]
    }).json()
    assert d["result"]["classification"]=="asymptotically-stable"


def test_julia_fallback_is_recorded():
    with patch("app.v1160._julia_binary",return_value=None):
        d=client.post("/calculation-engine/v1/dynamics",json={
            "operation":"julia-ivp",
            "model":"exponential-decay",
            "initialState":[1.0],
            "parameters":{"rate":1.0},
            "timeSpan":[0.0,1.0],
            "samples":11,
            "allowPythonFallback":True
        }).json()
    assert d["runtime"]=="python"
    assert d["fallback"] is True
    assert d["fallbackReason"]


def test_strict_julia_refuses_silent_fallback():
    with patch("app.v1160._julia_binary",return_value=None):
        r=client.post("/calculation-engine/v1/dynamics",json={
            "operation":"julia-ivp",
            "model":"exponential-decay",
            "initialState":[1.0],
            "parameters":{"rate":1.0},
            "allowPythonFallback":False
        })
    assert r.status_code==503


def test_calculation_object_extension():
    payload={
      "calculationObjectRequest":{
        "calculation":{
            "operation":"ode",
            "expression":"-y",
            "variable":"t",
            "variables":["y"],
            "initialState":[1.0],
            "timeSpan":[0.0,1.0]
        },
        "preferredRuntime":"julia",
        "requestedResultType":"timeseries"
      },
      "dynamics":{
        "operation":"numerical-ivp",
        "equations":["-y"],
        "stateVariables":["y"],
        "initialState":[1.0],
        "timeSpan":[0.0,1.0],
        "samples":11
      }
    }
    d=client.post("/calculation-engine/v1/dynamics/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert "dynamicalSystems" in d["extensions"]
    assert d["executionPlan"]["dynamicalSystems"]["engine"]=="scipy"
    assert d["provenance"]["dynamicalSystemsResultHash"]
    assert d["calculationObjectHash"]

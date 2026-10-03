from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.v1150 import JuliaExecutionRequest, execute_julia, runtime_contract

client=TestClient(app)

def test_v1150_status_contract():
    d=client.get("/v1150/status").json()
    assert d["ok"] is True and d["version"]=="11.5.0"
    assert d["wordpressRequired"] is False
    assert d["capabilities"]["juliaExecutionTarget"] is True

def test_runtime_contract_structured_not_arbitrary():
    d=runtime_contract()
    assert d["runtime"]=="julia" and d["orchestrator"]=="python"
    assert d["arbitraryCodeExecution"] is False
    assert d["structuredKernelOnly"] is True
    assert "linear-solve" in d["supportedOperations"]

def test_python_fallback_explicit_and_hashed():
    with patch("app.v1150._julia_binary", return_value=None):
        d=execute_julia(JuliaExecutionRequest(operation="vector-dot",
            vectorA=[1,2,3],vectorB=[4,5,6],allowPythonFallback=True))
    assert d["result"]==32.0
    assert d["requestedRuntime"]=="julia" and d["selectedRuntime"]=="python"
    assert d["fallback"] is True and d["fallbackReason"] and d["executionHash"]

def test_strict_julia_refuses_silent_fallback():
    with patch("app.v1150._julia_binary", return_value=None):
        r=client.post("/calculation-engine/v1/runtimes/julia/execute",json={
            "operation":"vector-dot","vectorA":[1,2],"vectorB":[3,4],
            "allowPythonFallback":False})
    assert r.status_code==503

def test_statistics_fallback_sample_std():
    with patch("app.v1150._julia_binary", return_value=None):
        d=execute_julia(JuliaExecutionRequest(operation="statistics",
            vectorA=[1,2,3,4],allowPythonFallback=True))
    assert d["result"]["mean"]==2.5
    assert round(d["result"]["std"],12)==round(1.2909944487358056,12)

def test_calculation_object_records_runtime_provenance():
    payload={
      "calculationObjectRequest":{
        "calculation":{"operation":"matrix","matrix":[[1,0],[0,1]],"matrixOperation":"det"},
        "preferredRuntime":"julia","requestedResultType":"matrix"},
      "julia":{"operation":"vector-dot","vectorA":[1,2],"vectorB":[3,4],
               "allowPythonFallback":True}}
    with patch("app.v1150._julia_binary", return_value=None):
        d=client.post("/calculation-engine/v1/runtimes/julia/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["extensions"]["juliaRuntime"]["result"]==11.0
    assert d["executionPlan"]["juliaRuntime"]["requestedRuntime"]=="julia"
    assert d["executionPlan"]["juliaRuntime"]["fallback"] is True
    assert d["provenance"]["juliaExecutionHash"]
    assert d["provenance"]["juliaRuntimeIdentityHash"]

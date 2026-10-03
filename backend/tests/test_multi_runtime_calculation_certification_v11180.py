from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v11180/status").json()
    assert d["version"]=="11.18.0"
    assert d["capabilities"]["normalizedCrossRuntimeComparison"] is True
    assert d["capabilities"]["fallbackDetection"] is True

def test_vector_dot_contract_compatible():
    d=client.post("/calculation-engine/v1/runtime-certification",json={
        "operation":"vector-dot",
        "vectorA":[1,2,3],
        "vectorB":[4,5,6],
        "requireNativeJulia":False
    }).json()
    c=d["certificate"]
    assert c["contractCompatible"] is True
    assert c["runtimes"]["python"]["result"]==32.0
    assert c["comparison"]["divergences"]==[]

def test_matrix_multiply_contract_compatible():
    d=client.post("/calculation-engine/v1/runtime-certification",json={
        "operation":"matrix-multiply",
        "matrixA":[[1,2],[3,4]],
        "matrixB":[[5,6],[7,8]],
        "requireNativeJulia":False
    }).json()
    c=d["certificate"]
    assert c["contractCompatible"] is True
    assert c["runtimes"]["python"]["result"]==[[19.0,22.0],[43.0,50.0]]

def test_linear_solve_contract_compatible():
    d=client.post("/calculation-engine/v1/runtime-certification",json={
        "operation":"linear-solve",
        "matrixA":[[3,1],[1,2]],
        "vectorA":[9,8],
        "requireNativeJulia":False,
        "absoluteTolerance":1e-9,
        "relativeTolerance":1e-9
    }).json()
    c=d["certificate"]
    assert c["contractCompatible"] is True
    x=c["runtimes"]["python"]["result"]
    assert abs(x[0]-2.0)<1e-10
    assert abs(x[1]-3.0)<1e-10

def test_statistics_contract_compatible():
    d=client.post("/calculation-engine/v1/runtime-certification",json={
        "operation":"statistics",
        "vectorA":[1,2,3,4,5],
        "requireNativeJulia":False
    }).json()
    c=d["certificate"]
    assert c["contractCompatible"] is True
    assert c["runtimes"]["python"]["result"]["mean"]==3.0
    assert c["comparison"]["divergences"]==[]

def test_native_julia_flag_is_explicit():
    d=client.post("/calculation-engine/v1/runtime-certification",json={
        "operation":"vector-dot",
        "vectorA":[1,2],
        "vectorB":[3,4],
        "requireNativeJulia":False
    }).json()
    c=d["certificate"]
    if c["fallbackUsed"]:
        assert c["crossRuntimeCertified"] is False
        assert c["certificationStatus"]=="compatible-fallback-observed"
    else:
        assert c["nativeJuliaExecuted"] is True
        assert c["crossRuntimeCertified"] is True
        assert c["certificationStatus"]=="certified"

def test_calculation_object_extension():
    payload={
      "calculationObjectRequest":{
        "calculation":{"operation":"evaluate","expression":"1"},
        "requestedResultType":"numeric"
      },
      "certification":{
        "operation":"vector-dot",
        "vectorA":[1,2,3],
        "vectorB":[4,5,6],
        "requireNativeJulia":False
      }
    }
    d=client.post("/calculation-engine/v1/runtime-certification/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["extensions"]["multiRuntimeCertification"]["operation"]=="vector-dot"
    assert d["verification"]["multiRuntimeCertification"]["contractCompatible"] is True
    assert d["provenance"]["multiRuntimeCertificationHash"]
    assert d["reproducibility"]["multiRuntimeCertification"]["certificateHash"]

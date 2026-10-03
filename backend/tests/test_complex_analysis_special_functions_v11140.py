from fastapi.testclient import TestClient
import math
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v11140/status").json()
    assert d["version"]=="11.14.0"
    assert d["capabilities"]["residues"] is True
    assert "besselj" in d["specialFunctions"]

def test_polar_and_roots():
    p=client.post("/calculation-engine/v1/complex-analysis",json={
        "operation":"polar-form","valueReal":1,"valueImag":1
    }).json()
    assert abs(p["result"]["magnitude"]-math.sqrt(2))<1e-12

    r=client.post("/calculation-engine/v1/complex-analysis",json={
        "operation":"complex-roots","valueReal":-1,"valueImag":0,"rootDegree":2
    }).json()
    assert r["verification"]["allRootsReconstruct"] is True
    assert len(r["result"]["roots"])==2

def test_residue():
    d=client.post("/calculation-engine/v1/complex-analysis",json={
        "operation":"residue","expression":"1/(z-1)","variable":"z",
        "centerReal":1,"centerImag":0
    }).json()
    assert d["result"]["residueExact"]=="1"

def test_zeros_poles():
    d=client.post("/calculation-engine/v1/complex-analysis",json={
        "operation":"zeros-poles","expression":"(z-2)/(z**2+1)","variable":"z"
    }).json()
    assert "2" in d["result"]["zeros"]
    assert "I" in " ".join(d["result"]["poles"])

def test_special_gamma_zeta():
    g=client.post("/calculation-engine/v1/complex-analysis",json={
        "operation":"special-function","specialFunction":"gamma",
        "valueReal":5,"valueImag":0,"precisionDigits":60
    }).json()
    assert abs(g["result"]["value"]["real"]-24.0)<1e-12

    z=client.post("/calculation-engine/v1/complex-analysis",json={
        "operation":"special-function","specialFunction":"zeta",
        "valueReal":2,"valueImag":0,"precisionDigits":60
    }).json()
    assert abs(z["result"]["value"]["real"]-(math.pi**2/6))<1e-12

def test_contour_integral():
    d=client.post("/calculation-engine/v1/complex-analysis",json={
        "operation":"contour-integral-circle","expression":"1/z","variable":"z",
        "centerReal":0,"centerImag":0,"radius":2,"precisionDigits":50
    }).json()
    val=d["result"]["integral"]
    assert abs(val["real"])<1e-8
    assert abs(val["imag"]-2*math.pi)<1e-8

def test_calculation_object():
    payload={
      "calculationObjectRequest":{
        "calculation":{"operation":"evaluate","expression":"1"},
        "requestedResultType":"numeric"
      },
      "complexAnalysis":{
        "operation":"special-function","specialFunction":"gamma",
        "valueReal":5,"precisionDigits":50
      }
    }
    d=client.post("/calculation-engine/v1/complex-analysis/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["extensions"]["complexAnalysis"]["engine"]=="sympy-mpmath-complex"
    assert d["executionPlan"]["complexAnalysis"]["operation"]=="special-function"
    assert d["provenance"]["complexAnalysisResultHash"]

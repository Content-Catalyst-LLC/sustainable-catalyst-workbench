from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v11130/status").json()
    assert d["version"]=="11.13.0"
    assert d["capabilities"]["chineseRemainderTheorem"] is True
    assert d["capabilities"]["recurrenceSolving"] is True

def test_gcd_lcm_and_extended():
    d=client.post("/calculation-engine/v1/discrete-math",json={
        "operation":"gcd-lcm","a":84,"b":30
    }).json()
    assert d["result"]=={"gcd":6,"lcm":420}
    e=client.post("/calculation-engine/v1/discrete-math",json={
        "operation":"extended-gcd","a":240,"b":46
    }).json()
    assert e["verification"]["bezoutIdentity"] is True
    assert e["result"]["gcd"]==2

def test_prime_factorization():
    p=client.post("/calculation-engine/v1/discrete-math",json={
        "operation":"prime-test","n":104729
    }).json()
    assert p["result"]["isPrime"] is True
    f=client.post("/calculation-engine/v1/discrete-math",json={
        "operation":"factor-integer","n":360
    }).json()
    assert f["result"]["factors"]=={"2":3,"3":2,"5":1}
    assert f["verification"]["reconstructsInput"] is True

def test_modular_arithmetic_crt():
    inv=client.post("/calculation-engine/v1/discrete-math",json={
        "operation":"modular-inverse","a":3,"modulus":11
    }).json()
    assert inv["result"]["inverse"]==4
    crt=client.post("/calculation-engine/v1/discrete-math",json={
        "operation":"crt","residues":[2,3,2],"moduli":[3,5,7]
    }).json()
    assert crt["result"]["solution"]==23
    assert crt["result"]["modulus"]==105
    assert crt["verification"]["satisfiesCongruences"] is True

def test_combinatorics_sequence():
    d=client.post("/calculation-engine/v1/discrete-math",json={
        "operation":"permutations-combinations","n":10,"k":3
    }).json()
    assert d["result"]["permutations"]==720
    assert d["result"]["combinations"]==120
    seq=client.post("/calculation-engine/v1/discrete-math",json={
        "operation":"sequence","sequenceType":"fibonacci","count":8
    }).json()
    assert seq["result"]["values"]==[0,1,1,2,3,5,8,13]

def test_recurrence():
    d=client.post("/calculation-engine/v1/discrete-math",json={
        "operation":"recurrence-solve",
        "recurrence":"Eq(a(n), a(n-1) + a(n-2))",
        "functionName":"a",
        "initialConditions":{"0":0,"1":1}
    }).json()
    assert d["verification"]["solutionFound"] is True
    assert d["result"]["closedForm"] is not None

def test_graph_properties_shortest_path_components():
    payload={
      "nodes":["A","B","C","D"],
      "edges":[["A","B"],["B","C"]],
      "directed":False
    }
    props=client.post("/calculation-engine/v1/discrete-math",json={
      "operation":"graph-properties",**payload
    }).json()
    assert props["result"]["nodeCount"]==4
    assert props["result"]["connected"] is False
    assert props["verification"]["handshakeLemma"] is True

    path=client.post("/calculation-engine/v1/discrete-math",json={
      "operation":"graph-shortest-path",**payload,"source":"A","target":"C"
    }).json()
    assert path["result"]["path"]==["A","B","C"]
    assert path["result"]["distanceEdges"]==2

    comps=client.post("/calculation-engine/v1/discrete-math",json={
      "operation":"graph-connected-components",**payload
    }).json()
    assert comps["result"]["count"]==2
    assert comps["verification"]["coversAllNodes"] is True

def test_calculation_object():
    payload={
      "calculationObjectRequest":{
        "calculation":{"operation":"evaluate","expression":"1"},
        "requestedResultType":"numeric"
      },
      "discreteMath":{
        "operation":"factor-integer","n":360
      }
    }
    d=client.post("/calculation-engine/v1/discrete-math/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["extensions"]["discreteMath"]["engine"]=="sympy-exact-discrete"
    assert d["executionPlan"]["discreteMath"]["operation"]=="factor-integer"
    assert d["provenance"]["discreteMathResultHash"]

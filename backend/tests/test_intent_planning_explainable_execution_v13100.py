from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_status():
    d=client.get("/v13100/status").json()
    assert d["version"]=="13.10.0"
    assert d["intentPlanningReady"] is True
    assert all(d["checks"].values())

def test_plan_and_validate():
    r=client.post("/standalone/v1/intent-planning/plan",json={
        "text":"differentiate x^3 + 2*x with respect to x","mode":"conservative"
    })
    assert r.status_code==200
    p=r.json()["plan"]
    assert p["intent"]=="differentiate"
    assert p["selectedCalculationRequest"]["calculation"]["operation"]=="differentiate"
    assert p["validation"]["valid"] is True
    assert p["policy"]["directPlannerExecution"] is False
    assert p["policy"]["userConfirmationRequired"] is True
    assert len(p["steps"])>=5
    assert p["planHash"]

    v=client.post("/standalone/v1/intent-planning/validate",json={"plan":p}).json()["validation"]
    assert v["valid"] is True
    assert not v["blockers"]

def test_alternatives_and_blockers():
    e=client.post("/standalone/v1/intent-planning/plan",json={
        "text":"calculate 2 + 2","mode":"conservative"
    }).json()["plan"]
    ids={x["id"] for x in e["alternatives"]}
    assert "primary" in ids
    assert "exact-alternative" in ids

    bad=client.post("/standalone/v1/intent-planning/plan",json={
        "text":"calculate 2x + 1","mode":"conservative"
    }).json()["plan"]
    assert bad["validation"]["valid"] is False
    assert "implicit-multiplication-not-expanded" in bad["validation"]["blockers"]

def test_explanation_uses_calculation_object_authority():
    p=client.post("/standalone/v1/intent-planning/plan",json={
        "text":"calculate 2 + 3 * 4","mode":"conservative"
    }).json()["plan"]
    calculation_object={
        "calculationObjectHash":"calc-123",
        "executionPlan":{"runtime":"python","method":"evaluate","solver":None,"tolerances":{}},
        "approximateResult":14,
        "verification":{"status":"passed","passed":True},
        "provenance":{"provenanceHash":"prov-123"},
    }
    r=client.post("/standalone/v1/intent-planning/explain",json={
        "plan":p,"calculationObject":calculation_object
    })
    assert r.status_code==200
    x=r.json()["explanation"]
    assert x["calculationObjectHash"]=="calc-123"
    assert x["resultSummary"]==14
    assert x["policy"]["resultAuthority"]=="CalculationObject"
    assert x["policy"]["plannerResultMutation"] is False

def test_contract_preserves_v139():
    c=client.get("/standalone/v1/intent-planning/contract").json()["planning"]
    assert c["features"]["v139InterpretationPreserved"] is True
    assert c["features"]["calculationObjectRemainsResultAuthority"] is True
    assert c["features"]["userConfirmationRequired"] is True

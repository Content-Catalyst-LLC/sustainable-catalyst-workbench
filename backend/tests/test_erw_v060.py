from copy import deepcopy
import pytest
from fastapi import HTTPException
from app.erw_v060 import VisualRequest,visual,status

def fixture():
    scenario={"schema":"sc.erw.scenario-ledger.v0.3.0","researchId":"erw-wexford-hypothetical-100ha-v0.1",
      "calculationObjectHash":"a"*64,"scenarios":[]}
    for rate in ("0","10"):
        scenario["scenarios"].append({"rateTonnesPerHa":rate,"annual":[
            {"year":year,"backgroundPotentialTonnesCO2":"2",
             "modeledScenarioPotentialTonnesCO2":"3",
             "incrementalPotentialProxyTonnesCO2":"1"} for year in (1,2)]})
    lifecycle={"researchId":scenario["researchId"],"calculationObjectHash":"b"*64,
      "sourceScenarioCalculationHash":"a"*64,
      "totalsByCategoryTonnesCO2e":{"transport":"10","quarrying":"4"},
      "totalModeledLifecycleBurdenTonnesCO2e":"14"}
    uncertainty={"schema":"sc.erw.uncertainty-mrv.v0.5.0","researchId":scenario["researchId"],
      "calculationObjectHash":"c"*64,
      "lineage":{"scenarioCalculationHash":"a"*64,"lifecycleCalculationHash":"b"*64},
      "grossTheoreticalCapacityTonnesCO2":{"low":"380","central":"600","high":"840"},
      "modeledRealizationProxyTonnesCO2":{"low":"38","central":"300","high":"756"},
      "exploratoryProxyMinusBurdenTonnes":{"low":"18","central":"286","high":"746"},
      "sensitivityOneAtATime":[{"parameter":k,"absoluteSwingTonnesCO2":"30"} for k in ("mass","fraction","capacity","burden")],
      "mrvReadiness":{"requirements":{"feedstock-assay":{"state":"planned","evidenceClass":"hypothetical"}}}}
    return VisualRequest(researchId=scenario["researchId"],scenario=scenario,lifecycle=lifecycle,
       uncertainty=uncertainty,sourceReference="Synthetic fixture")

def test_status(): assert status()["extensionVersion"]=="0.6.0"
def test_five_views():
    assert [v["id"] for v in visual(fixture())["views"]]==[
      "scenario-trajectories","lifecycle-breakdown","uncertainty-intervals",
      "sensitivity-ranking","mrv-evidence-matrix"]
def test_no_cdr():
    v=visual(fixture()); assert v["verifiedCDR"] is False and v["netDurableAtmosphericRemoval"] is None
def test_deterministic_hash():
    assert visual(fixture())["calculationObjectHash"]==visual(fixture())["calculationObjectHash"]
def test_lineage_rejected():
    f=fixture(); f.uncertainty["lineage"]["scenarioCalculationHash"]="z"*64
    with pytest.raises(HTTPException):visual(f)
def test_lifecycle_lineage_rejected():
    f=fixture(); f.lifecycle["sourceScenarioCalculationHash"]="z"*64
    with pytest.raises(HTTPException):visual(f)
def test_emissions_sum_rejected():
    f=fixture(); f.lifecycle["totalModeledLifecycleBurdenTonnesCO2e"]="16"
    with pytest.raises(HTTPException):visual(f)
def test_nonfinite_rejected():
    f=fixture(); f.lifecycle["totalsByCategoryTonnesCO2e"]["transport"]="NaN"
    with pytest.raises(HTTPException):visual(f)
def test_negative_interval_allowed_for_screening():
    f=fixture(); f.uncertainty["exploratoryProxyMinusBurdenTonnes"]["low"]="-2"
    assert visual(f)["views"][2]["intervals"][2]["low"]=="-2"
def test_out_of_order_interval_rejected():
    f=fixture(); f.uncertainty["grossTheoreticalCapacityTonnesCO2"]["low"]="900"
    with pytest.raises(HTTPException):visual(f)
def test_disordered_year_rejected():
    f=fixture(); f.scenario["scenarios"][0]["annual"][1]["year"]=3
    with pytest.raises(HTTPException):visual(f)
def test_invalid_scenario_schema_rejected():
    f=fixture(); f.scenario["schema"]="other"
    with pytest.raises(HTTPException):visual(f)
def test_sorted_emissions():
    v=visual(fixture());assert v["views"][1]["bars"][0]["category"]=="quarrying"
def test_mrv_is_categorical_only():
    v=visual(fixture()); assert v["views"][4]["cells"][0]["state"]=="planned"

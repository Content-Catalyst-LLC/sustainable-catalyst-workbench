import pytest
from fastapi import HTTPException
from app.erw_v080 import ReportRequest,compose,status,KINDS,EXPECTED
from app.erw_v010 import PROJECT_KEY

def fixture():
    h={k:(str(i)*64) for i,k in enumerate(KINDS,1)}
    o={k:{"researchId":PROJECT_KEY,"schema":EXPECTED[k],"calculationObjectHash":h[k]} for k in KINDS}
    o["scenario"]["inputs"]={"compositionCalculationHash":h["geochemistry"]}
    o["lifecycle"]["sourceScenarioCalculationHash"]=h["scenario"]
    o["uncertainty"]["lineage"]={"scenarioCalculationHash":h["scenario"],"lifecycleCalculationHash":h["lifecycle"]}
    o["visualization"].update({"sourceHashes":{k:h[k] for k in ("scenario","lifecycle","uncertainty")},
        "views":[{"id":x} for x in ("scenario-trajectories","lifecycle-breakdown","uncertainty-intervals","sensitivity-ranking","mrv-evidence-matrix")],"verifiedCDR":False})
    o["diagrams"].update({"sourceVisualHash":h["visualization"],"verifiedCDR":False,
        "equations":[{"id":str(i),"latex":"x=y"} for i in range(4)]})
    return ReportRequest(title="Hypothetical ERW research draft",authors=["Researcher"],
        sourceObjects=o,purpose="Explain hypothetical ERW study methodology.",
        sourceReference="Synthetic only")

def test_status():assert status()["publicationEnabled"] is False
def test_compose():assert compose(fixture())["schema"]=="sc.erw.academic-report.v0.8.0"
def test_seven_sections():assert len(compose(fixture())["sections"])==7
def test_five_figures():assert len(compose(fixture())["figures"])==5
def test_four_equations():assert len(compose(fixture())["equations"])==4
def test_unpublished():
    x=compose(fixture());assert x["publicationEnabled"] is False and x["status"]=="draft-unpublished"
def test_cdr_disabled():assert compose(fixture())["netDurableAtmosphericRemoval"] is None
def test_hash_deterministic():assert compose(fixture())["calculationObjectHash"]==compose(fixture())["calculationObjectHash"]
def test_six_hashes():assert len(compose(fixture())["sourceHashes"])==6
def test_source_integrity_not_claimed():assert compose(fixture())["sourceIntegrityVerified"] is False
def test_missing_source():
    f=fixture();f.sourceObjects.pop("diagrams")
    with pytest.raises(HTTPException):compose(f)
def test_scenario_mismatch():
    f=fixture();f.sourceObjects["scenario"]["inputs"]["compositionCalculationHash"]="z"*64
    with pytest.raises(HTTPException):compose(f)
def test_lifecycle_mismatch():
    f=fixture();f.sourceObjects["lifecycle"]["sourceScenarioCalculationHash"]="z"*64
    with pytest.raises(HTTPException):compose(f)
def test_visual_mismatch():
    f=fixture();f.sourceObjects["visualization"]["sourceHashes"]["scenario"]="z"*64
    with pytest.raises(HTTPException):compose(f)
def test_diagram_mismatch():
    f=fixture();f.sourceObjects["diagrams"]["sourceVisualHash"]="z"*64
    with pytest.raises(HTTPException):compose(f)
def test_verified_status_rejected():
    f=fixture();f.sourceObjects["visualization"]["verifiedCDR"]=True
    with pytest.raises(HTTPException):compose(f)
def test_bibliography():
    f=fixture();f.bibliography=[{"reference":"Synthetic source","evidenceClass":"hypothetical"}]
    assert compose(f)["bibliography"][0]["verifiedAgainstExternalSource"] is False
def test_duplicate_bibliography():
    f=fixture();f.bibliography=[{"reference":"X","evidenceClass":"hypothetical"}]*2
    with pytest.raises(HTTPException):compose(f)

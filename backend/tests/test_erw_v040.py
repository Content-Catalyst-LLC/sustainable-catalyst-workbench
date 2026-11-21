import pytest
from decimal import Decimal
from fastapi import HTTPException
from app.erw_v040 import Activity,PermanenceEvidence,LifecycleRequest,assess,status

def fixture(**overrides):
    data=dict(
      sourceScenarioCalculationHash="a"*64,studyYears=10,
      scenarioDoseTonnesPerHa="20",rockTonnes="2000",
      theoreticalUpperBoundTonnesCO2="636.2066995699716166428187670",
      activities=[
        Activity(category="quarrying",activityId="q",quantity="2000",unit="t",
          emissionsFactorKgCO2ePerUnit="2",factorUnit="kgCO2e/t",
          evidenceClass="hypothetical",sourceReference="Synthetic test factor",boundaryNote="Illustration only"),
        Activity(category="transport",activityId="t",quantity="100000",unit="tonne-km",
          emissionsFactorKgCO2ePerUnit="0.1",factorUnit="kgCO2e/tonne-km",
          evidenceClass="hypothetical",sourceReference="Synthetic test factor",boundaryNote="Illustration only"),
      ],
      permanence=PermanenceEvidence(pathway="unknown",status="unassessed",
                                    sourceReference="Unassessed Wexford hypothetical scenario"),
      assessmentSourceReference="Hypothetical demonstration")
    data.update(overrides)
    return LifecycleRequest(**data)

def test_emissions_unit_conversion():
    a=assess(fixture())
    assert a["totalModeledLifecycleBurdenTonnesCO2e"]=="14"
    assert a["lifecycleBurdenByCategoryTonnesCO2e"]=={"quarrying":"4","transport":"10"}

def test_screening_difference_not_net_removal():
    a=assess(fixture())
    assert Decimal(a["exploratoryUpperBoundMinusBurden"])==Decimal("636.2066995699716166428187670")-14
    assert a["netDurableAtmosphericRemoval"] is None
    assert a["screeningDifferenceIsNetRemoval"] is False
    assert a["additionalityDemonstrated"] is False

def test_permanence_unverified_even_when_all_evidence_flags_true():
    p=PermanenceEvidence(pathway="ocean-storage",status="site-measured",sourceReference="Hypothetical fixture",
      hydrologicalFateEstablished=True,secondaryMineralEffectsEstablished=True,
      strongAcidCorrectionsEstablished=True,longTermRetentionEstablished=True)
    a=assess(fixture(permanence=p))
    assert a["permanence"]["unresolvedGaps"]==[]
    assert a["permanence"]["verifiedDurableStorage"] is False

def test_unresolved_gaps():
    assert len(assess(fixture())["permanence"]["unresolvedGaps"])==4

def test_stable_hash():
    assert assess(fixture())["calculationObjectHash"]==assess(fixture())["calculationObjectHash"]

def test_no_negative():
    x=fixture().model_copy(deep=True)
    x.activities[0].quantity="-1"
    with pytest.raises(HTTPException):assess(x)

def test_reject_unit_mismatch():
    x=fixture().model_copy(deep=True)
    x.activities[0].factorUnit="kgCO2e/km"
    with pytest.raises(HTTPException):assess(x)

def test_duplicate_ids():
    x=fixture().model_copy(deep=True)
    x.activities[1].activityId="q"
    with pytest.raises(HTTPException):assess(x)

def test_zero_control_must_have_no_treatment():
    with pytest.raises(HTTPException):assess(fixture(scenarioDoseTonnesPerHa="0"))

def test_zero_control_accepted_with_operational_burden():
    a=assess(fixture(scenarioDoseTonnesPerHa="0",rockTonnes="0",theoreticalUpperBoundTonnesCO2="0"))
    assert a["inputs"]["theoreticalUpperBoundTonnesCO2"]=="0"
    assert a["netDurableAtmosphericRemoval"] is None

def test_status():
    assert status()["extensionVersion"]=="0.4.0"
    assert status()["verifiedCDR"] is False

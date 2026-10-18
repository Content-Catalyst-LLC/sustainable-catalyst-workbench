import pytest
from decimal import Decimal
from fastapi import HTTPException
from app.erw_v050 import Range,Evidence,UncertaintyRequest,analyze,status,REQUIREMENTS

def fixture(**kw):
    d=dict(
      scenarioCalculationHash="a"*64,lifecycleCalculationHash="b"*64,
      feedstockMassTonnes=Range(low="1900",central="2000",high="2100"),
      grossCapacityTco2PerTFeedstock=Range(low="0.2",central="0.3",high="0.4"),
      realizedFraction=Range(low="0.1",central="0.5",high="0.9"),
      lifecycleBurdenTonnesCO2e=Range(low="10",central="14",high="20"),
      evidence=[Evidence(requirement=x,state="planned",sourceReference="Synthetic MRV plan",
         evidenceClass="hypothetical",limitations="No field data") for x in REQUIREMENTS],
      assumptionsSourceReference="Synthetic uncertainty assumptions")
    d.update(kw)
    return UncertaintyRequest(**d)

def test_bound_math():
    a=analyze(fixture())
    assert a["grossTheoreticalCapacityTonnesCO2"]=={"low":"380","central":"600","high":"840"}
    assert a["modeledRealizationProxyTonnesCO2"]=={"low":"38","central":"300","high":"756"}
    assert a["exploratoryProxyMinusBurdenTonnes"]=={"low":"18","central":"286","high":"746"}

def test_not_probability_or_cdr():
    a=analyze(fixture())
    assert a["boundsKind"]=="deterministic-extreme-screening-not-probabilistic"
    assert a["netDurableAtmosphericRemoval"] is None
    assert a["mrvReadiness"]["approvedForCrediting"] is False

def test_planned_does_not_count_as_measured():
    a=analyze(fixture())
    assert len(a["mrvReadiness"]["missingOrPlanned"])==10

def test_all_reviewed_still_not_credited():
    e=[Evidence(requirement=x,state="independently-reviewed",
          sourceReference="Synthetic fixture",evidenceClass="hypothetical",
          limitations="Review status is a test assertion only") for x in REQUIREMENTS]
    a=analyze(fixture(evidence=e))
    assert a["mrvReadiness"]["notIndependentlyReviewed"]==[]
    assert a["mrvReadiness"]["approvedForCrediting"] is False

def test_duplicate_evidence_rejected():
    x=fixture()
    x.evidence.append(x.evidence[0])
    with pytest.raises(HTTPException):analyze(x)

def test_reversed_bound_rejected():
    with pytest.raises(HTTPException):analyze(fixture(realizedFraction=Range(low="0.8",central="0.5",high="0.9")))

def test_fraction_over_one_rejected():
    with pytest.raises(HTTPException):analyze(fixture(realizedFraction=Range(low="0",central="0.5",high="1.1")))

def test_nonfinite_rejected():
    with pytest.raises(HTTPException):analyze(fixture(feedstockMassTonnes=Range(low="NaN",central="2000",high="2100")))

def test_distinct_hashes_required():
    with pytest.raises(HTTPException):analyze(fixture(lifecycleCalculationHash="a"*64))

def test_sensitivity_count():
    a=analyze(fixture())
    assert len(a["sensitivityOneAtATime"])==4
    assert a["sensitivityOneAtATime"][0]["absoluteSwingTonnesCO2"]=="15"

def test_hash_deterministic():
    assert analyze(fixture())["calculationObjectHash"]==analyze(fixture())["calculationObjectHash"]

def test_status():
    assert status()["extensionVersion"]=="0.5.0"
    assert status()["approvedForCrediting"] is False

from decimal import Decimal
import pytest
from fastapi import HTTPException
from app.erw_v030 import AnnualAssumption, ScenarioRequest, model, status

HASH="a08fec3fd183a7886698796b2f21aed05d9ddf75228adc0adf8e10c6f4e3f1aa"
def req(**kw):
    data=dict(studyAreaHa="100",years=10,applicationRatesTonnesPerHa=["0","10","20"],
      upperBoundTco2PerTFeedstock="0.3181033497849858083214093835",
      compositionCalculationHash=HASH,scenarioSourceReference="Hypothetical Wexford scenarios",
      timeline=[AnnualAssumption(year=i,realizationFraction="0.1",backgroundPotentialTonnesCO2="2")
                for i in range(1,11)])
    data.update(kw)
    return ScenarioRequest(**data)

def test_three_scenarios_feedstock():
    r=model(req())
    assert [x["rockTonnes"] for x in r["scenarios"]]==["0","1000","2000"]
    assert r["scenarios"][0]["cumulativeIncrementalPotentialProxyTonnesCO2"]=="0"

def test_half_dose_is_half_proxy():
    r=model(req())
    a,b=r["scenarios"][1:]
    assert Decimal(b["cumulativeIncrementalPotentialProxyTonnesCO2"])==2*Decimal(a["cumulativeIncrementalPotentialProxyTonnesCO2"])

def test_ten_year_partition_no_double_counting():
    r=model(req())
    b=r["scenarios"][2]
    assert Decimal(b["cumulativeIncrementalPotentialProxyTonnesCO2"])==Decimal(b["grossTheoreticalUpperBoundTonnesCO2"])
    assert all(v["assumptionEvidenceClass"]=="hypothetical" for v in b["annual"])

def test_no_automatic_additionality():
    r=model(req())
    assert r["additionalityAssessment"]["demonstrated"] is False
    assert r["additionalityAssessment"]["netDurableAtmosphericRemoval"] is None
    assert status()["verifiedCDR"] is False

def test_hash_reproducible():
    assert model(req())["calculationObjectHash"]==model(req())["calculationObjectHash"]

@pytest.mark.parametrize("rates",[["10","20"],["0","0","20"]])
def test_zero_control_and_unique_rates(rates):
    with pytest.raises(HTTPException): model(req(applicationRatesTonnesPerHa=rates))

def test_timeline_must_cover_every_year():
    with pytest.raises(HTTPException): model(req(timeline=[AnnualAssumption(year=1,realizationFraction="0.1")]))

def test_fraction_cannot_double_count():
    with pytest.raises(HTTPException): model(req(timeline=[AnnualAssumption(year=i,realizationFraction="0.2") for i in range(1,11)]))

def test_negative_background_rejected():
    years=[AnnualAssumption(year=i,realizationFraction="0.1",backgroundPotentialTonnesCO2="-1" if i==1 else "0") for i in range(1,11)]
    with pytest.raises(HTTPException): model(req(timeline=years))

def test_no_preapplication_proxy():
    r=model(req(applicationYear=3,timeline=[AnnualAssumption(year=i,realizationFraction="0" if i<3 else "0.125") for i in range(1,11)]))
    assert r["scenarios"][2]["annual"][0]["incrementalPotentialProxyTonnesCO2"]=="0"

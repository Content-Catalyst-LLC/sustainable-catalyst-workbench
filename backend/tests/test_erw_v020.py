import pytest
from fastapi import HTTPException
from app.erw_v020 import Assay, PotentialRequest, calculate, status, MW_CO2, MW

def assay(**kw):
    data = dict(feedstockId="BASALT-DEMO",sampleId="SYN-001",
                compositionWtPct={"CaO":"10","MgO":"5","Na2O":"3","K2O":"1"},
                otherOxidesWtPct={"SiO2":"50","Al2O3":"15","Fe2O3":"10","TiO2":"2","other":"4"},
                sourceKind="hypothetical",sourceReference="Synthetic test fixture, NOT a published basalt assay",
                carbonateStatus="unknown",sulfatePhosphateStatus="unknown")
    data.update(kw)
    return Assay(**data)

def test_result_reference_formula_independent():
    result=calculate(PotentialRequest(assay=assay(),rockTonnes="2000"))
    expected=sum((float(v)/100)*(2*float(MW_CO2)/float(MW[k]))
                 for k,v in {"CaO":"10","MgO":"5","Na2O":"3","K2O":"1"}.items())
    assert abs(float(result["grossUpperBound"]["tCO2PerTFeedstock"])-expected)<1e-12
    assert abs(float(result["grossUpperBound"]["tCO2ForInputRockMass"])-2000*expected)<1e-9

def test_zero_oxide_is_zero_capacity():
    a=assay(compositionWtPct=dict.fromkeys(MW,"0"),otherOxidesWtPct={"other":"100"})
    assert calculate(PotentialRequest(assay=a))["grossUpperBound"]["tCO2PerTFeedstock"]=="0"

def test_missing_oxide_rejected():
    with pytest.raises(HTTPException) as e:
        calculate(PotentialRequest(assay=assay(compositionWtPct={"CaO":"10"})))
    assert e.value.status_code==422

@pytest.mark.parametrize("bad", ["-1","NaN","101","Infinity"])
def test_bad_wt_percent_rejected(bad):
    a=assay(compositionWtPct={"CaO":bad,"MgO":"5","Na2O":"3","K2O":"1"})
    with pytest.raises(HTTPException): calculate(PotentialRequest(assay=a))

def test_mass_over_100_rejected():
    a=assay(otherOxidesWtPct={"SiO2":"99"})
    with pytest.raises(HTTPException): calculate(PotentialRequest(assay=a))

def test_incomplete_assay_fails_closed_as_exploratory():
    r=calculate(PotentialRequest(assay=assay(otherOxidesWtPct={})))
    assert "bulk-assay-incomplete-or-unreported" in r["unresolvedCorrections"]
    assert r["netDurableAtmosphericRemoval"] is None
    assert r["status"]=="exploratory-gross-upper-bound"

def test_assay_provenance_hash_and_unresolved_acids():
    r=calculate(PotentialRequest(assay=assay()))
    assert r["calculationObjectHash"]==calculate(PotentialRequest(assay=assay()))["calculationObjectHash"]
    assert len(r["unresolvedCorrections"])==2
    assert status()["verifiedCDR"] is False

def test_no_literature_values_silently_implied():
    r=calculate(PotentialRequest(assay=assay()))
    assert r["assay"]["sourceKind"]=="hypothetical"
    assert "Synthetic test fixture" in r["assay"]["sourceReference"]

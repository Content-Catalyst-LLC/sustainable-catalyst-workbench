"""ERW 0.1.0 regression tests: calculations, evidence boundaries and persistence API."""
from decimal import Decimal
from fastapi import HTTPException
from app.erw_v010 import template, mass_object, finite_nonnegative, status

def test_template_marks_hypothetical_and_has_source_provenance():
    t = template()
    assert t["researchId"] == "SC-ERW-IRELAND-001"
    assert t["studyArea"]["siteStatus"] == "hypothetical"
    assert t["coreContracts"]["truthPromotion"] is False
    assert len(t["sources"]) >= 5

def test_mass_calculation_and_units():
    o = mass_object("100", "20")
    assert Decimal(o["result"]["value"]) == 2000
    assert o["result"]["unit"] == "t basalt"
    assert o["inputs"][0]["unit"] == "ha"
    assert o["inputs"][1]["unit"] == "t/ha"
    assert "CO2" in o["scientificLimit"]

def test_zero_control_and_fractional_dose():
    assert Decimal(mass_object("100", "0")["result"]["value"]) == 0
    assert Decimal(mass_object("2.5", "10.5")["result"]["value"]) == Decimal("26.25")

def test_reject_negative_nan_and_infinity():
    for v in ("-1", "NaN", "Infinity", "abc"):
        try: finite_nonnegative(v, "areaHa")
        except HTTPException as exc: assert exc.status_code == 422
        else: raise AssertionError(v)

def test_hash_deterministic_and_no_unsupported_claim():
    a = mass_object("100", "20")
    b = mass_object("100", "20")
    assert a["calculationObjectHash"] == b["calculationObjectHash"]
    assert status()["carbonRemovalCalculated"] is False

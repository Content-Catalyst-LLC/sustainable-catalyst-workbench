"""ERW 0.2.0: assay-traceable gross stoichiometric feedstock potential.

Scientific status: four-oxide carbonic-acid charge-balance *upper bound*.
Sulfate, phosphate, carbonate and acid corrections MUST NOT be silently ignored
in a decision-grade result. Uncorrected numbers are exploratory only.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import _owner, get_project, save_calculation, SavedCalculationCreateRequest
from .erw_v010 import PROJECT_KEY, finite_nonnegative

router = APIRouter(tags=["erw-0.2.0"])
# Decimal masses in g/mol. Each mole of these oxides can balance two HCO3-
# under idealized carbonic-acid silicate dissolution (not real-world CDR).
MW = {"CaO": Decimal("56.077"), "MgO": Decimal("40.304"),
      "Na2O": Decimal("61.979"), "K2O": Decimal("94.196")}
MW_CO2 = Decimal("44.0095")
OXIDES = tuple(MW)
METHOD_DOI = "10.3389/fclim.2024.1345224"
METHOD_URL = "https://www.frontiersin.org/journals/climate/articles/10.3389/fclim.2024.1345224/full"

class Assay(BaseModel):
    feedstockId: str = Field(min_length=1, max_length=120)
    sampleId: str = Field(min_length=1, max_length=160)
    compositionWtPct: Dict[str, str]
    otherOxidesWtPct: Dict[str, str] = Field(default_factory=dict)
    sourceKind: str = Field(pattern="^(laboratory|literature|hypothetical)$")
    sourceReference: str = Field(min_length=1, max_length=1200)
    carbonateStatus: str = Field(pattern="^(absent-confirmed|present|unknown)$")
    sulfatePhosphateStatus: str = Field(pattern="^(absent-confirmed|present|unknown)$")
    limitations: str = ""

class PotentialRequest(BaseModel):
    assay: Assay
    rockTonnes: str = "1"

class SavePotentialRequest(PotentialRequest):
    projectId: str = Field(min_length=1, max_length=100)

def _number(value: str, label: str) -> Decimal:
    try: n = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise HTTPException(422, detail=f"{label}: invalid number")
    if not n.is_finite() or n < 0 or n > 100:
        raise HTTPException(422, detail=f"{label}: expected 0..100 wt%")
    return n

def calculate(req: PotentialRequest) -> dict:
    assay = req.assay
    mass = finite_nonnegative(req.rockTonnes, "rockTonnes")
    missing = [k for k in OXIDES if k not in assay.compositionWtPct]
    if missing:
        raise HTTPException(422, detail="Missing required oxides: " + ", ".join(missing))
    prohibited = set(assay.compositionWtPct) - set(OXIDES)
    if prohibited:
        raise HTTPException(422, detail="Unknown target oxide keys: " + ", ".join(sorted(prohibited)))
    amounts = {k: _number(v, k) for k, v in assay.compositionWtPct.items()}
    other = {k: _number(v, k) for k, v in assay.otherOxidesWtPct.items()}
    if set(other) & set(amounts):
        raise HTTPException(422, detail="Oxides duplicated between target and other fractions")
    total = sum(amounts.values(), Decimal("0")) + sum(other.values(), Decimal("0"))
    if total > Decimal("100"):
        raise HTTPException(422, detail="Total reported oxides exceed 100 wt%")
    # For a tonne of feedstock: oxide fraction * molar CO2 per mol oxide.
    # Two mol CO2 per mole of divalent oxide or alkali-metal oxide.
    contributions = {
        k: (v / Decimal("100")) * (Decimal("2") * MW_CO2 / MW[k])
        for k, v in amounts.items()
    }
    gross = sum(contributions.values(), Decimal("0"))
    reasons = []
    if assay.carbonateStatus != "absent-confirmed":
        reasons.append("carbonate-correction-not-established")
    if assay.sulfatePhosphateStatus != "absent-confirmed":
        reasons.append("sulfate-phosphate-correction-not-established")
    if total < Decimal("99"):
        reasons.append("bulk-assay-incomplete-or-unreported")
    # Even a complete assay cannot certify net durable atmospheric uptake.
    def output_decimal(value: Decimal) -> str:
        """Emit canonical zero rather than Decimal exponent notation (0E-28)."""
        return "0" if value == 0 else str(value)

    obj = {
        "schema": "sc.erw.stoichiometric-potential.v0.2.0",
        "method": {"name": "idealized-four-oxide-charge-balance",
                   "referenceDOI": METHOD_DOI, "referenceURL": METHOD_URL,
                   "equation": "sum_i[(wtPct_i/100)*(2*M_CO2/M_oxide_i)]",
                   "assumption": "complete idealized carbonic-acid dissolution"},
        "assay": assay.model_dump(),
        "inputs": {"rockTonnes": str(mass), "unit": "t feedstock"},
        "oxideContributionsTco2PerTrock": {k: output_decimal(v) for k,v in contributions.items()},
        "grossUpperBound": {
            "tCO2PerTFeedstock": output_decimal(gross),
            "tCO2ForInputRockMass": output_decimal(gross * mass),
        },
        "assayTotalWtPct": str(total),
        "unresolvedCorrections": reasons,
        "status": "exploratory-gross-upper-bound",
        "netDurableAtmosphericRemoval": None,
        "scientificLimit": "Gross theoretical capacity only. Not dissolution, uptake, durable storage, or verified CDR; downstream, carbonates, strong acids and LCA not assessed.",
    }
    obj["calculationObjectHash"] = content_hash(obj)
    return obj

@router.get("/erw/v0.2.0/status")
def status():
    return {"ok": True, "extension": "erw", "extensionVersion": "0.2.0",
            "workbenchVersion": APP_VERSION, "mode": "exploratory-gross-upper-bound",
            "verifiedCDR": False}

@router.get("/erw/v0.2.0/method")
def method():
    return {"ok": True, "requiredOxides": list(OXIDES), "atomicMassesGPerMol": {k:str(v) for k,v in MW.items()},
            "co2MolarMass": str(MW_CO2), "doi": METHOD_DOI,
            "caution": "Not a correction-complete Steinour estimate or crediting methodology."}

@router.post("/erw/v0.2.0/potential")
def potential(req: PotentialRequest):
    return {"ok": True, "calculation": calculate(req)}

@router.post("/erw/v0.2.0/projects/potential")
def save_potential(req: SavePotentialRequest, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    project = get_project(req.projectId, owner)
    if project.get("metadata", {}).get("researchId") != PROJECT_KEY:
        raise HTTPException(422, detail="Project is not the ERW research template")
    obj = calculate(PotentialRequest(assay=req.assay, rockTonnes=req.rockTonnes))
    saved = save_calculation(SavedCalculationCreateRequest(
        projectId=req.projectId, title="ERW 0.2 gross feedstock potential",
        calculationObject=obj, tags=["erw","stoichiometry","exploratory"],
        metadata={"evidenceClass": req.assay.sourceKind, "researchId": PROJECT_KEY,
                  "scientificStatus": "exploratory-gross-upper-bound"}), owner)
    return {"ok": True, "calculation": obj, "saved": saved}

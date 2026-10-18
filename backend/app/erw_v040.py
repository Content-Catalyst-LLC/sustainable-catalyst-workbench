"""ERW 0.4.0 — scenario-linked lifecycle burden and permanence evidence ledger.

This is an exploratory *burden and evidence* calculation, not a verified net CDR model.
All quantities and factors must be supplied explicitly with source records.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import _owner, get_project, save_calculation, SavedCalculationCreateRequest
from .erw_v010 import PROJECT_KEY

router = APIRouter(tags=["erw-0.4.0"])

def number(raw, label, ceiling="1000000000000"):
    try:
        value=Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(422, detail=label+": invalid decimal")
    if not value.is_finite() or value < 0 or value > Decimal(ceiling):
        raise HTTPException(422, detail=label+": value outside permitted range")
    return value

def fmt(value):
    return "0" if value == 0 else str(value)

class Activity(BaseModel):
    category: str = Field(pattern="^(quarrying|crushing|processing|transport|spreading|monitoring|other)$")
    activityId: str = Field(min_length=1, max_length=100)
    quantity: str
    unit: str = Field(min_length=1, max_length=50)
    emissionsFactorKgCO2ePerUnit: str
    factorUnit: str = Field(min_length=1, max_length=60)
    sourceReference: str = Field(min_length=1, max_length=1200)
    evidenceClass: str = Field(pattern="^(hypothetical|literature-derived|measured)$")
    boundaryNote: str = Field(min_length=1, max_length=800)

class PermanenceEvidence(BaseModel):
    pathway: str = Field(pattern="^(dissolved-inorganic-carbon|soil-inorganic-carbonate|ocean-storage|other|unknown)$")
    status: str = Field(pattern="^(unassessed|hypothetical|literature-supported|site-measured)$")
    sourceReference: str = Field(min_length=1, max_length=1200)
    hydrologicalFateEstablished: bool = False
    secondaryMineralEffectsEstablished: bool = False
    strongAcidCorrectionsEstablished: bool = False
    longTermRetentionEstablished: bool = False

class LifecycleRequest(BaseModel):
    researchId: str = PROJECT_KEY
    sourceScenarioCalculationHash: str = Field(min_length=16, max_length=200)
    studyYears: int = Field(ge=1, le=100, default=10)
    scenarioDoseTonnesPerHa: str
    rockTonnes: str
    theoreticalUpperBoundTonnesCO2: str
    activities: List[Activity] = Field(min_length=1, max_length=100)
    permanence: PermanenceEvidence
    assessmentSourceReference: str = Field(min_length=1, max_length=1200)

class SaveLifecycleRequest(LifecycleRequest):
    projectId: str = Field(min_length=1, max_length=100)

def assess(req: LifecycleRequest) -> dict:
    if req.researchId != PROJECT_KEY:
        raise HTTPException(422, detail="Not the Wexford ERW research template")
    rock=number(req.rockTonnes,"rockTonnes")
    dose=number(req.scenarioDoseTonnesPerHa,"scenarioDoseTonnesPerHa")
    theoretical=number(req.theoreticalUpperBoundTonnesCO2,"theoreticalUpperBoundTonnesCO2")
    if dose == 0 and (rock != 0 or theoretical != 0):
        raise HTTPException(422, detail="Zero-dose control requires zero applied rock and zero treatment chemical capacity")
    ids=[a.activityId for a in req.activities]
    if len(ids)!=len(set(ids)):
        raise HTTPException(422, detail="Duplicate activityId")
    totals={}
    lines=[]
    for a in req.activities:
        qty=number(a.quantity,"activity quantity")
        ef=number(a.emissionsFactorKgCO2ePerUnit,"emissions factor")
        # Guard against an emissions factor expressed in incompatible units.
        if a.factorUnit != "kgCO2e/"+a.unit:
            raise HTTPException(422,detail="factorUnit must be kgCO2e/<unit> using the matching activity unit")
        amount=qty*ef/Decimal("1000")
        totals[a.category]=totals.get(a.category,Decimal("0"))+amount
        lines.append({"activityId":a.activityId,"category":a.category,
                      "quantity":fmt(qty),"unit":a.unit,
                      "emissionsFactorKgCO2ePerUnit":fmt(ef),
                      "factorUnit":a.factorUnit,
                      "emissionsTonnesCO2e":fmt(amount),"sourceReference":a.sourceReference,
                      "evidenceClass":a.evidenceClass,"boundaryNote":a.boundaryNote})
    burden=sum(totals.values(),Decimal("0"))
    # This is intentionally a DIFFERENCE OF INCOMPATIBLE ACCOUNTING QUANTITIES,
    # displayed only as a screening gap, never as net durable removal.
    screening=theoretical-burden
    p=req.permanence
    gaps=[name for name,value in (
        ("hydrological-fate",p.hydrologicalFateEstablished),
        ("secondary-mineral-effects",p.secondaryMineralEffectsEstablished),
        ("strong-acid-corrections",p.strongAcidCorrectionsEstablished),
        ("long-term-retention",p.longTermRetentionEstablished)) if not value]
    obj={
        "schema":"sc.erw.lifecycle-permanence.v0.4.0",
        "workbenchVersion":APP_VERSION,"researchId":PROJECT_KEY,
        "sourceScenarioCalculationHash":req.sourceScenarioCalculationHash,
        "studyYears":req.studyYears,
        "inputs":{"scenarioDoseTonnesPerHa":fmt(dose),"rockTonnes":fmt(rock),
                  "theoreticalUpperBoundTonnesCO2":fmt(theoretical),
                  "assessmentSourceReference":req.assessmentSourceReference},
        "activities":lines,"lifecycleBurdenByCategoryTonnesCO2e":{k:fmt(v) for k,v in sorted(totals.items())},
        "totalModeledLifecycleBurdenTonnesCO2e":fmt(burden),
        "exploratoryUpperBoundMinusBurden":fmt(screening),
        "screeningDifferenceIsNetRemoval":False,
        "permanence":{"evidence":p.model_dump(),"unresolvedGaps":gaps,
                      "verifiedDurableStorage":False},
        "additionalityDemonstrated":False,
        "netDurableAtmosphericRemoval":None,
        "verificationStatus":"exploratory-input-dependent-not-verified",
        "scientificLimit":"A theoretical chemical capacity minus lifecycle emissions is not net CDR. Realized weathering, counterfactual additionality, transport, downstream chemistry, permanence, uncertainty and verification remain unresolved."
    }
    obj["calculationObjectHash"]=content_hash(obj)
    return obj

@router.get("/erw/v0.4.0/status")
def status():
    return {"ok":True,"extension":"erw","extensionVersion":"0.4.0",
            "workbenchVersion":APP_VERSION,"verifiedCDR":False,"verifiedPermanence":False}

@router.post("/erw/v0.4.0/assess")
def assessment(req:LifecycleRequest):
    return {"ok":True,"assessment":assess(req)}

@router.post("/erw/v0.4.0/projects/assess")
def save_assessment(req:SaveLifecycleRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    project=get_project(req.projectId,owner)
    if project.get("metadata",{}).get("researchId")!=PROJECT_KEY:
        raise HTTPException(422,detail="Not an ERW research project")
    obj=assess(LifecycleRequest(**req.model_dump(exclude={"projectId"})))
    saved=save_calculation(SavedCalculationCreateRequest(
        projectId=req.projectId,title="ERW 0.4 lifecycle burden and permanence evidence",
        calculationObject=obj,tags=["erw","lifecycle","permanence","exploratory"],
        metadata={"researchId":PROJECT_KEY,"scientificStatus":"not-verified-cdr"}),owner)
    return {"ok":True,"assessment":obj,"saved":saved}

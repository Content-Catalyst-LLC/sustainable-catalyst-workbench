"""ERW 0.3.0: hypothetical ten-year baseline and intervention scenario ledger.

Models feedstock applications and *illustrative realization of theoretical potential*
only. Never equates realized model potential with verified additional durable CO2 removal.
No site, baseline or measurement is inferred.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import _owner, get_project, save_calculation, SavedCalculationCreateRequest
from .erw_v010 import PROJECT_KEY, finite_nonnegative

router = APIRouter(tags=["erw-0.3.0"])

def num(x, name, upper="1000000000"):
    try:
        v=Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(422, detail=name+": invalid decimal")
    if not v.is_finite() or v<0 or v>Decimal(upper):
        raise HTTPException(422, detail=name+": out of range")
    return v

def out(v):
    return "0" if v==0 else str(v)

class AnnualAssumption(BaseModel):
    year: int = Field(ge=1, le=100)
    realizationFraction: str  # share of INITIAL feedstock potential assigned to the year, 0..1
    backgroundPotentialTonnesCO2: str = "0"  # hypothetical untreated annual comparison
    evidenceClass: str = Field(default="hypothetical",pattern="^(hypothetical|literature-derived|measured)$")
    sourceReference: str = Field(min_length=1, max_length=1000,default="User-specified illustrative scenario assumption")

class ScenarioRequest(BaseModel):
    studyAreaHa: str = "100"
    years: int = Field(default=10, ge=1, le=100)
    applicationRatesTonnesPerHa: List[str] = Field(default_factory=lambda:["0","10","20"], min_length=2, max_length=12)
    upperBoundTco2PerTFeedstock: str
    compositionCalculationHash: str = Field(min_length=16, max_length=200)
    timeline: List[AnnualAssumption] = Field(min_length=1, max_length=100)
    applicationYear: int = Field(default=1, ge=1, le=100)
    scenarioSourceReference: str = Field(min_length=1, max_length=1000)
    evidenceClass: str = Field(default="hypothetical",pattern="^(hypothetical|literature-derived|measured)$")

class SaveScenarioRequest(ScenarioRequest):
    projectId: str = Field(min_length=1, max_length=100)

def model(req: ScenarioRequest):
    area=num(req.studyAreaHa,"studyAreaHa")
    factor=num(req.upperBoundTco2PerTFeedstock,"upperBoundTco2PerTFeedstock","10")
    if req.applicationYear>req.years:
        raise HTTPException(422,detail="applicationYear exceeds assessment")
    rates=[num(x,"applicationRateTonnesPerHa") for x in req.applicationRatesTonnesPerHa]
    if len(set(rates))!=len(rates) or Decimal("0") not in rates:
        raise HTTPException(422,detail="Unique rates including zero control are required")
    years=[a.year for a in req.timeline]
    if len(years)!=req.years or sorted(years)!=list(range(1,req.years+1)):
        raise HTTPException(422,detail="Exactly one annual assumption for each modeled year is required")
    assumptions=sorted(req.timeline,key=lambda x:x.year)
    fractions=[num(a.realizationFraction,"realizationFraction","1") for a in assumptions]
    if sum(fractions,Decimal("0"))>1:
        raise HTTPException(422,detail="Sum of fractions cannot exceed 1; no double-counting initial application")
    baseline=[num(a.backgroundPotentialTonnesCO2,"backgroundPotentialTonnesCO2") for a in assumptions]
    # The treatment proxy is a partition of the original theoretical capacity across years.
    # It is NOT an atmospheric removal flux, verified additionality or soil observation.
    scenarios=[]
    for rate in rates:
        rock=area*rate
        gross=rock*factor
        series=[]
        for a,frac,bg in zip(assumptions,fractions,baseline):
            proxy=(gross*frac) if a.year>=req.applicationYear else Decimal("0")
            # By construction the counterfactual bg is equal for treatment and control.
            # Incremental model proxy is the treatment component, NOT a field causal estimate.
            series.append({"year":a.year,"backgroundPotentialTonnesCO2":out(bg),
                           "modeledScenarioPotentialTonnesCO2":out(bg+proxy),
                           "incrementalPotentialProxyTonnesCO2":out(proxy),
                           "realizationFraction":out(frac),
                           "assumptionEvidenceClass":a.evidenceClass,
                           "assumptionSourceReference":a.sourceReference})
        scenarios.append({"rateTonnesPerHa":out(rate),"rockTonnes":out(rock),
                          "grossTheoreticalUpperBoundTonnesCO2":out(gross),
                          "annual":series,
                          "cumulativeIncrementalPotentialProxyTonnesCO2":out(gross * sum((frac for a, frac in zip(assumptions, fractions) if a.year >= req.applicationYear), Decimal("0")))})
    payload={"schema":"sc.erw.scenario-ledger.v0.3.0","workbenchVersion":APP_VERSION,
             "researchId":PROJECT_KEY,
             "inputs":{"studyAreaHa":out(area),"years":req.years,
                       "applicationYear":req.applicationYear,
                       "upperBoundTco2PerTFeedstock":out(factor),
                       "compositionCalculationHash":req.compositionCalculationHash,
                       "scenarioSourceReference":req.scenarioSourceReference,
                       "evidenceClass":req.evidenceClass},
             "scenarios":scenarios,
             "additionalityAssessment":{"demonstrated":False,"baselineType":"user-provided-hypothetical-counterfactual",
               "comparison":"scenario potential minus shared background potential",
               "causalIdentification":"not-established",
               "netDurableAtmosphericRemoval":None},
             "scenarioStatus":"illustrative-model-only",
             "scientificLimit":"Annual incremental potential proxy is NOT measured weathering, counterfactual additionality, net CDR, durability, or avoided emissions."}
    payload["calculationObjectHash"]=content_hash(payload)
    return payload

@router.get("/erw/v0.3.0/status")
def status():
    return {"ok":True,"extension":"erw","extensionVersion":"0.3.0",
            "workbenchVersion":APP_VERSION,"verifiedAdditionality":False,"verifiedCDR":False}

@router.post("/erw/v0.3.0/scenarios")
def scenarios(req:ScenarioRequest):
    return {"ok":True,"scenario":model(req)}

@router.post("/erw/v0.3.0/projects/scenarios")
def save_scenarios(req:SaveScenarioRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    project=get_project(req.projectId,owner)
    if project.get("metadata",{}).get("researchId")!=PROJECT_KEY:
        raise HTTPException(422,detail="Not an ERW study project")
    data=model(ScenarioRequest(**req.model_dump(exclude={"projectId"})))
    saved=save_calculation(SavedCalculationCreateRequest(
        projectId=req.projectId,title="ERW 0.3 hypothetical baseline scenario ledger",
        calculationObject=data,tags=["erw","scenarios","hypothetical","not-verified-cdr"],
        metadata={"researchId":PROJECT_KEY,"evidenceClass":req.evidenceClass,
                  "scientificStatus":"illustrative-model-only"}),owner)
    return {"ok":True,"scenario":data,"saved":saved}

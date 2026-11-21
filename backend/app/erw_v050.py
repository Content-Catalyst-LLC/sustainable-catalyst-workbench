"""ERW 0.5.0 — bounded sensitivity and evidence-specific MRV readiness.

Deterministic interval propagation only. Not a probability interval, field estimate,
causal additionality finding, or verified net durable atmospheric removal.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import List, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import _owner, get_project, save_calculation, SavedCalculationCreateRequest
from .erw_v010 import PROJECT_KEY

router=APIRouter(tags=["erw-0.5.0"])
def dec(raw,name):
    try: value=Decimal(str(raw))
    except (InvalidOperation,ValueError,TypeError): raise HTTPException(422,detail=name+": invalid decimal")
    if not value.is_finite() or value<0 or value>Decimal("1000000000000"):
        raise HTTPException(422,detail=name+": out of range")
    return value
def fmt(value):
    s=format(value,"f")
    return (s.rstrip("0").rstrip(".") if "." in s else s) or "0"

class Range(BaseModel):
    low: str
    central: str
    high: str

class Evidence(BaseModel):
    requirement: str = Field(pattern="^(baseline-control|feedstock-assay|soil-porewater|water-flux|dissolved-alkalinity|downstream-fate|strong-acid-correction|lifecycle-inventory|permanence|independent-verification)$")
    state: str = Field(pattern="^(missing|planned|documented|measured|independently-reviewed)$")
    sourceReference: str = Field(min_length=1,max_length=1200)
    evidenceClass: str = Field(pattern="^(hypothetical|literature-derived|measured)$")
    limitations: str = Field(min_length=1,max_length=1200)

REQUIREMENTS=("baseline-control","feedstock-assay","soil-porewater","water-flux",
              "dissolved-alkalinity","downstream-fate","strong-acid-correction",
              "lifecycle-inventory","permanence","independent-verification")

class UncertaintyRequest(BaseModel):
    researchId: str = PROJECT_KEY
    lifecycleCalculationHash: str = Field(min_length=16,max_length=200)
    scenarioCalculationHash: str = Field(min_length=16,max_length=200)
    feedstockMassTonnes: Range
    grossCapacityTco2PerTFeedstock: Range
    realizedFraction: Range
    lifecycleBurdenTonnesCO2e: Range
    evidence: List[Evidence] = Field(min_length=1,max_length=40)
    assumptionsSourceReference: str = Field(min_length=1,max_length=1200)

class SaveUncertaintyRequest(UncertaintyRequest):
    projectId: str = Field(min_length=1,max_length=100)

def analyze(req:UncertaintyRequest):
    if req.researchId != PROJECT_KEY: raise HTTPException(422,detail="Not ERW template")
    if req.lifecycleCalculationHash == req.scenarioCalculationHash:
        raise HTTPException(422,detail="Distinct scenario and lifecycle hashes required")
    vals={}
    for key in ("feedstockMassTonnes","grossCapacityTco2PerTFeedstock","realizedFraction","lifecycleBurdenTonnesCO2e"):
        interval=getattr(req,key)
        lo,ce,hi=(dec(getattr(interval,k),key+"."+k) for k in ("low","central","high"))
        if not lo<=ce<=hi: raise HTTPException(422,detail=key+" must have low <= central <= high")
        if key=="realizedFraction" and hi>1:
            raise HTTPException(422,detail="Realization fraction must be <=1")
        vals[key]=(lo,ce,hi)
    mass,capacity,realization,burden=(vals[k] for k in
      ("feedstockMassTonnes","grossCapacityTco2PerTFeedstock","realizedFraction","lifecycleBurdenTonnesCO2e"))
    # Screening only; independence/correlation unknown. Extreme bounds are not confidence intervals.
    gross=(mass[0]*capacity[0],mass[1]*capacity[1],mass[2]*capacity[2])
    proxy=(gross[0]*realization[0],gross[1]*realization[1],gross[2]*realization[2])
    screen=(proxy[0]-burden[2],proxy[1]-burden[1],proxy[2]-burden[0])
    def triple(t): return dict(zip(("low","central","high"),(fmt(x) for x in t)))
    evidence={}; duplicates=set()
    for e in req.evidence:
        if e.requirement in evidence: duplicates.add(e.requirement)
        evidence[e.requirement]=e.model_dump()
    if duplicates: raise HTTPException(422,detail="Duplicate MRV requirements: "+",".join(sorted(duplicates)))
    missing=[key for key in REQUIREMENTS if key not in evidence or evidence[key]["state"] in ("missing","planned")]
    not_reviewed=[key for key in REQUIREMENTS if key not in evidence or evidence[key]["state"]!="independently-reviewed"]
    sensitivities=[]
    central_proxy=proxy[1]
    for key in ("feedstockMassTonnes","grossCapacityTco2PerTFeedstock","realizedFraction"):
        a,b,c=vals[key]
        others=Decimal("1")
        for k in ("feedstockMassTonnes","grossCapacityTco2PerTFeedstock","realizedFraction"):
            if k!=key: others*=vals[k][1]
        sensitivities.append({"parameter":key,"lowPerturbationProxyTonnesCO2":fmt(a*others),
                              "highPerturbationProxyTonnesCO2":fmt(c*others),
                              "absoluteSwingTonnesCO2":fmt((c-a)*others)})
    sensitivities.append({"parameter":"lifecycleBurdenTonnesCO2e",
                          "lowPerturbationScreeningDifference":fmt(central_proxy-burden[2]),
                          "highPerturbationScreeningDifference":fmt(central_proxy-burden[0]),
                          "absoluteSwingTonnesCO2e":fmt(burden[2]-burden[0])})
    obj={"schema":"sc.erw.uncertainty-mrv.v0.5.0","workbenchVersion":APP_VERSION,
         "researchId":PROJECT_KEY,"lineage":{"scenarioCalculationHash":req.scenarioCalculationHash,
         "lifecycleCalculationHash":req.lifecycleCalculationHash},
         "inputRanges":{k:triple(v) for k,v in vals.items()},
         "grossTheoreticalCapacityTonnesCO2":triple(gross),
         "modeledRealizationProxyTonnesCO2":triple(proxy),
         "exploratoryProxyMinusBurdenTonnes":triple(screen),
         "sensitivityOneAtATime":sensitivities,
         "mrvReadiness":{"requirements":evidence,"missingOrPlanned":missing,
                        "notIndependentlyReviewed":not_reviewed,
                        "completeEvidenceInventory":len(evidence)==len(REQUIREMENTS),
                        "approvedForCrediting":False,"verifiedNetRemoval":False},
         "assumptionsSourceReference":req.assumptionsSourceReference,
         "boundsKind":"deterministic-extreme-screening-not-probabilistic",
         "verifiedAdditionality":False,"netDurableAtmosphericRemoval":None,
         "scientificLimit":"Screening bounds are not confidence intervals or actual uptake. Scenario hashes are provenance references supplied by caller, not verified server-side lineage. Independent MRV, causal baseline, field measurements, downstream storage and durable CDR are not established."}
    obj["calculationObjectHash"]=content_hash(obj)
    return obj

@router.get("/erw/v0.5.0/status")
def status():
    return {"ok":True,"extension":"erw","extensionVersion":"0.5.0",
      "workbenchVersion":APP_VERSION,"verifiedCDR":False,"approvedForCrediting":False}

@router.get("/erw/v0.5.0/mrv-requirements")
def requirements():
    return {"ok":True,"requirements":list(REQUIREMENTS)}

@router.post("/erw/v0.5.0/analyze")
def analyze_route(req:UncertaintyRequest):
    return {"ok":True,"analysis":analyze(req)}

@router.post("/erw/v0.5.0/projects/analyze")
def save_analysis(req:SaveUncertaintyRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    project=get_project(req.projectId,owner)
    if project.get("metadata",{}).get("researchId")!=PROJECT_KEY:
        raise HTTPException(422,detail="Not an ERW research project")
    obj=analyze(UncertaintyRequest(**req.model_dump(exclude={"projectId"})))
    saved=save_calculation(SavedCalculationCreateRequest(
       projectId=req.projectId,title="ERW 0.5 uncertainty and MRV readiness ledger",
       calculationObject=obj,tags=["erw","uncertainty","mrv","not-verified"],
       metadata={"researchId":PROJECT_KEY,"scientificStatus":"not-verified-cdr"}),owner)
    return {"ok":True,"analysis":obj,"saved":saved}

"""ERW v0.6: deterministic, declarative visual research objects.

Only uses explicitly provided, schema-checked calculation objects; never fetches
external sources or infers verified net durable carbon removal.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import _owner, get_project, save_calculation, SavedCalculationCreateRequest
from .erw_v010 import PROJECT_KEY

router=APIRouter(tags=["erw-0.6.0"])
SCHEMAS={
 "scenario":"sc.erw.scenario-ledger.v0.3.0",
 "uncertainty":"sc.erw.uncertainty-mrv.v0.5.0",
}
MAX_POINTS=1200

class VisualRequest(BaseModel):
    researchId: str=PROJECT_KEY
    scenario: dict[str,Any]
    lifecycle: dict[str,Any]
    uncertainty: dict[str,Any]
    sourceReference: str=Field(min_length=1,max_length=1200)

class SaveVisualRequest(VisualRequest):
    projectId: str=Field(min_length=1,max_length=100)

def number(x, label):
    if isinstance(x,bool): raise HTTPException(422,detail=label+": invalid number")
    try: d=Decimal(str(x))
    except (InvalidOperation,ValueError,TypeError): raise HTTPException(422,detail=label+": invalid number")
    if not d.is_finite() or abs(d)>Decimal("1e30"):
        raise HTTPException(422,detail=label+": out of range")
    return d

def num_string(x,label): return str(number(x,label))

def required(obj,key):
    if not isinstance(obj,dict) or key not in obj: raise HTTPException(422,detail="Missing "+key)
    return obj[key]

def visual(req:VisualRequest):
    if req.researchId!=PROJECT_KEY: raise HTTPException(422,detail="Not ERW research")
    s,l,u=req.scenario,req.lifecycle,req.uncertainty
    if s.get("schema")!=SCHEMAS["scenario"] or u.get("schema")!=SCHEMAS["uncertainty"]:
        raise HTTPException(422,detail="Incompatible source schema")
    for name,obj in (("scenario",s),("lifecycle",l),("uncertainty",u)):
        if obj.get("researchId")!=PROJECT_KEY: raise HTTPException(422,detail=name+" research ID mismatch")
        if not isinstance(obj.get("calculationObjectHash"),str) or len(obj["calculationObjectHash"])<16:
            raise HTTPException(422,detail=name+" hash missing")
    if required(u,"lineage").get("scenarioCalculationHash")!=s["calculationObjectHash"]:
        raise HTTPException(422,detail="Uncertainty scenario reference mismatch")
    if u["lineage"].get("lifecycleCalculationHash")!=l["calculationObjectHash"]:
        raise HTTPException(422,detail="Uncertainty lifecycle reference mismatch")
    if l.get("sourceScenarioCalculationHash")!=s["calculationObjectHash"]:
        raise HTTPException(422,detail="Lifecycle scenario reference mismatch")
    items=required(s,"scenarios")
    if not isinstance(items,list) or not 2<=len(items)<=12:
        raise HTTPException(422,detail="2-12 scenarios required")
    trajectories=[]
    for item in items:
        rate=num_string(required(item,"rateTonnesPerHa"),"rate")
        annual=required(item,"annual")
        if not isinstance(annual,list) or not 1<=len(annual)<=100:
            raise HTTPException(422,detail="Invalid annual series")
        points=[]
        for i,entry in enumerate(annual,1):
            if not isinstance(entry,dict) or entry.get("year")!=i:
                raise HTTPException(422,detail="Nonconsecutive year")
            points.append({"year":i,
                "baselinePotentialTonnesCO2":num_string(required(entry,"backgroundPotentialTonnesCO2"),"baseline"),
                "scenarioPotentialTonnesCO2":num_string(required(entry,"modeledScenarioPotentialTonnesCO2"),"scenario"),
                "incrementalPotentialProxyTonnesCO2":num_string(required(entry,"incrementalPotentialProxyTonnesCO2"),"proxy")})
        trajectories.append({"rateTonnesPerHa":rate,"points":points})
    if sum(len(x["points"]) for x in trajectories)>MAX_POINTS:
        raise HTTPException(422,detail="Visualization size exceeded")
    category=required(l,"totalsByCategoryTonnesCO2e")
    if not isinstance(category,dict) or len(category)>30: raise HTTPException(422,detail="Invalid emissions categories")
    emissions=[{"category":k,"tonnesCO2e":num_string(v,"emissions")} for k,v in sorted(category.items())]
    required_total=number(required(l,"totalModeledLifecycleBurdenTonnesCO2e"),"total emissions")
    if sum((number(p["tonnesCO2e"],"category") for p in emissions),Decimal(0))!=required_total:
        raise HTTPException(422,detail="Emissions category sum mismatch")
    uncertainty=[]
    for variable in ("grossTheoreticalCapacityTonnesCO2","modeledRealizationProxyTonnesCO2",
                     "exploratoryProxyMinusBurdenTonnes"):
        bounds=required(u,variable)
        low,central,high=[number(required(bounds,k),variable+"."+k) for k in ("low","central","high")]
        if not low<=central<=high: raise HTTPException(422,detail="Invalid interval")
        uncertainty.append({"metric":variable,"low":str(low),"central":str(central),"high":str(high)})
    sensitivity=required(u,"sensitivityOneAtATime")
    if not isinstance(sensitivity,list) or len(sensitivity)!=4: raise HTTPException(422,detail="Expected four sensitivities")
    ranks=[]
    for entry in sensitivity:
        v=entry.get("absoluteSwingTonnesCO2",entry.get("absoluteSwingTonnesCO2e"))
        ranks.append({"parameter":str(required(entry,"parameter")),"swing":num_string(v,"sensitivity")})
    ranks.sort(key=lambda r:(-number(r["swing"],"swing"),r["parameter"]))
    mrv=required(required(u,"mrvReadiness"),"requirements")
    if not isinstance(mrv,dict) or len(mrv)>40: raise HTTPException(422,detail="Invalid MRV evidence")
    matrix=[{"requirement":name,"state":str(required(record,"state")),
        "evidenceClass":str(required(record,"evidenceClass"))} for name,record in sorted(mrv.items())]
    out={"schema":"sc.erw.visual-research-package.v0.6.0","workbenchVersion":APP_VERSION,
         "researchId":PROJECT_KEY,"rendererContract":"sc.erw.declarative-scene.v1",
         "sourceHashes":{"scenario":s["calculationObjectHash"],
                         "lifecycle":l["calculationObjectHash"],
                         "uncertainty":u["calculationObjectHash"]},
         "views":[
           {"id":"scenario-trajectories","kind":"multi-series-line","x":"year",
            "units":"tonnes CO2 theoretical potential proxy","series":trajectories},
           {"id":"lifecycle-breakdown","kind":"categorical-bar","units":"tonnes CO2e","bars":emissions},
           {"id":"uncertainty-intervals","kind":"interval","intervalSemantics":"deterministic-extreme-not-probabilistic",
            "intervals":uncertainty},
           {"id":"sensitivity-ranking","kind":"ranked-bar","ranking":ranks},
           {"id":"mrv-evidence-matrix","kind":"categorical-matrix","cells":matrix}],
         "sourceReference":req.sourceReference,
         "allInputsCallerSupplied":True,"sourceIntegrityVerified":False,
         "verifiedCDR":False,"verifiedAdditionality":False,"verifiedPermanence":False,
         "netDurableAtmosphericRemoval":None,
         "scientificLimit":"Visuals describe caller-supplied hypothetical model objects; references are checked for equality only, not independently against database. No measured removal or crediting determination."}
    out["calculationObjectHash"]=content_hash(out)
    return out

@router.get("/erw/v0.6.0/status")
def status():
    return {"ok":True,"extension":"erw","extensionVersion":"0.6.0",
            "workbenchVersion":APP_VERSION,"verifiedCDR":False}

@router.post("/erw/v0.6.0/visualize")
def visualize(req:VisualRequest): return {"ok":True,"visual":visual(req)}

@router.post("/erw/v0.6.0/projects/visualize")
def save_visual(req:SaveVisualRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    project=get_project(req.projectId,owner)
    if project.get("metadata",{}).get("researchId")!=PROJECT_KEY:
        raise HTTPException(422,detail="Not an ERW study")
    out=visual(VisualRequest(**req.model_dump(exclude={"projectId"})))
    saved=save_calculation(SavedCalculationCreateRequest(
       projectId=req.projectId,title="ERW 0.6 declarative scientific visualization",
       calculationObject=out,tags=["erw","visualization","unverified-cdr"],
       metadata={"researchId":PROJECT_KEY,"scientificStatus":"exploratory-only"}),owner)
    return {"ok":True,"visual":out,"saved":saved}

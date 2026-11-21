"""ERW 0.8 — deterministic, unpublished, academic manuscript composition.

Caller-provided six source objects; reference equality != independently verified provenance.
No outbound publication, external writing or attestation.
"""
from __future__ import annotations
from typing import Any,Optional
from fastapi import APIRouter,HTTPException,Header
from pydantic import BaseModel,Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import _owner,get_project,save_calculation,SavedCalculationCreateRequest
from .erw_v010 import PROJECT_KEY

router=APIRouter(tags=["erw-0.8.0"])
KINDS=("geochemistry","scenario","lifecycle","uncertainty","visualization","diagrams")
EXPECTED={
 "geochemistry":"sc.erw.stoichiometric-potential.v0.2.0",
 "scenario":"sc.erw.scenario-ledger.v0.3.0",
 "lifecycle":"sc.erw.lifecycle-permanence.v0.4.0",
 "uncertainty":"sc.erw.uncertainty-mrv.v0.5.0",
 "visualization":"sc.erw.visual-research-package.v0.6.0",
 "diagrams":"sc.erw.equations-maps-diagrams.v0.7.0",
}
class ReportRequest(BaseModel):
    researchId:str=PROJECT_KEY
    title:str=Field(min_length=5,max_length=250)
    authors:list[str]=Field(min_length=1,max_length=20)
    sourceObjects:dict[str,dict[str,Any]]
    bibliography:list[dict[str,str]]=Field(default_factory=list,max_length=100)
    purpose:str=Field(min_length=8,max_length=1500)
    sourceReference:str=Field(min_length=1,max_length=1200)

class SaveReportRequest(ReportRequest):
    projectId:str=Field(min_length=1,max_length=100)

def compose(req:ReportRequest):
    if req.researchId!=PROJECT_KEY:raise HTTPException(422,detail="Not an ERW study")
    if set(req.sourceObjects)!=set(KINDS):raise HTTPException(422,detail="Exactly six source objects required")
    objs=req.sourceObjects;hashes={}
    for k in KINDS:
        o=objs[k]
        if k!="geochemistry" and o.get("researchId")!=PROJECT_KEY:raise HTTPException(422,detail=k+": research mismatch")
        h=o.get("calculationObjectHash")
        if not isinstance(h,str) or len(h)<16 or len(h)>200:raise HTTPException(422,detail=k+": missing hash")
        if o.get("schema")!=EXPECTED[k]:
            raise HTTPException(422,detail=k+": incompatible schema")
        hashes[k]=h
    if len(set(hashes.values()))!=6:raise HTTPException(422,detail="Source hashes must be distinct")
    if objs["scenario"].get("inputs",{}).get("compositionCalculationHash")!=hashes["geochemistry"]:
        raise HTTPException(422,detail="Scenario/geochemistry lineage mismatch")
    if objs["lifecycle"].get("sourceScenarioCalculationHash")!=hashes["scenario"]:
        raise HTTPException(422,detail="Lifecycle/scenario lineage mismatch")
    u=objs["uncertainty"]
    if u.get("lineage",{}).get("scenarioCalculationHash")!=hashes["scenario"] or u.get("lineage",{}).get("lifecycleCalculationHash")!=hashes["lifecycle"]:
        raise HTTPException(422,detail="Uncertainty lineage mismatch")
    vis=objs["visualization"]
    if vis.get("sourceHashes")!={"scenario":hashes["scenario"],"lifecycle":hashes["lifecycle"],"uncertainty":hashes["uncertainty"]}:
        raise HTTPException(422,detail="Visualization lineage mismatch")
    if objs["diagrams"].get("sourceVisualHash")!=hashes["visualization"]:
        raise HTTPException(422,detail="Diagram lineage mismatch")
    if vis.get("verifiedCDR") is not False or objs["diagrams"].get("verifiedCDR") is not False:
        raise HTTPException(422,detail="Unverified CDR status required")
    if any(not a.strip() or len(a)>200 for a in req.authors):
        raise HTTPException(422,detail="Invalid author")
    refs=[]; seen=set()
    for raw in req.bibliography:
        ref=raw.get("reference","").strip()
        classification=raw.get("evidenceClass","")
        if not ref or len(ref)>1200 or classification not in ("hypothetical","literature-derived","measured"):
            raise HTTPException(422,detail="Invalid bibliography entry")
        if ref in seen:raise HTTPException(422,detail="Duplicate reference")
        seen.add(ref); refs.append({"reference":ref,"evidenceClass":classification,
                                    "verifiedAgainstExternalSource":False})
    views=vis.get("views")
    if not isinstance(views,list) or len(views)!=5:raise HTTPException(422,detail="Missing figures")
    equation_specs=objs["diagrams"].get("equations")
    if not isinstance(equation_specs,list) or len(equation_specs)!=4:
        raise HTTPException(422,detail="Missing equations")
    sections=[
       {"id":"abstract","heading":"Abstract","text":"Hypothetical enhanced rock weathering methods and screening outputs. No verified net atmospheric removal."},
       {"id":"introduction","heading":"Research context and objectives","text":req.purpose},
       {"id":"methods","heading":"Materials and methods","text":"Caller-provided composition, baseline scenario, lifecycle inputs, bounded sensitivity and MRV evidence statuses."},
       {"id":"results","heading":"Exploratory results","text":"Theoretical potential and illustrative realized proxies; lifecycle burdens and deterministic intervals. Figures are declarative specifications, not rendered data."},
       {"id":"discussion","heading":"Discussion and uncertainties","text":"Lack of independently established additionality, aqueous flux, downstream fate and durable storage prevents verified CDR conclusions."},
       {"id":"limitations","heading":"Limitations and integrity","text":"Source hashes are checked for internal equality only, not verified against saved source data; no observational or crediting claim."},
       {"id":"conclusions","heading":"Conclusions","text":"Provides reproducible structure for research review, not a field measurement or publication-ready verified finding."}
    ]
    output={"schema":"sc.erw.academic-report.v0.8.0","researchId":PROJECT_KEY,
       "workbenchVersion":APP_VERSION,"title":req.title,"authors":req.authors,
       "status":"draft-unpublished","publicationEnabled":False,"outboundSubmissionEnabled":False,
       "sourceHashes":hashes,"sourceIntegrityVerified":False,"purpose":req.purpose,
       "sections":sections,"figures":[{"figureId":v["id"],"kind":v.get("kind","declarative"),
          "sourceHash":hashes["visualization"]} for v in views],
       "equations":[{"equationId":x.get("id"),"latex":x.get("latex"),
          "sourceHash":hashes["diagrams"]} for x in equation_specs],
       "bibliography":refs,"sourceReference":req.sourceReference,
       "reproducibilityAppendix":{"sourceHashes":hashes,
           "calculationKinds":list(KINDS),"dataAccess":"caller-provided-only",
           "sourceAuthenticityChecked":False,"independentReexecutionPerformed":False},
       "verifiedCDR":False,"verifiedAdditionality":False,"verifiedPermanence":False,
       "netDurableAtmosphericRemoval":None}
    output["calculationObjectHash"]=content_hash(output)
    return output

@router.get("/erw/v0.8.0/status")
def status():
    return {"ok":True,"extension":"erw","extensionVersion":"0.8.0","workbenchVersion":APP_VERSION,
            "publicationEnabled":False,"verifiedCDR":False}

@router.post("/erw/v0.8.0/compose")
def draft(req:ReportRequest):return {"ok":True,"report":compose(req)}

@router.post("/erw/v0.8.0/projects/compose")
def save_draft(req:SaveReportRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    project=get_project(req.projectId,owner)
    if project.get("metadata",{}).get("researchId")!=PROJECT_KEY:
        raise HTTPException(422,detail="Not ERW project")
    report=compose(ReportRequest(**req.model_dump(exclude={"projectId"})))
    saved=save_calculation(SavedCalculationCreateRequest(
        projectId=req.projectId,title="ERW 0.8 unpublished academic research draft",
        calculationObject=report,tags=["erw","academic-report","draft","not-verified-cdr"],
        metadata={"researchId":PROJECT_KEY,"publicationStatus":"disabled"}),owner)
    return {"ok":True,"report":report,"saved":saved}

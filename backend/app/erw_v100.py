"""ERW 1.0 — consolidated internal research-package certification manifest.

Never certifies field CDR, external evidence, peer review, or permission to publish.
"""
from __future__ import annotations
from typing import Any,Optional
from fastapi import APIRouter,HTTPException,Header
from pydantic import BaseModel,Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import _owner,get_project,save_calculation,SavedCalculationCreateRequest
from .erw_v010 import PROJECT_KEY
from .erw_v080 import KINDS, EXPECTED
from .erw_v090 import AuditRequest,audit as recompute_audit

router=APIRouter(tags=["erw-1.0.0"])
REQUIRED=(*KINDS,"report","audit")
SCHEMAS={**EXPECTED,"report":"sc.erw.academic-report.v0.8.0",
                  "audit":"sc.erw.scientific-integrity-audit.v0.9.0"}
class CertificationRequest(BaseModel):
    researchId:str=PROJECT_KEY
    objects:dict[str,dict[str,Any]]
    sourceReference:str=Field(min_length=1,max_length=1200)
class SaveCertificationRequest(CertificationRequest):
    projectId:str=Field(min_length=1,max_length=100)

def certify(req:CertificationRequest):
    if req.researchId!=PROJECT_KEY:raise HTTPException(422,detail="Invalid ERW study")
    if set(req.objects)!=set(REQUIRED):raise HTTPException(422,detail="Exactly eight ERW objects required")
    hashes={};gates=[];issues=[]
    def gate(name,ok,detail=""):
        gates.append({"gate":name,"passed":bool(ok),"detail":detail})
        if not ok:issues.append(name)
    for kind in REQUIRED:
        obj=req.objects[kind]
        gate("schema-"+kind,obj.get("schema")==SCHEMAS[kind])
        if kind!="geochemistry":gate("research-"+kind,obj.get("researchId")==PROJECT_KEY)
        claimed=obj.get("calculationObjectHash")
        valid=isinstance(claimed,str) and len(claimed)>=16
        gate("hash-present-"+kind,valid)
        actual=content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"})
        gate("hash-content-"+kind,valid and actual==claimed)
        hashes[kind]=claimed
    report=req.objects["report"];audit_obj=req.objects["audit"]
    gate("report-source-lineage",report.get("sourceHashes")=={k:hashes[k] for k in KINDS})
    gate("audit-source-lineage",audit_obj.get("sourceHashes")=={k:hashes[k] for k in KINDS})
    gate("audit-report-lineage",audit_obj.get("reportHash")==hashes["report"])
    gate("scenario-geochemistry",req.objects["scenario"].get("inputs",{}).get("compositionCalculationHash")==hashes["geochemistry"])
    gate("lifecycle-scenario",req.objects["lifecycle"].get("sourceScenarioCalculationHash")==hashes["scenario"])
    un=req.objects["uncertainty"].get("lineage",{})
    gate("uncertainty-scenario",un.get("scenarioCalculationHash")==hashes["scenario"])
    gate("uncertainty-lifecycle",un.get("lifecycleCalculationHash")==hashes["lifecycle"])
    vis=req.objects["visualization"]
    gate("visualization-lineage",vis.get("sourceHashes")=={k:hashes[k] for k in ("scenario","lifecycle","uncertainty")})
    gate("diagram-lineage",req.objects["diagrams"].get("sourceVisualHash")==hashes["visualization"])
    gate("manuscript-completeness",len(report.get("sections",[]))==7 and len(report.get("figures",[]))==5 and len(report.get("equations",[]))==4)
    gate("report-unpublished",report.get("status")=="draft-unpublished" and report.get("publicationEnabled") is False and report.get("outboundSubmissionEnabled") is False)
    gate("audit-unpublished",audit_obj.get("publicationEnabled") is False and audit_obj.get("outboundSubmissionEnabled") is False and audit_obj.get("publicationReadiness")=="not-ready")
    gate("audit-nonverification",audit_obj.get("independentScientificVerification") is False and audit_obj.get("externalSourceAuthenticityVerified") is False)
    for kind in ("report","audit"):
        o=req.objects[kind]
        gate("cdrlimit-"+kind,o.get("verifiedCDR") is False and o.get("netDurableAtmosphericRemoval") is None)
    # Recompute audit findings from the supplied report and sources. The caller cannot
    # pass an altered audit status or a forged clean audit without detection.
    a_req=AuditRequest(report=report,sourceObjects={k:req.objects[k] for k in KINDS},
                       claims=[],reviewerNote=audit_obj.get("reviewerNote") or "Recheck")
    recheck=recompute_audit(a_req)
    gate("audit-recomputed-lineage",recheck.get("sourceHashes")==audit_obj.get("sourceHashes"))
    gate("no-blocking-findings",not any(f.get("severity")=="blocker" for f in recheck["findings"]))
    # A stored audit may contain caller-supplied claim entries not passed here; do not
    # falsely mark the claim trace as independently verified.
    gate("audit-claim-references",all(set(t.get("sourceHashes",{}).values()).issubset(set(hashes.values())) for t in audit_obj.get("claimTrace",[])))
    out={"schema":"sc.erw.research-certification-manifest.v1.0.0","researchId":PROJECT_KEY,
         "workbenchVersion":APP_VERSION,"sourceReference":req.sourceReference,
         "inputHashes":hashes,"gates":gates,"failedGates":issues,
         "internalCertificationStatus":"pass-with-limitations" if not issues else "blocked",
         "productionPersistenceCertified":False,"researchPackageExportCertified":False,
         "externalAuthenticityVerified":False,"independentScientificValidation":False,
         "publicationReadiness":"not-ready","publicationEnabled":False,
         "outboundSubmissionEnabled":False,"verifiedCDR":False,"verifiedAdditionality":False,
         "verifiedPermanence":False,"netDurableAtmosphericRemoval":None,
         "scientificLimit":"Internal consistency manifest only; authenticated save/export certification is a separate live test."}
    out["calculationObjectHash"]=content_hash(out)
    return out
@router.get("/erw/v1.0.0/status")
def status():return {"ok":True,"extension":"erw","extensionVersion":"1.0.0",
                       "workbenchVersion":APP_VERSION,"publicationEnabled":False,"verifiedCDR":False}
@router.post("/erw/v1.0.0/certify")
def preview(req:CertificationRequest):return {"ok":True,"manifest":certify(req)}
@router.post("/erw/v1.0.0/projects/certify")
def save_manifest(req:SaveCertificationRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    project=get_project(req.projectId,owner)
    if project.get("metadata",{}).get("researchId")!=PROJECT_KEY:raise HTTPException(422,detail="Not ERW project")
    obj=certify(CertificationRequest(**req.model_dump(exclude={"projectId"})))
    if obj["failedGates"]:raise HTTPException(422,detail={"failedGates":obj["failedGates"]})
    saved=save_calculation(SavedCalculationCreateRequest(
        projectId=req.projectId,title="ERW 1.0 internal research certification manifest",
        calculationObject=obj,tags=["erw","certification-manifest","not-verified-cdr"],
        metadata={"researchId":PROJECT_KEY,"publicationStatus":"disabled"}),owner)
    return {"ok":True,"manifest":obj,"saved":saved}

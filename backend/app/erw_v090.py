"""ERW 0.9: deterministic internal integrity and publication-readiness audit.

Audits caller-supplied objects only. No independent source authentication, scientific
certification, outbound publication, or side effects except owner-scoped save endpoint.
"""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import _owner, get_project, save_calculation, SavedCalculationCreateRequest
from .erw_v010 import PROJECT_KEY
from .erw_v080 import KINDS, EXPECTED

router=APIRouter(tags=["erw-0.9.0"])
class Claim(BaseModel):
    claimId:str=Field(min_length=1,max_length=100,pattern=r"^[A-Za-z0-9_-]+$")
    statement:str=Field(min_length=8,max_length=2000)
    sourceKinds:list[str]=Field(min_length=1,max_length=6)
    evidenceStatus:str=Field(pattern=r"^(hypothetical|derived|unverified|independently-verified)$")
    limitations:str=Field(min_length=8,max_length=1200)

class AuditRequest(BaseModel):
    researchId:str=PROJECT_KEY
    report:dict[str,Any]
    sourceObjects:dict[str,dict[str,Any]]
    claims:list[Claim]=Field(default_factory=list,max_length=100)
    reviewerNote:str=Field(min_length=1,max_length=1200)

class SaveAuditRequest(AuditRequest):
    projectId:str=Field(min_length=1,max_length=100)

def audit(req:AuditRequest):
    if req.researchId!=PROJECT_KEY:raise HTTPException(422,detail="Invalid research ID")
    rep=req.report
    if rep.get("schema")!="sc.erw.academic-report.v0.8.0" or rep.get("researchId")!=PROJECT_KEY:
        raise HTTPException(422,detail="Academic report v0.8 required")
    if set(req.sourceObjects)!=set(KINDS):raise HTTPException(422,detail="Exactly six source objects required")
    hashes={}
    findings=[]
    for kind in KINDS:
        obj=req.sourceObjects[kind]
        if obj.get("schema")!=EXPECTED[kind]:
            raise HTTPException(422,detail=kind+" schema mismatch")
        if kind!="geochemistry" and obj.get("researchId")!=PROJECT_KEY:
            raise HTTPException(422,detail=kind+" research ID mismatch")
        h=obj.get("calculationObjectHash")
        if not isinstance(h,str) or len(h)<16:raise HTTPException(422,detail=kind+" hash invalid")
        hashes[kind]=h
        # Source object digests cannot be independently verified just by trusting supplied hash.
        if content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"})!=h:
            findings.append({"id":"source-hash-"+kind,"severity":"blocker",
                             "description":"Caller-supplied source object digest mismatch"})
    report_hash=rep.get("calculationObjectHash")
    if not isinstance(report_hash,str) or len(report_hash)<16:
        raise HTTPException(422,detail="Report hash missing")
    if content_hash({k:v for k,v in rep.items() if k!="calculationObjectHash"})!=report_hash:
        findings.append({"id":"report-hash","severity":"blocker","description":"Report digest mismatch"})
    if rep.get("sourceHashes")!=hashes:
        findings.append({"id":"report-lineage","severity":"blocker","description":"Report lineage differs from supplied sources"})
    if rep.get("publicationEnabled") is not False or rep.get("outboundSubmissionEnabled") is not False:
        findings.append({"id":"publication-gate","severity":"blocker","description":"Publication disabled flags are required"})
    if rep.get("verifiedCDR") is not False or rep.get("netDurableAtmosphericRemoval") is not None:
        findings.append({"id":"removal-gate","severity":"blocker","description":"No verified carbon removal permitted"})
    if len(rep.get("sections",[]))!=7 or len(rep.get("figures",[]))!=5 or len(rep.get("equations",[]))!=4:
        findings.append({"id":"manuscript-structure","severity":"blocker","description":"Expected manuscript sections or figure/equation references missing"})
    if rep.get("sourceIntegrityVerified") is not False:
        findings.append({"id":"integrity-claim","severity":"blocker","description":"Report must not assert independently verified source integrity"})
    claim_trace=[];seen=set()
    for c in req.claims:
        if c.claimId in seen:raise HTTPException(422,detail="Duplicate claim ID")
        seen.add(c.claimId)
        if len(set(c.sourceKinds))!=len(c.sourceKinds) or any(k not in KINDS for k in c.sourceKinds):
            raise HTTPException(422,detail="Unrecognized or repeated source kind")
        if c.evidenceStatus=="independently-verified":
            findings.append({"id":"claim-"+c.claimId,"severity":"blocker","description":"Independent verification is not demonstrated by caller-supplied references"})
        claim_trace.append({"claimId":c.claimId,"statement":c.statement,
            "sourceHashes":{k:hashes[k] for k in c.sourceKinds},
            "assertedEvidenceStatus":c.evidenceStatus,
            "independentVerificationPerformed":False,"limitations":c.limitations})
    if not claim_trace:
        findings.append({"id":"claims-missing","severity":"warning","description":"No claim-to-evidence trace supplied"})
    findings.extend([
      {"id":"external-authenticity","severity":"warning","description":"External references not authenticated independently"},
      {"id":"independent-reexecution","severity":"warning","description":"Original computation not independently re-executed"},
      {"id":"field-evidence","severity":"warning","description":"Physical weathering and permanence not independently established"}])
    blockers=sum(f["severity"]=="blocker" for f in findings)
    out={"schema":"sc.erw.scientific-integrity-audit.v0.9.0",
         "researchId":PROJECT_KEY,"workbenchVersion":APP_VERSION,
         "reportHash":report_hash,"sourceHashes":hashes,
         "claimTrace":claim_trace,"findings":findings,
         "internalConsistency":"blocked" if blockers else "pass-with-limitations",
         "publicationReadiness":"not-ready",
         "publicationEnabled":False,"outboundSubmissionEnabled":False,
         "independentScientificVerification":False,"independentReexecutionPerformed":False,
         "externalSourceAuthenticityVerified":False,"verifiedCDR":False,
         "verifiedAdditionality":False,"verifiedPermanence":False,
         "netDurableAtmosphericRemoval":None,
         "reviewerNote":req.reviewerNote,
         "scientificLimit":"Internal digest and reference checks do not verify real-world evidence or constitute publication approval."}
    out["calculationObjectHash"]=content_hash(out)
    return out

@router.get("/erw/v0.9.0/status")
def status():return {"ok":True,"extension":"erw","extensionVersion":"0.9.0","workbenchVersion":APP_VERSION,"publicationEnabled":False,"verifiedCDR":False}

@router.post("/erw/v0.9.0/audit")
def preview(req:AuditRequest):return {"ok":True,"audit":audit(req)}

@router.post("/erw/v0.9.0/projects/audit")
def save_audit(req:SaveAuditRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    project=get_project(req.projectId,owner)
    if project.get("metadata",{}).get("researchId")!=PROJECT_KEY:raise HTTPException(422,detail="Not an ERW project")
    obj=audit(AuditRequest(**req.model_dump(exclude={"projectId"})))
    saved=save_calculation(SavedCalculationCreateRequest(
        projectId=req.projectId,title="ERW 0.9 internal scientific integrity audit",
        calculationObject=obj,tags=["erw","scientific-audit","not-publication-ready","not-verified-cdr"],
        metadata={"researchId":PROJECT_KEY,"publicationStatus":"disabled"}),owner)
    return {"ok":True,"audit":obj,"saved":saved}

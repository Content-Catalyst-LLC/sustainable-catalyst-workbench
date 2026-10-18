"""ERW 1.3.3 — owner-scoped, append-only claim-to-PDF evidence annotations.

Page numbers and excerpts are researcher supplied and explicitly unverified.
No PDF text parsing, citation accuracy certification or publication.
"""
from __future__ import annotations
from typing import Optional, Literal
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .erw_v121 import owner_from_auth
from .erw_v110 import project_for
from .erw_v132_sources import source_record
from .v1220 import get_calculation, list_calculations, save_calculation, SavedCalculationCreateRequest
from .v510 import content_hash
from .erw_v010 import PROJECT_KEY
router=APIRouter(tags=["erw-1.3.3-evidence"])
SCHEMA="sc.erw.claim-evidence.v1.3.3"

class EvidenceRequest(BaseModel):
    sourceId: str=Field(min_length=20,max_length=100)
    sectionId: str=Field(min_length=1,max_length=80)
    claim: str=Field(min_length=5,max_length=3000)
    pageReference: str=Field(min_length=1,max_length=120)
    excerpt: str=Field(default="",max_length=3000)
    evidenceClass: Literal["literature-derived","measured","hypothetical","unclassified"]="unclassified"
    assessment: Literal["supports","contradicts","context","uncertain"]="uncertain"
    note: str=Field(default="",max_length=1200)
    excerptCheckedAgainstPdf: bool=False

def claim_record(project_id,owner,req:EvidenceRequest):
    project_for(project_id,owner)
    source=source_record(req.sourceId,project_id,owner)
    obj={"schema":SCHEMA,"researchId":PROJECT_KEY,"projectId":project_id,
         "sourceId":req.sourceId,"sourceSha256":source["sha256"],
         "sectionId":req.sectionId,"claim":req.claim.strip(),
         "pageReference":req.pageReference.strip(),"researcherProvidedExcerpt":req.excerpt.strip(),
         "excerptCheckedAgainstPdf":req.excerptCheckedAgainstPdf,
         "evidenceClass":req.evidenceClass,"assessment":req.assessment,
         "note":req.note.strip(),"machineVerifiedExcerpt":False,
         "pageTextExtracted":False,"claimScientificallyVerified":False,
         "publicationEnabled":False,"verifiedCDR":False,
         "netDurableAtmosphericRemoval":None}
    obj["calculationObjectHash"]=content_hash(obj)
    return obj

def list_evidence(project_id,owner):
    project_for(project_id,owner);records=[]
    for row in list_calculations(project_id,owner):
        obj=row.get("calculationObject",{})
        if obj.get("schema")!=SCHEMA:continue
        if obj.get("calculationObjectHash")!=content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"}):
            continue
        records.append({"id":row["id"],"claim":obj["claim"],"sectionId":obj["sectionId"],
           "sourceId":obj["sourceId"],"pageReference":obj["pageReference"],
           "evidenceClass":obj["evidenceClass"],"assessment":obj["assessment"],
           "excerptCheckedAgainstPdf":obj["excerptCheckedAgainstPdf"],
           "hash":obj["calculationObjectHash"]})
    return records

@router.get("/erw/v1.3.3/status")
def status():
    return {"ok":True,"extensionVersion":"1.3.3","ownerScopedEvidence":True,
        "appendOnlyClaimSnapshots":True,"sourceHashBinding":True,
        "manualPageReferences":True,"researcherExcerptReview":True,
        "machinePdfTextInspection":False,"claimVerification":False,
        "publicationEnabled":False,"verifiedCDR":False}

@router.post("/erw/v1.3.3/projects/{project_id}/evidence")
def create(project_id:str,req:EvidenceRequest,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    obj=claim_record(project_id,owner,req)
    saved=save_calculation(SavedCalculationCreateRequest(projectId=project_id,
       title="Evidence: "+req.claim[:120],calculationObject=obj,
       tags=["erw","evidence","researcher-annotation"],
       metadata={"researchId":PROJECT_KEY,"scientificStatus":"unverified"}),owner)
    return {"ok":True,"id":saved["id"],"evidence":obj}

@router.get("/erw/v1.3.3/projects/{project_id}/evidence")
def listing(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    return {"ok":True,"evidence":list_evidence(project_id,owner)}

@router.get("/erw/v1.3.3/projects/{project_id}/evidence/{evidence_id}")
def detail(project_id:str,evidence_id:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization);project_for(project_id,owner)
    saved=get_calculation(evidence_id,owner)
    if saved.get("projectId")!=project_id:raise HTTPException(404,detail="Evidence not in project")
    obj=saved.get("calculationObject",{})
    if obj.get("schema")!=SCHEMA:raise HTTPException(404,detail="Not a claim-evidence record")
    if obj.get("calculationObjectHash")!=content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"}):
        raise HTTPException(409,detail="Evidence integrity mismatch")
    source=source_record(obj["sourceId"],project_id,owner)
    if source["sha256"]!=obj["sourceSha256"]:raise HTTPException(409,detail="Source PDF fingerprint changed")
    return {"ok":True,"evidence":obj,"sourceFilename":source["filename"]}

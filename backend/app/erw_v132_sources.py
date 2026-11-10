"""ERW 1.3.2 — private research PDF library and reviewed Harvard citations.

PDF bytes are stored in persistent /data and linked to owner-scoped Workbench
objects. Metadata must be entered and reviewed by the researcher; this release
does not invent or independently verify metadata or extract PDF text.
"""
from __future__ import annotations
import hashlib
import os
import re
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from .erw_v121 import owner_from_auth
from .erw_v110 import project_for
from .v1220 import SavedCalculationCreateRequest, save_calculation, get_calculation, list_calculations
from .v510 import content_hash
from .erw_v010 import PROJECT_KEY

router=APIRouter(tags=["erw-1.3.2-pdf-library"])
SCHEMA="sc.erw.pdf-source.v1.3.2"
MAX_PDF=20*1024*1024
DOI=re.compile(r"^10\.\d{4,9}/\S+$",re.I)
class CitationFields(BaseModel):
    authors: list[str]=Field(default_factory=list,max_length=30)
    year: Optional[int]=Field(default=None,ge=1500,le=2200)
    title: str=Field(default="",max_length=500)
    journal: str=Field(default="",max_length=350)
    volume: str=Field(default="",max_length=50)
    issue: str=Field(default="",max_length=50)
    pages: str=Field(default="",max_length=100)
    publisher: str=Field(default="",max_length=200)
    doi: str=Field(default="",max_length=250)
    url: str=Field(default="",max_length=600)
    verifiedByResearcher: bool=False
class CitationRequest(BaseModel):
    sourceId: str=Field(min_length=20,max_length=100)
    fields: CitationFields

def clean(value):
    return " ".join(str(value).strip().split())
def harvard(fields:CitationFields):
    if not fields.verifiedByResearcher:
        return {"reference":None,"inText":None,"warnings":["Researcher must review bibliographic metadata before a final reference is generated"]}
    missing=[k for k,v in (("authors",fields.authors),("year",fields.year),("title",fields.title)) if not v]
    if missing:return {"reference":None,"inText":None,"warnings":["Missing required fields: "+", ".join(missing)]}
    if fields.doi and not DOI.fullmatch(fields.doi.strip().removeprefix("https://doi.org/")):
        raise HTTPException(422,detail="Invalid DOI format")
    names=[clean(n) for n in fields.authors]
    if any(not n or len(n)>150 for n in names):raise HTTPException(422,detail="Invalid author name")
    label=names[0] if len(names)==1 else names[0]+" et al." if len(names)>2 else names[0]+" and "+names[1]
    authors=", ".join(names[:-1])+" and "+names[-1] if len(names)>1 else names[0]
    ref=authors+" ("+str(fields.year)+") '"+clean(fields.title)+"'."
    if fields.journal:ref+=" "+clean(fields.journal)
    if fields.volume:ref+=", "+clean(fields.volume)
    if fields.issue:ref+="("+clean(fields.issue)+")"
    if fields.pages:ref+=", pp. "+clean(fields.pages)
    if fields.publisher and not fields.journal:ref+=" "+clean(fields.publisher)
    ref+="."
    if fields.doi:ref+=" https://doi.org/"+fields.doi.strip().removeprefix("https://doi.org/")
    elif fields.url:ref+=" "+clean(fields.url)
    return {"reference":ref,"inText":"("+label+", "+str(fields.year)+")",
            "warnings":["Harvard styles vary by institution; confirm against UCD instructions. Metadata is researcher-reviewed, not independently verified."]}

def storage(owner,project_id,doc_id):
    try:pid=str(uuid.UUID(project_id));did=str(uuid.UUID(doc_id))
    except ValueError as exc:raise HTTPException(422,detail="Invalid source or project ID") from exc
    root=Path(os.getenv("SCWB_ERW_PDF_DIR","/data/erw-pdf-sources"))
    return root/hashlib.sha256(owner.encode()).hexdigest()[:32]/pid/(did+".pdf")

def source_record(source_id,project_id,owner):
    project_for(project_id,owner)
    row=get_calculation(source_id,owner)
    if row["projectId"]!=project_id:raise HTTPException(404,detail="Source not in this project")
    obj=row.get("calculationObject",{})
    if obj.get("schema")!=SCHEMA:raise HTTPException(404,detail="Not a PDF source")
    if obj.get("calculationObjectHash")!=content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"}):
        raise HTTPException(409,detail="Stored source integrity mismatch")
    return obj

def list_sources(project_id,owner):
    project_for(project_id,owner)
    out=[]
    for row in list_calculations(project_id,owner):
        o=row.get("calculationObject",{})
        if o.get("schema")==SCHEMA:
            out.append({"sourceId":row["id"],"name":o["filename"],"sha256":o["sha256"],
                        "citation":o.get("citation"),"metadataReviewed":o.get("metadataReviewed",False)})
    return out

def validate_pdf(data):
    if len(data)>MAX_PDF or len(data)<8 or not data.startswith(b"%PDF-"):
        raise HTTPException(422,detail="Invalid PDF or size limit exceeded")
    if b"%%EOF" not in data[-4096:]:
        raise HTTPException(422,detail="PDF trailer not found")
    return hashlib.sha256(data).hexdigest()

def save_source(owner,project_id,filename,data,metadata:CitationFields):
    project_for(project_id,owner)
    sha=validate_pdf(data)
    if metadata.verifiedByResearcher:
        harvard(metadata)
    doc_id=str(uuid.uuid4())
    dest=storage(owner,project_id,doc_id)
    dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"wb") as file:file.write(data)
        cited=harvard(metadata)
        record={"schema":SCHEMA,"researchId":PROJECT_KEY,"projectId":project_id,
            "documentId":doc_id,"filename":filename,"sha256":sha,"bytes":len(data),
            "citation":metadata.model_dump(),"formattedCitation":cited,
            "metadataReviewed":metadata.verifiedByResearcher,
            "externallyVerified":False,"textExtracted":False,"ocrPerformed":False,
            "verifiedCDR":False,"netDurableAtmosphericRemoval":None,
            "publicationEnabled":False}
        record["calculationObjectHash"]=content_hash(record)
        saved=save_calculation(SavedCalculationCreateRequest(projectId=project_id,
            title="PDF source: "+filename,calculationObject=record,
            tags=["erw","pdf-source","private"],metadata={"researchId":PROJECT_KEY}),owner)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return {"ok":True,"sourceId":saved["id"],"sha256":sha,
            "formattedCitation":cited,"originalPreserved":True}

@router.get("/erw/v1.3.2/status")
def status():return {"ok":True,"extensionVersion":"1.3.2","privatePdfUpload":True,
    "projectScopedSources":True,"researcherReviewedHarvardFormatting":True,
    "pdfTextExtraction":False,"metadataLookup":False,
    "nativeDocxExport":False,"nativePdfExport":False,
    "automatedCitationInsertion":False,"verifiedCDR":False,"publicationEnabled":False}

@router.post("/erw/v1.3.2/projects/{project_id}/sources")
async def upload(project_id:str,request:Request,
                 authorization:Optional[str]=Header(default=None),
                 x_filename:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    project_for(project_id,owner)
    if request.headers.get("content-type","").split(";")[0].strip()!="application/pdf":
        raise HTTPException(415,detail="application/pdf required")
    filename=re.sub(r"[^a-zA-Z0-9._ -]","_", (x_filename or "source.pdf").split("/")[-1].split("\\")[-1])[:150]
    if not filename.lower().endswith(".pdf"):raise HTTPException(422,detail="PDF filename required")
    data=bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data)>MAX_PDF:raise HTTPException(413,detail="PDF exceeds 20 MiB")
    return save_source(owner,project_id,filename,bytes(data),CitationFields())

@router.get("/erw/v1.3.2/projects/{project_id}/sources")
def sources(project_id:str,authorization:Optional[str]=Header(default=None)):
    return {"ok":True,"sources":list_sources(project_id,owner_from_auth(authorization))}

@router.get("/erw/v1.3.2/projects/{project_id}/sources/{source_id}/pdf")
def original(project_id:str,source_id:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization);obj=source_record(source_id,project_id,owner)
    path=storage(owner,project_id,obj["documentId"])
    if not path.is_file():raise HTTPException(404,detail="PDF not available")
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=obj["sha256"]:raise HTTPException(409,detail="PDF SHA-256 mismatch")
    return Response(content=data,media_type="application/pdf",
        headers={"Content-Disposition":"inline; filename=research-source.pdf",
                 "Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"})

@router.post("/erw/v1.3.2/projects/{project_id}/citations")
def create_citation(project_id:str,req:CitationRequest,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    obj=source_record(req.sourceId,project_id,owner)
    formatted=harvard(req.fields)
    if not formatted["reference"]:raise HTTPException(422,detail="Review and complete required citation fields")
    # Append-only citation approval snapshot; original upload record not mutated.
    new={"schema":"sc.erw.approved-citation.v1.3.2","researchId":PROJECT_KEY,
         "projectId":project_id,"sourceId":req.sourceId,
         "sourceSha256":obj["sha256"],"fields":req.fields.model_dump(),
         "formattedCitation":formatted,"metadataReviewed":True,
         "externalVerification":False,"verifiedCDR":False,
         "netDurableAtmosphericRemoval":None,"publicationEnabled":False}
    new["calculationObjectHash"]=content_hash(new)
    saved=save_calculation(SavedCalculationCreateRequest(projectId=project_id,
      title="Harvard reference: "+req.fields.title,calculationObject=new,
      tags=["erw","citation","researcher-reviewed"],
      metadata={"researchId":PROJECT_KEY}),owner)
    return {"ok":True,"citationId":saved["id"],"formattedCitation":formatted}

"""ERW 1.3.1 — owner-scoped DOCX intake and conservative text extraction.

Retains original DOCX bytes in /data; creates an immutable Workbench source
record and returns editable plain-text sections. No OCR, binary execution,
macro support, or claims that complete Word formatting can round-trip.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import re
import uuid
import zipfile
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET
from fastapi import APIRouter, Header, HTTPException, Request
from .erw_v121 import owner_from_auth
from .erw_v110 import project_for
from .erw_v010 import PROJECT_KEY
from .v510 import content_hash
from .v1220 import SavedCalculationCreateRequest, save_calculation

router=APIRouter(tags=["erw-1.3.1-word-import"])
MAX_DOCX=8*1024*1024
MAX_XML=12*1024*1024
MAX_TOTAL_UNCOMPRESSED=45*1024*1024
W="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DOCX_MEDIA="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
SCHEMA="sc.erw.word-source.v1.3.1"

def safe_filename(raw:str)->str:
    name=raw.rsplit("/",1)[-1].rsplit("\\",1)[-1]
    name=re.sub(r"[^A-Za-z0-9._ -]","_",name).strip(" .")
    if not name.lower().endswith(".docx") or not name or len(name)>160:
        raise HTTPException(422,detail="Upload a .docx file (legacy .doc is not supported)")
    return name

def extract_docx(blob:bytes):
    if not blob.startswith(b"PK") or len(blob)>MAX_DOCX:
        raise HTTPException(422,detail="Invalid or oversized DOCX file")
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            info=archive.infolist()
            if len(info)>1500 or sum(i.file_size for i in info)>MAX_TOTAL_UNCOMPRESSED:
                raise HTTPException(422,detail="DOCX archive exceeds extraction limits")
            if any(i.flag_bits & 1 for i in info):
                raise HTTPException(422,detail="Encrypted DOCX not supported")
            names=set(archive.namelist())
            if "word/document.xml" not in names or "[Content_Types].xml" not in names:
                raise HTTPException(422,detail="Not a valid Word document")
            entry=archive.getinfo("word/document.xml")
            if entry.file_size>MAX_XML:
                raise HTTPException(422,detail="Word document text exceeds limits")
            raw=archive.read(entry)
    except (zipfile.BadZipFile,RuntimeError,ValueError,EOFError) as exc:
        raise HTTPException(422,detail="Unreadable DOCX archive") from exc
    try:
        root=ET.fromstring(raw)
    except ET.ParseError as exc:
        raise HTTPException(422,detail="Invalid Word document XML") from exc
    sections=[]
    current={"heading":"Imported manuscript","text":[]}
    paragraphs=0
    for paragraph in root.iter(W+"p"):
        # Only document-level paragraphs, not nested table descendants.
        if any(child.tag==W+"tbl" for child in paragraph):
            continue
        text="".join(t.text or "" for t in paragraph.iter(W+"t")).strip()
        if not text:continue
        paragraphs+=1
        if paragraphs>3500:raise HTTPException(422,detail="Too many Word paragraphs")
        style=paragraph.find("./"+W+"pPr/"+W+"pStyle")
        style_id=style.get(W+"val","") if style is not None else ""
        if re.fullmatch(r"Heading[1-6]",style_id,re.I):
            if current["text"]:sections.append(current)
            current={"heading":text[:200],"text":[]}
        else:current["text"].append(text)
    if current["text"] or not sections:sections.append(current)
    result=[]
    for idx,section in enumerate(sections[:20]):
        body="\n\n".join(section["text"])
        if len(body)>25000:body=body[:25000]
        result.append({"id":"word"+str(idx),"heading":section["heading"],"text":body})
    if not any(s["text"] for s in result):
        raise HTTPException(422,detail="No editable paragraphs found; scanned/image-only documents require separate processing")
    return result,paragraphs

def original_path(owner:str,project_id:str,document_id:str):
    root=Path(os.environ.get("SCWB_ERW_DOCX_DIR","/data/erw-word-documents"))
    owner_dir=hashlib.sha256(owner.encode()).hexdigest()[:32]
    # project ID must have been checked via owner-scoped DB and is restricted to UUID names
    return root/owner_dir/str(uuid.UUID(project_id))/(document_id+".docx")

def store_import(owner:str,project_id:str,filename:str,blob:bytes):
    project_for(project_id,owner)
    sections,count=extract_docx(blob)
    digest=hashlib.sha256(blob).hexdigest()
    document_id=str(uuid.uuid4())
    try:path=original_path(owner,project_id,document_id)
    except (ValueError,AttributeError) as exc:raise HTTPException(422,detail="Invalid project ID") from exc
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,"wb") as f:f.write(blob)
        record={"schema":SCHEMA,"researchId":PROJECT_KEY,"projectId":project_id,
            "originalFilename":filename,"originalSha256":digest,
            "documentId":document_id,"paragraphCount":count,
            "extractedSections":len(sections),
            "importLimitations":"Plain-text paragraphs and Heading styles only; images, tables, footnotes, equations, citations and complex formatting require review.",
            "publicationEnabled":False,"verifiedCDR":False,
            "netDurableAtmosphericRemoval":None}
        record["calculationObjectHash"]=content_hash(record)
        saved=save_calculation(SavedCalculationCreateRequest(
            projectId=project_id,title="Uploaded Word source: "+filename,
            calculationObject=record,tags=["erw","word-source","unpublished"],
            metadata={"researchId":PROJECT_KEY,"wordDocumentId":document_id}),owner)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return {"ok":True,"sourceId":saved["id"],"documentId":document_id,
        "filename":filename,"sha256":digest,"sections":sections,
        "originalPreserved":True,"formattingFullyPreserved":False,
        "warnings":[record["importLimitations"]]}

@router.post("/erw/v1.3.1/projects/{project_id}/word-import")
async def word_import(project_id:str,request:Request,
                      authorization:Optional[str]=Header(default=None),
                      x_filename:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    project_for(project_id,owner)
    if request.headers.get("content-type","").split(";")[0].strip()!=DOCX_MEDIA:
        raise HTTPException(415,detail="DOCX content type required")
    name=safe_filename(x_filename or "manuscript.docx")
    declared=request.headers.get("content-length")
    if declared and (not declared.isdigit() or int(declared)>MAX_DOCX):
        raise HTTPException(413,detail="DOCX exceeds 8 MiB limit")
    data=bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data)>MAX_DOCX:raise HTTPException(413,detail="DOCX exceeds 8 MiB limit")
    return store_import(owner,project_id,name,bytes(data))

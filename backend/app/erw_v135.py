"""ERW 1.3.5: reproducible, read-only scientific publication readiness audit.

An audit is NOT a publication authorization. Missing evidence, unsupported
renderers, PDF page verification and human acceptance remain explicit gates.
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from .erw_v121 import owner_from_auth
from .erw_v134_export import get_report, source_parts, make_docx, make_pdf
from .erw_v133_evidence import list_evidence
from .erw_v132_sources import list_sources
from .v510 import content_hash

router=APIRouter(tags=["erw-1.3.5-certification"])
def audit(project_id:str,report_id:str,owner:str,render:bool=False):
    report=get_report(project_id,report_id,owner)
    sections=report.get("sections",[])
    inserts=report.get("inserts",[])
    issues=[];checks=[]
    def gate(name,passed,detail):
        checks.append({"gate":name,"passed":bool(passed),"detail":detail})
        if not passed:issues.append(name)
    gate("manuscript-nonempty",bool(sections) and any(s.get("text","").strip() for s in sections),
         "At least one section must contain manuscript text")
    gate("bibliography-present",bool(report.get("bibliography","").strip()),
         "Bibliography must be reviewed against its underlying sources")
    gate("author-attribution",bool(report.get("authors")),
         "Explicit report authors must be present")
    ids={s.get("id") for s in sections}
    source_errors=[]
    for i,insert in enumerate(inserts):
        if insert.get("sectionId") not in ids:
            source_errors.append("Insert "+str(i)+" has unknown section")
            continue
        try:source_parts(project_id,owner,insert)
        except (HTTPException,KeyError,ValueError) as exc:
            source_errors.append("Insert "+str(i)+" source invalid: "+str(getattr(exc,"detail",exc)))
    gate("source-integrity",not source_errors,source_errors or "All linked insert hashes consistent")
    evidence=list_evidence(project_id,owner)
    source_rows=list_sources(project_id,owner)
    # Claim links are annotations, not proof that an excerpt matches a PDF.
    annotations=[e for e in evidence if e.get("sectionId") in ids]
    gate("evidence-coverage",bool(annotations),
         "At least one section-level claim annotation required; this does not verify factual accuracy")
    gate("pdf-source-library",bool(source_rows),
         "Research project must contain a source PDF, independently reviewed")
    gate("human-document-review",False,
         "Human has not submitted an independently verified export-rendering signoff through this audit")
    gate("pdf-page-text-verification",False,
         "Automated source-page excerpt verification is not implemented")
    gate("citation-style-verification",False,
         "Harvard reference format and bibliography have not been checked against UCD policy")
    rendered={"docx":False,"pdf":False}
    if render and not source_errors:
        for fmt,fn,signature in (("docx",make_docx,b"PK"),("pdf",make_pdf,b"%PDF-")):
            try:
                data=fn(report,project_id,owner)
                rendered[fmt]=data.startswith(signature) and len(data)>500
            except Exception as exc:
                issues.append(fmt+"-render: "+str(type(exc).__name__))
    if render:gate("native-file-generation",all(rendered.values()),"DOCX and PDF binary smoke validation only")
    return {"ok":True,"extensionVersion":"1.3.5","reportId":report_id,
      "reportHash":report["calculationObjectHash"],"projectId":project_id,
      "researchObjects":len(inserts),"pdfSources":len(source_rows),"evidenceAnnotations":len(annotations),
      "checks":checks,"unresolvedGates":issues,"rendered":rendered,
      "automatedChecksPassed":all(x["passed"] for x in checks if x["gate"] not in
          {"human-document-review","pdf-page-text-verification","citation-style-verification"}),
      "publicationCertified":False,"publicationEnabled":False,"verifiedCDR":False,
      "warning":"Readiness audit only. Human review, source-page verification and citation checking remain required."}

@router.get("/erw/v1.3.5/status")
def status():
    return {"ok":True,"extensionVersion":"1.3.5","publicationReadinessAudit":True,
      "immutableReportHashValidation":True,"ownerScoped":True,
      "nativeExportSmokeAudit":True,"publicationCertified":False,
      "publicationEnabled":False,"verifiedCDR":False}

@router.get("/erw/v1.3.5/projects/{project_id}/reports/{report_id}/audit")
def audit_route(project_id:str,report_id:str,render:bool=False,
                authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    return audit(project_id,report_id,owner,render=render)

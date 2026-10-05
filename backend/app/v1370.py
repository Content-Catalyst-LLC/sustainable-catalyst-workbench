"""Workbench v13.7.0 — Reproducibility Package Workspace."""
from __future__ import annotations
import json, sqlite3, time
from typing import Any, Dict, Optional
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1220 import _connection, _owner, _assert_project_owner, _json
from .v1260 import (
    _migrate as _migrate_packages, _assert_package, _package_dict,
    list_packages, get_package, verify_package, replay_package
)
from .v1340 import get_research_session
from .v1360 import timeline_contract

VERSION=APP_VERSION
router=APIRouter(tags=["workbench-v1370-reproducibility-package-workspace"])
STATUS_SCHEMA="sc-workbench-reproducibility-package-workspace-status/1.0"

class PackageUpdateRequest(BaseModel):
    title:Optional[str]=Field(default=None,min_length=1,max_length=240)
    notes:Optional[str]=Field(default=None,max_length=5000)
    researchSessionId:Optional[str]=Field(default=None,max_length=100)
    metadata:Optional[Dict[str,Any]]=None

class PackageWorkspaceReplayRequest(BaseModel):
    comparisonMode:str=Field(default="strict")

def _hash(x): return content_hash(x)

def _ensure_column(conn,table,column,definition):
    cols={r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def _migrate(conn):
    _migrate_packages(conn)
    _ensure_column(conn,"scwb_reproducibility_packages","research_session_id","TEXT")
    _ensure_column(conn,"scwb_reproducibility_packages","integrity_status","TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scwb_repro_packages_session ON scwb_reproducibility_packages(research_session_id,owner_subject,created_at DESC)")

def _workspace_package(row):
    p=_package_dict(row)
    p["researchSessionId"]=row["research_session_id"]
    p["integrityStatus"]=row["integrity_status"] or "unchecked"
    replay=p.get("lastReplay") or {}
    cert=replay.get("certificate") or {}
    p["replaySummary"]={
      "status":p.get("lastReplayStatus") or "not-replayed",
      "reproducible":cert.get("reproducible"),
      "comparisonMode":cert.get("comparisonMode"),
      "runtimeManifestMatch":cert.get("runtimeManifestMatch"),
      "divergenceCount":len(cert.get("divergences") or []),
      "certificateHash":cert.get("certificateHash")
    }
    return p

def workspace_list(project_id,owner):
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,project_id,owner)
        rows=conn.execute("""SELECT * FROM scwb_reproducibility_packages
          WHERE project_id=? AND owner_subject=? ORDER BY updated_at DESC,id""",(project_id,owner)).fetchall()
    return [_workspace_package(r) for r in rows]

def workspace_get(package_id,owner):
    with _connection() as conn:
        _migrate(conn); row=_assert_package(conn,package_id,owner)
    p=_workspace_package(row)
    verification=verify_package(package_id,owner)
    p["verification"]=verification
    return p

def update_package(package_id,req,owner):
    with _connection() as conn:
        _migrate(conn); cur=_assert_package(conn,package_id,owner)
        title=req.title.strip() if req.title is not None else cur["title"]
        notes=req.notes if req.notes is not None else cur["notes"]
        metadata=json.dumps(req.metadata,sort_keys=True) if req.metadata is not None else cur["metadata_json"]
        session_id=req.researchSessionId if req.researchSessionId is not None else cur["research_session_id"]
        if session_id:
            rs=get_research_session(session_id,owner)
            if rs["projectId"]!=cur["project_id"]:
                raise HTTPException(status_code=409,detail="Research session belongs to another project")
        now=int(time.time())
        conn.execute("""UPDATE scwb_reproducibility_packages
          SET title=?,notes=?,metadata_json=?,research_session_id=?,updated_at=?
          WHERE id=? AND owner_subject=?""",(title,notes,metadata,session_id,now,package_id,owner))
        row=_assert_package(conn,package_id,owner)
    return _workspace_package(row)

def verify_and_persist(package_id,owner):
    verification=verify_package(package_id,owner)
    status="verified" if verification["verified"] else "integrity-failed"
    with _connection() as conn:
        _migrate(conn); _assert_package(conn,package_id,owner)
        conn.execute("UPDATE scwb_reproducibility_packages SET integrity_status=?,updated_at=? WHERE id=? AND owner_subject=?",
                     (status,int(time.time()),package_id,owner))
    return verification

def replay_workspace(package_id,mode,owner):
    result=replay_package(package_id,mode,owner)
    cert=result["certificate"]
    p=workspace_get(package_id,owner)
    comparison={
      "schema":"sc-workbench-reproducibility-comparison/1.0",
      "comparisonMode":cert["comparisonMode"],
      "reproducible":cert["reproducible"],
      "envelopeIntegrity":cert["envelopeIntegrity"],
      "requestIntegrity":cert["requestIntegrity"],
      "runtimeManifestMatch":cert["runtimeManifestMatch"],
      "matches":cert["matches"],
      "divergences":cert["divergences"],
      "certificateHash":cert["certificateHash"],
      "source":{
        "calculationObjectHash":p["sourceCalculationObjectHash"],
        "runtimeManifestHash":p["runtimeManifestHash"],
        "requestHash":p["requestHash"]
      },
      "replay":{
        "calculationObjectHash":result["replayedCalculationObject"].get("calculationObjectHash"),
        "runtimeManifestHash":cert["replayRuntimeManifestHash"]
      }
    }
    comparison["comparisonHash"]=_hash(comparison)
    return {"package":p,"comparison":comparison,"replay":result}

def package_export(package_id,owner):
    p=workspace_get(package_id,owner)
    body={
      "schema":"sc-workbench-reproducibility-package-export/1.0",
      "version":VERSION,
      "package":p,
      "exportedAt":int(time.time()),
      "canonicalReplayEngine":"v11.17"
    }
    body["exportHash"]=_hash(body)
    return body

def package_workspace_contract():
    prior=timeline_contract()
    features={
      "packageDetailWorkspace":True,"editablePackageMetadata":True,
      "researchSessionBinding":True,"integrityVerification":True,
      "deterministicReplay":True,"sideBySideReplayComparison":True,
      "certificateInspection":True,"runtimeManifestInspection":True,
      "divergenceInspection":True,"packageExport":True,
      "notebookAttachmentCompatible":True,"timelineIntegrationCompatible":True,
      "canonicalV1117ReplayEnginePreserved":True,"wordpressRequiredFalse":True
    }
    body={"schema":"sc-workbench-reproducibility-package-workspace-contract/1.0",
          "version":VERSION,"v136TimelinePreserved":all(prior["features"].values()),
          "features":features,"wordpressRequired":False}
    body["contractHash"]=_hash(body); return body

def status():
    c=package_workspace_contract()
    checks={"v136TimelinePreserved":c["v136TimelinePreserved"],
            "packageWorkspaceReady":all(c["features"].values()),
            "canonicalReplayEnginePreserved":c["features"]["canonicalV1117ReplayEnginePreserved"],
            "wordpressRequiredFalse":c["wordpressRequired"] is False}
    return {"ok":all(checks.values()),"schema":STATUS_SCHEMA,"version":VERSION,
      "release":"Reproducibility Package Workspace","product":PRODUCT_KEY,"name":PRODUCT_NAME,
      "runtime":RUNTIME_KIND,"wordpressRequired":False,
      "packageWorkspaceReady":all(checks.values()),"checks":checks,
      "contractHash":c["contractHash"]}

@router.get("/v1370/status")
def status_route(): return status()

@router.get("/standalone/v1/reproducibility/workspace/contract")
def contract_route(): return {"ok":True,"version":VERSION,"workspace":package_workspace_contract()}

@router.get("/standalone/v1/projects/{project_id}/reproducibility/workspace")
def workspace_list_route(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); items=workspace_list(project_id,owner)
    return {"ok":True,"version":VERSION,"packages":items,"count":len(items)}

@router.get("/standalone/v1/reproducibility/workspace/{package_id}")
def workspace_get_route(package_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"package":workspace_get(package_id,owner)}

@router.patch("/standalone/v1/reproducibility/workspace/{package_id}")
def workspace_patch_route(package_id:str,req:PackageUpdateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"package":update_package(package_id,req,owner)}

@router.post("/standalone/v1/reproducibility/workspace/{package_id}/verify")
def workspace_verify_route(package_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return verify_and_persist(package_id,owner)

@router.post("/standalone/v1/reproducibility/workspace/{package_id}/replay")
def workspace_replay_route(package_id:str,req:PackageWorkspaceReplayRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,**replay_workspace(package_id,req.comparisonMode,owner)}

@router.get("/standalone/v1/reproducibility/workspace/{package_id}/export")
def workspace_export_route(package_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return JSONResponse(package_export(package_id,owner))

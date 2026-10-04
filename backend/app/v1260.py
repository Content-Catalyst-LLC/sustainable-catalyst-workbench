"""Workbench v12.6.0 — Reproducibility Package Browser.

Adds durable, project-owned reproducibility package records around the canonical
v11.17 replay envelope/certificate engine. Package metadata is persisted in the
existing v12 SQLite store; replay and verification remain delegated to v11.17.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest
from .v11170 import (
    CaptureReplayRequest,
    ReplayEnvelope,
    ReplayRequest,
    capture_replay,
    replay,
)
from .v1210 import require_session
from .v1220 import _connection, _assert_project_owner
from .v510 import content_hash

VERSION=APP_VERSION
STATUS_SCHEMA="sc-workbench-reproducibility-package-browser-status/1.0"
PACKAGE_SCHEMA="sc-workbench-reproducibility-package-record/1.0"

router=APIRouter(tags=["workbench-v1260-reproducibility-package-browser"])


class PackageCreateRequest(BaseModel):
    projectId:str=Field(min_length=1,max_length=100)
    calculationRequest:UnifiedCalculationRequest
    calculationObject:Optional[Dict[str,Any]]=None
    title:str=Field(default="Reproducibility Package",min_length=1,max_length=240)
    notes:str=Field(default="",max_length=5000)
    metadata:Dict[str,Any]=Field(default_factory=dict)


class PackageReplayRequest(BaseModel):
    comparisonMode:str=Field(default="strict")


def _hash(payload:Any)->str:
    return content_hash(payload)


def _owner(authorization:Optional[str]):
    s=require_session(authorization)
    return s["subject"]["id"],s


def _migrate(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS scwb_reproducibility_packages (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        owner_subject TEXT NOT NULL,
        title TEXT NOT NULL,
        notes TEXT NOT NULL DEFAULT '',
        envelope_json TEXT NOT NULL,
        envelope_hash TEXT NOT NULL,
        runtime_manifest_hash TEXT NOT NULL,
        request_hash TEXT NOT NULL,
        source_calculation_object_hash TEXT NOT NULL,
        last_replay_json TEXT,
        last_replay_status TEXT,
        last_replay_at INTEGER,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        FOREIGN KEY(project_id) REFERENCES scwb_projects(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_scwb_repro_packages_project_created
      ON scwb_reproducibility_packages(project_id, created_at DESC);

    CREATE INDEX IF NOT EXISTS idx_scwb_repro_packages_owner_created
      ON scwb_reproducibility_packages(owner_subject, created_at DESC);
    """)


def initialize_store():
    with _connection() as conn:
        _migrate(conn)
        n=conn.execute("SELECT COUNT(*) AS n FROM scwb_reproducibility_packages").fetchone()["n"]
    return {"engine":"sqlite","persistent":True,"packageCount":int(n),"schemaVersion":VERSION}


def _json(s,fallback):
    try: return json.loads(s) if s is not None else fallback
    except Exception: return fallback


def _package_dict(row):
    env=_json(row["envelope_json"],{})
    last=_json(row["last_replay_json"],None)
    body={
      "schema":PACKAGE_SCHEMA,"id":row["id"],"projectId":row["project_id"],
      "title":row["title"],"notes":row["notes"],
      "envelope":env,"envelopeHash":row["envelope_hash"],
      "runtimeManifestHash":row["runtime_manifest_hash"],
      "requestHash":row["request_hash"],
      "sourceCalculationObjectHash":row["source_calculation_object_hash"],
      "lastReplay":last,"lastReplayStatus":row["last_replay_status"],
      "lastReplayAt":row["last_replay_at"],
      "metadata":_json(row["metadata_json"],{}),
      "createdAt":row["created_at"],"updatedAt":row["updated_at"]
    }
    body["packageRecordHash"]=_hash({
      k:v for k,v in body.items() if k not in {"lastReplay","lastReplayStatus","lastReplayAt","packageRecordHash"}
    })
    return body


def _assert_package(conn,pid,owner):
    row=conn.execute(
      "SELECT * FROM scwb_reproducibility_packages WHERE id=? AND owner_subject=?",
      (pid,owner)
    ).fetchone()
    if row is None: raise HTTPException(status_code=404,detail="Reproducibility package not found")
    return row


def create_package(req,owner):
    now=int(time.time()); pid=str(uuid.uuid4())
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,req.projectId,owner)

        captured=capture_replay(CaptureReplayRequest(
          calculationRequest=req.calculationRequest,
          calculationObject=req.calculationObject,
          label=req.title,
          notes=req.notes
        ))
        env=captured["envelope"]
        conn.execute("""INSERT INTO scwb_reproducibility_packages
          (id,project_id,owner_subject,title,notes,envelope_json,envelope_hash,
           runtime_manifest_hash,request_hash,source_calculation_object_hash,
           last_replay_json,last_replay_status,last_replay_at,metadata_json,
           created_at,updated_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (pid,req.projectId,owner,req.title.strip(),req.notes,
           json.dumps(env,sort_keys=True,separators=(",",":")),
           env["envelopeHash"],env["runtimeManifestHash"],env["requestHash"],
           env["sourceCalculationObjectHash"],None,None,None,
           json.dumps(req.metadata,sort_keys=True,separators=(",",":")),now,now))
        row=_assert_package(conn,pid,owner)
    return _package_dict(row)


def list_packages(project_id,owner):
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,project_id,owner)
        rows=conn.execute("""SELECT * FROM scwb_reproducibility_packages
          WHERE project_id=? AND owner_subject=? ORDER BY created_at DESC,id DESC""",
          (project_id,owner)).fetchall()
    return [_package_dict(r) for r in rows]


def get_package(package_id,owner):
    with _connection() as conn:
        _migrate(conn); row=_assert_package(conn,package_id,owner)
    return _package_dict(row)


def verify_package(package_id,owner):
    with _connection() as conn:
        _migrate(conn); row=_assert_package(conn,package_id,owner)
        env=_json(row["envelope_json"],{})
    supplied=env.get("envelopeHash")
    payload={k:v for k,v in env.items() if k!="envelopeHash"}
    calculated=_hash(payload)
    request_hash_ok=env.get("requestHash")==_hash(env.get("request"))
    checks={
      "envelopeHashMatch": supplied==calculated,
      "requestHashMatch": request_hash_ok,
      "runtimeManifestHashPresent": bool(env.get("runtimeManifestHash")),
      "sourceCalculationObjectHashPresent": bool(env.get("sourceCalculationObjectHash")),
    }
    body={
      "ok":True,"schema":"sc-workbench-reproducibility-package-verification/1.0",
      "version":VERSION,"packageId":package_id,
      "verified":all(checks.values()),"checks":checks,
      "envelopeHash":supplied,"calculatedEnvelopeHash":calculated
    }
    body["verificationHash"]=_hash(body)
    return body


def replay_package(package_id,mode,owner):
    if mode not in {"strict","result-only","input-plan-result"}:
        raise HTTPException(status_code=422,detail="Unsupported comparisonMode")
    with _connection() as conn:
        _migrate(conn); row=_assert_package(conn,package_id,owner)
        env=_json(row["envelope_json"],{})
    result=replay(ReplayRequest(
      envelope=ReplayEnvelope.model_validate(env),
      comparisonMode=mode
    ))
    cert=result["certificate"]
    now=int(time.time())
    with _connection() as conn:
        _migrate(conn); _assert_package(conn,package_id,owner)
        conn.execute("""UPDATE scwb_reproducibility_packages
          SET last_replay_json=?,last_replay_status=?,last_replay_at=?,updated_at=?
          WHERE id=? AND owner_subject=?""",
          (json.dumps(result,sort_keys=True,separators=(",",":")),
           "reproducible" if cert["reproducible"] else "divergent",
           now,now,package_id,owner))
    return result


def delete_package(package_id,owner):
    with _connection() as conn:
        _migrate(conn); _assert_package(conn,package_id,owner)
        conn.execute("DELETE FROM scwb_reproducibility_packages WHERE id=? AND owner_subject=?",(package_id,owner))
    return {"ok":True,"deletedPackageId":package_id}


def status():
    store=initialize_store()
    return {
      "ok":True,"schema":STATUS_SCHEMA,"version":VERSION,
      "release":"Reproducibility Package Browser","product":PRODUCT_KEY,
      "runtime":RUNTIME_KIND,"wordpressRequired":False,
      "canonicalReplayEngine":"v11.17 Calculation Provenance, Replay & Reproducibility",
      "storage":store,
      "capabilities":{
        "persistentPackageIndex":True,
        "projectOwnedPackages":True,
        "manifestInspection":True,
        "runtimeManifestInspection":True,
        "packageIntegrityVerification":True,
        "deterministicReplay":True,
        "replayCertification":True,
        "structuredDivergenceInspection":True,
        "lastReplayPersistence":True,
        "wordpressPackageBrowserNotRequired":True
      }
    }


@router.get("/v1260/status")
def status_route(): return status()

@router.post("/standalone/v1/reproducibility/packages")
def create_package_route(req:PackageCreateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"package":create_package(req,owner)}

@router.get("/standalone/v1/projects/{project_id}/reproducibility/packages")
def list_packages_route(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); items=list_packages(project_id,owner)
    return {"ok":True,"version":VERSION,"packages":items,"count":len(items)}

@router.get("/standalone/v1/reproducibility/packages/{package_id}")
def get_package_route(package_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"package":get_package(package_id,owner)}

@router.post("/standalone/v1/reproducibility/packages/{package_id}/verify")
def verify_package_route(package_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return verify_package(package_id,owner)

@router.post("/standalone/v1/reproducibility/packages/{package_id}/replay")
def replay_package_route(package_id:str,req:PackageReplayRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return replay_package(package_id,req.comparisonMode,owner)

@router.delete("/standalone/v1/reproducibility/packages/{package_id}")
def delete_package_route(package_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return delete_package(package_id,owner)

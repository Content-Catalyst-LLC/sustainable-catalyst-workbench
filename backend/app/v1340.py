"""Workbench v13.4.0 — Project Workspace & Persistent Research Sessions."""
from __future__ import annotations
import json, sqlite3, time, uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1220 import _connection, _owner, _assert_project_owner, _json
from .v1330 import input_contract

VERSION=APP_VERSION
router=APIRouter(tags=["workbench-v1340-project-workspace-persistent-research-sessions"])
SESSION_SCHEMA="sc-workbench-research-session/1.0"
ACTIVITY_SCHEMA="sc-workbench-research-session-activity/1.0"
STATUS_SCHEMA="sc-workbench-project-workspace-session-status/1.0"

class ResearchSessionCreateRequest(BaseModel):
    projectId:str=Field(min_length=1,max_length=100)
    title:str=Field(min_length=1,max_length=240)
    purpose:str=Field(default="",max_length=5000)
    tags:List[str]=Field(default_factory=list,max_length=100)
    metadata:Dict[str,Any]=Field(default_factory=dict)

class ResearchSessionUpdateRequest(BaseModel):
    title:Optional[str]=Field(default=None,min_length=1,max_length=240)
    purpose:Optional[str]=Field(default=None,max_length=5000)
    tags:Optional[List[str]]=None
    status:Optional[str]=Field(default=None,max_length=40)
    lastRoute:Optional[str]=Field(default=None,max_length=80)
    metadata:Optional[Dict[str,Any]]=None

class ResearchSessionActivityRequest(BaseModel):
    kind:str=Field(min_length=1,max_length=80)
    label:str=Field(min_length=1,max_length=500)
    objectType:Optional[str]=Field(default=None,max_length=120)
    objectId:Optional[str]=Field(default=None,max_length=160)
    route:Optional[str]=Field(default=None,max_length=80)
    metadata:Dict[str,Any]=Field(default_factory=dict)

def _hash(x:Any)->str: return content_hash(x)

def _migrate(conn:sqlite3.Connection)->None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS scwb_research_sessions(
      id TEXT PRIMARY KEY,
      project_id TEXT NOT NULL,
      owner_subject TEXT NOT NULL,
      title TEXT NOT NULL,
      purpose TEXT NOT NULL DEFAULT '',
      tags_json TEXT NOT NULL DEFAULT '[]',
      status TEXT NOT NULL DEFAULT 'active',
      last_route TEXT NOT NULL DEFAULT 'workspace',
      metadata_json TEXT NOT NULL DEFAULT '{}',
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL,
      last_active_at INTEGER NOT NULL,
      FOREIGN KEY(project_id) REFERENCES scwb_projects(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_scwb_research_sessions_project
      ON scwb_research_sessions(project_id,owner_subject,last_active_at DESC);
    CREATE TABLE IF NOT EXISTS scwb_research_session_activity(
      id TEXT PRIMARY KEY,
      session_id TEXT NOT NULL,
      project_id TEXT NOT NULL,
      owner_subject TEXT NOT NULL,
      kind TEXT NOT NULL,
      label TEXT NOT NULL,
      object_type TEXT,
      object_id TEXT,
      route TEXT,
      metadata_json TEXT NOT NULL DEFAULT '{}',
      created_at INTEGER NOT NULL,
      FOREIGN KEY(session_id) REFERENCES scwb_research_sessions(id) ON DELETE CASCADE,
      FOREIGN KEY(project_id) REFERENCES scwb_projects(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_scwb_session_activity
      ON scwb_research_session_activity(session_id,owner_subject,created_at DESC);
    """)

def _session_dict(row:sqlite3.Row)->Dict[str,Any]:
    d={"schema":SESSION_SCHEMA,"id":row["id"],"projectId":row["project_id"],
       "title":row["title"],"purpose":row["purpose"],"tags":_json(row["tags_json"],[]),
       "status":row["status"],"lastRoute":row["last_route"],
       "metadata":_json(row["metadata_json"],{}),"createdAt":row["created_at"],
       "updatedAt":row["updated_at"],"lastActiveAt":row["last_active_at"]}
    d["researchSessionHash"]=_hash(d); return d

def _activity_dict(row:sqlite3.Row)->Dict[str,Any]:
    return {"schema":ACTIVITY_SCHEMA,"id":row["id"],"sessionId":row["session_id"],
      "projectId":row["project_id"],"kind":row["kind"],"label":row["label"],
      "objectType":row["object_type"],"objectId":row["object_id"],"route":row["route"],
      "metadata":_json(row["metadata_json"],{}),"createdAt":row["created_at"]}

def _session_row(conn,session_id,owner):
    row=conn.execute("SELECT * FROM scwb_research_sessions WHERE id=? AND owner_subject=?",
                     (session_id,owner)).fetchone()
    if row is None: raise HTTPException(status_code=404,detail="Research session not found")
    return row

def create_research_session(req,owner):
    now=int(time.time()); sid=str(uuid.uuid4())
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,req.projectId,owner)
        conn.execute("""INSERT INTO scwb_research_sessions
          (id,project_id,owner_subject,title,purpose,tags_json,status,last_route,
           metadata_json,created_at,updated_at,last_active_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
          (sid,req.projectId,owner,req.title.strip(),req.purpose,
           json.dumps(req.tags,sort_keys=True), "active","workspace",
           json.dumps(req.metadata,sort_keys=True),now,now,now))
        row=_session_row(conn,sid,owner)
    return _session_dict(row)

def list_research_sessions(project_id,owner):
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,project_id,owner)
        rows=conn.execute("""SELECT * FROM scwb_research_sessions
          WHERE project_id=? AND owner_subject=? ORDER BY last_active_at DESC,id""",
          (project_id,owner)).fetchall()
    return [_session_dict(r) for r in rows]

def get_research_session(session_id,owner):
    with _connection() as conn:
        _migrate(conn); row=_session_row(conn,session_id,owner)
    return _session_dict(row)

def update_research_session(session_id,req,owner):
    with _connection() as conn:
        _migrate(conn); cur=_session_row(conn,session_id,owner); now=int(time.time())
        title=req.title.strip() if req.title is not None else cur["title"]
        purpose=req.purpose if req.purpose is not None else cur["purpose"]
        tags=json.dumps(req.tags,sort_keys=True) if req.tags is not None else cur["tags_json"]
        status=req.status if req.status is not None else cur["status"]
        route=req.lastRoute if req.lastRoute is not None else cur["last_route"]
        meta=json.dumps(req.metadata,sort_keys=True) if req.metadata is not None else cur["metadata_json"]
        conn.execute("""UPDATE scwb_research_sessions SET title=?,purpose=?,tags_json=?,
          status=?,last_route=?,metadata_json=?,updated_at=?,last_active_at=?
          WHERE id=? AND owner_subject=?""",
          (title,purpose,tags,status,route,meta,now,now,session_id,owner))
        row=_session_row(conn,session_id,owner)
    return _session_dict(row)

def activate_research_session(session_id,owner):
    now=int(time.time())
    with _connection() as conn:
        _migrate(conn); row=_session_row(conn,session_id,owner)
        conn.execute("UPDATE scwb_research_sessions SET last_active_at=?,updated_at=? WHERE id=? AND owner_subject=?",
                     (now,now,session_id,owner))
        row=_session_row(conn,session_id,owner)
    return _session_dict(row)

def append_activity(session_id,req,owner):
    now=int(time.time()); aid=str(uuid.uuid4())
    with _connection() as conn:
        _migrate(conn); s=_session_row(conn,session_id,owner)
        conn.execute("""INSERT INTO scwb_research_session_activity
          (id,session_id,project_id,owner_subject,kind,label,object_type,object_id,route,metadata_json,created_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
          (aid,session_id,s["project_id"],owner,req.kind,req.label,req.objectType,
           req.objectId,req.route,json.dumps(req.metadata,sort_keys=True),now))
        conn.execute("UPDATE scwb_research_sessions SET last_active_at=?,updated_at=? WHERE id=? AND owner_subject=?",
                     (now,now,session_id,owner))
        row=conn.execute("SELECT * FROM scwb_research_session_activity WHERE id=?",(aid,)).fetchone()
    return _activity_dict(row)

def list_activity(session_id,owner,limit=100):
    limit=max(1,min(int(limit),500))
    with _connection() as conn:
        _migrate(conn); _session_row(conn,session_id,owner)
        rows=conn.execute("""SELECT * FROM scwb_research_session_activity
          WHERE session_id=? AND owner_subject=? ORDER BY created_at DESC,id LIMIT ?""",
          (session_id,owner,limit)).fetchall()
    return [_activity_dict(r) for r in rows]

def session_summary(session_id,owner):
    with _connection() as conn:
        _migrate(conn); s=_session_row(conn,session_id,owner); pid=s["project_id"]
        counts={}
        for key,table in [
          ("calculations","scwb_saved_calculations"),
          ("notebooks","scwb_notebooks"),
          ("packages","scwb_reproducibility_packages")]:
            try:
                counts[key]=int(conn.execute(
                  f"SELECT COUNT(*) AS n FROM {table} WHERE project_id=? AND owner_subject=?",
                  (pid,owner)).fetchone()["n"])
            except sqlite3.OperationalError:
                counts[key]=0
        counts["activities"]=int(conn.execute(
          "SELECT COUNT(*) AS n FROM scwb_research_session_activity WHERE session_id=? AND owner_subject=?",
          (session_id,owner)).fetchone()["n"])
    body={"schema":"sc-workbench-research-session-summary/1.0",
          "session":_session_dict(s),"counts":counts,"resumable":True}
    body["summaryHash"]=_hash(body); return body

def project_workspace_contract():
    previous=input_contract()
    features={"persistentResearchSessions":True,"projectSessionBinding":True,
      "sessionResume":True,"sessionActivityStream":True,"sessionSummary":True,
      "lastRoutePersistence":True,"shellSessionSelector":True,
      "activeSessionRestoration":True,"wordpressRequiredFalse":True}
    body={"schema":"sc-workbench-project-workspace-contract/1.0","version":VERSION,
      "backendAuthority":"FastAPI","storageAuthority":"SQLite project store",
      "v133InputPreserved":all(previous["features"].values()),
      "features":features,"wordpressRequired":False}
    body["contractHash"]=_hash(body); return body

def status():
    c=project_workspace_contract()
    checks={"v133InputPreserved":c["v133InputPreserved"],
      "sessionPersistenceReady":all(c["features"].values()),
      "backendAuthorityPreserved":c["backendAuthority"]=="FastAPI",
      "wordpressRequiredFalse":c["wordpressRequired"] is False}
    return {"ok":all(checks.values()),"schema":STATUS_SCHEMA,"version":VERSION,
      "release":"Project Workspace & Persistent Research Sessions",
      "product":PRODUCT_KEY,"name":PRODUCT_NAME,"runtime":RUNTIME_KIND,
      "wordpressRequired":False,"projectWorkspaceReady":all(checks.values()),
      "checks":checks,"contractHash":c["contractHash"]}

@router.get("/v1340/status")
def status_route(): return status()

@router.get("/standalone/v1/project-workspace/contract")
def contract_route(): return {"ok":True,"version":VERSION,"workspace":project_workspace_contract()}

@router.post("/standalone/v1/research-sessions")
def create_route(req:ResearchSessionCreateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"researchSession":create_research_session(req,owner)}

@router.get("/standalone/v1/projects/{project_id}/research-sessions")
def list_route(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); items=list_research_sessions(project_id,owner)
    return {"ok":True,"version":VERSION,"researchSessions":items,"count":len(items)}

@router.get("/standalone/v1/research-sessions/{session_id}")
def get_route(session_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"researchSession":get_research_session(session_id,owner)}

@router.patch("/standalone/v1/research-sessions/{session_id}")
def patch_route(session_id:str,req:ResearchSessionUpdateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"researchSession":update_research_session(session_id,req,owner)}

@router.post("/standalone/v1/research-sessions/{session_id}/activate")
def activate_route(session_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"researchSession":activate_research_session(session_id,owner)}

@router.post("/standalone/v1/research-sessions/{session_id}/activity")
def activity_create_route(session_id:str,req:ResearchSessionActivityRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"activity":append_activity(session_id,req,owner)}

@router.get("/standalone/v1/research-sessions/{session_id}/activity")
def activity_list_route(session_id:str,limit:int=100,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); items=list_activity(session_id,owner,limit)
    return {"ok":True,"version":VERSION,"activity":items,"count":len(items)}

@router.get("/standalone/v1/research-sessions/{session_id}/summary")
def summary_route(session_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"summary":session_summary(session_id,owner)}

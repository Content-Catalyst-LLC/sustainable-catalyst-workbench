"""Workbench v13.8.0 — Unified Workbench Workspace."""
from __future__ import annotations
from typing import Any, Dict, Optional, Literal
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1220 import _connection, _owner, _assert_project_owner
from .v1340 import get_research_session, project_workspace_contract
from .v1350 import studio_contract
from .v1360 import timeline_contract, unified_project_timeline, session_timeline
from .v1370 import package_workspace_contract, workspace_list

VERSION=APP_VERSION
router=APIRouter(tags=["workbench-v1380-unified-workbench-workspace"])
STATUS_SCHEMA="sc-workbench-unified-workspace-status/1.0"
SURFACES=("calculator","workspace","graphs","history","packages","settings")

class WorkspaceHandoffRequest(BaseModel):
    target:Literal["calculator","workspace","graphs","history","packages","settings"]
    objectType:Optional[str]=Field(default=None,max_length=100)
    objectId:Optional[str]=Field(default=None,max_length=160)
    researchSessionId:Optional[str]=Field(default=None,max_length=100)
    metadata:Dict[str,Any]=Field(default_factory=dict)

def _hash(x): return content_hash(x)

def _count(conn,sql,args):
    try:
        return int(conn.execute(sql,args).fetchone()["n"])
    except Exception:
        return 0

def project_workspace_summary(project_id,owner):
    with _connection() as conn:
        _assert_project_owner(conn,project_id,owner)
        counts={
          "calculations":_count(conn,"SELECT COUNT(*) n FROM scwb_saved_calculations WHERE project_id=? AND owner_subject=?",(project_id,owner)),
          "researchSessions":_count(conn,"SELECT COUNT(*) n FROM scwb_research_sessions WHERE project_id=? AND owner_subject=?",(project_id,owner)),
          "graphs":_count(conn,"SELECT COUNT(*) n FROM scwb_graph_studies WHERE project_id=? AND owner_subject=?",(project_id,owner)),
          "notebooks":_count(conn,"SELECT COUNT(*) n FROM scwb_notebooks WHERE project_id=? AND owner_subject=?",(project_id,owner)),
          "notebookEntries":_count(conn,"SELECT COUNT(*) n FROM scwb_notebook_entries WHERE project_id=? AND owner_subject=?",(project_id,owner)),
          "packages":_count(conn,"SELECT COUNT(*) n FROM scwb_reproducibility_packages WHERE project_id=? AND owner_subject=?",(project_id,owner)),
        }
        last_session=conn.execute("""SELECT * FROM scwb_research_sessions
          WHERE project_id=? AND owner_subject=? ORDER BY last_active_at DESC,id LIMIT 1""",
          (project_id,owner)).fetchone()
        last_calc=conn.execute("""SELECT id,title,created_at FROM scwb_saved_calculations
          WHERE project_id=? AND owner_subject=? ORDER BY created_at DESC,id DESC LIMIT 1""",
          (project_id,owner)).fetchone()
        try:
            last_graph=conn.execute("""SELECT id,title,updated_at FROM scwb_graph_studies
              WHERE project_id=? AND owner_subject=? ORDER BY updated_at DESC,id DESC LIMIT 1""",
              (project_id,owner)).fetchone()
        except Exception: last_graph=None
        try:
            last_notebook=conn.execute("""SELECT id,title,updated_at FROM scwb_notebooks
              WHERE project_id=? AND owner_subject=? ORDER BY updated_at DESC,id DESC LIMIT 1""",
              (project_id,owner)).fetchone()
        except Exception: last_notebook=None
        try:
            last_package=conn.execute("""SELECT id,title,updated_at FROM scwb_reproducibility_packages
              WHERE project_id=? AND owner_subject=? ORDER BY updated_at DESC,id DESC LIMIT 1""",
              (project_id,owner)).fetchone()
        except Exception: last_package=None

    timeline=unified_project_timeline(project_id,owner,12)
    body={
      "schema":"sc-workbench-unified-project-workspace/1.0",
      "version":VERSION,"projectId":project_id,"counts":counts,
      "activeResearchSession":({
        "id":last_session["id"],"title":last_session["title"],
        "purpose":last_session["purpose"],"lastRoute":last_session["last_route"],
        "lastActiveAt":last_session["last_active_at"]
      } if last_session else None),
      "continuations":{
        "calculator":({"id":last_calc["id"],"title":last_calc["title"],"route":"calculator"} if last_calc else None),
        "graphs":({"id":last_graph["id"],"title":last_graph["title"],"route":"graphs"} if last_graph else None),
        "history":({"id":last_notebook["id"],"title":last_notebook["title"],"route":"history"} if last_notebook else None),
        "packages":({"id":last_package["id"],"title":last_package["title"],"route":"packages"} if last_package else None),
      },
      "recentActivity":timeline["items"],
      "surfaces":[
        {"id":"calculator","title":"Calculator","authority":"Calculation Engine","ready":True},
        {"id":"graphs","title":"Graph Studio","authority":"v11.16 + v13.5","ready":True},
        {"id":"history","title":"Notebook & Timeline","authority":"v12.5 + v13.6","ready":True},
        {"id":"packages","title":"Reproducibility","authority":"v11.17 + v13.7","ready":True},
      ],
      "wordpressRequired":False
    }
    body["workspaceHash"]=_hash(body)
    return body

def session_workspace_summary(session_id,owner):
    rs=get_research_session(session_id,owner)
    project=project_workspace_summary(rs["projectId"],owner)
    tl=session_timeline(session_id,owner,12)
    project["schema"]="sc-workbench-unified-session-workspace/1.0"
    project["researchSessionId"]=session_id
    project["researchSession"]=rs
    project["recentActivity"]=tl["items"]
    project["workspaceHash"]=_hash(project)
    return project

def handoff(req,project_id,owner):
    _assert_project_owner_for_handoff(project_id,owner)
    if req.researchSessionId:
        rs=get_research_session(req.researchSessionId,owner)
        if rs["projectId"]!=project_id:
            raise HTTPException(status_code=409,detail="Research session belongs to another project")
    body={
      "schema":"sc-workbench-unified-handoff/1.0","version":VERSION,
      "projectId":project_id,"researchSessionId":req.researchSessionId,
      "target":req.target,"route":f"/{req.target}",
      "objectType":req.objectType,"objectId":req.objectId,
      "metadata":req.metadata,"preservesProjectContext":True,
      "preservesResearchSessionContext":True
    }
    body["handoffHash"]=_hash(body); return body

def _assert_project_owner_for_handoff(project_id,owner):
    with _connection() as conn:
        _assert_project_owner(conn,project_id,owner)

def unified_contract():
    p=project_workspace_contract(); g=studio_contract(); t=timeline_contract(); r=package_workspace_contract()
    features={
      "singleProjectContext":True,"singleResearchSessionContext":True,
      "crossSurfaceHandoffs":True,"continuationCards":True,
      "unifiedCounts":True,"recentActivity":True,
      "calculatorIntegrated":True,"graphStudioIntegrated":all(g["features"].values()),
      "notebookTimelineIntegrated":all(t["features"].values()),
      "reproducibilityIntegrated":all(r["features"].values()),
      "backendAuthoritiesPreserved":True,"standalonePrimary":True,
      "wordpressRequiredFalse":True
    }
    body={"schema":"sc-workbench-unified-workspace-contract/1.0","version":VERSION,
      "v134ProjectWorkspacePreserved":all(p["features"].values()),
      "features":features,"surfaces":list(SURFACES),"wordpressRequired":False}
    body["contractHash"]=_hash(body); return body

def status():
    c=unified_contract()
    checks={
      "projectWorkspacePreserved":c["v134ProjectWorkspacePreserved"],
      "unifiedWorkspaceReady":all(c["features"].values()),
      "backendAuthoritiesPreserved":c["features"]["backendAuthoritiesPreserved"],
      "standalonePrimary":c["features"]["standalonePrimary"],
      "wordpressRequiredFalse":c["wordpressRequired"] is False
    }
    return {"ok":all(checks.values()),"schema":STATUS_SCHEMA,"version":VERSION,
      "release":"Unified Workbench Workspace","product":PRODUCT_KEY,"name":PRODUCT_NAME,
      "runtime":RUNTIME_KIND,"wordpressRequired":False,
      "unifiedWorkspaceReady":all(checks.values()),"checks":checks,
      "contractHash":c["contractHash"]}

@router.get("/v1380/status")
def status_route(): return status()

@router.get("/standalone/v1/unified-workspace/contract")
def contract_route(): return {"ok":True,"version":VERSION,"workspace":unified_contract()}

@router.get("/standalone/v1/projects/{project_id}/unified-workspace")
def project_route(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    return {"ok":True,"version":VERSION,"workspace":project_workspace_summary(project_id,owner)}

@router.get("/standalone/v1/research-sessions/{session_id}/unified-workspace")
def session_route(session_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    return {"ok":True,"version":VERSION,"workspace":session_workspace_summary(session_id,owner)}

@router.post("/standalone/v1/projects/{project_id}/unified-workspace/handoff")
def handoff_route(project_id:str,req:WorkspaceHandoffRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    return {"ok":True,"version":VERSION,"handoff":handoff(req,project_id,owner)}

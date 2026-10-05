"""Workbench v13.6.0 — Notebook, History & Research Timeline Workspace."""
from __future__ import annotations
import json, sqlite3, time, uuid
from typing import Any, Dict, Literal, Optional
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1220 import _connection, _owner, _assert_project_owner, _json
from .v1250 import _assert_notebook, _migrate as _migrate_notebooks
from .v1340 import get_research_session, project_workspace_contract
from .v1350 import studio_contract

VERSION=APP_VERSION
router=APIRouter(tags=["workbench-v1360-notebook-history-research-timeline"])
STATUS_SCHEMA="sc-workbench-notebook-history-research-timeline-status/1.0"
TIMELINE_SCHEMA="sc-workbench-unified-research-timeline/1.0"

class NotebookAttachmentRequest(BaseModel):
    objectType:Literal["calculation","graph","package"]
    objectId:str=Field(min_length=1,max_length=160)
    title:Optional[str]=Field(default=None,max_length=240)
    note:str=Field(default="",max_length=50000)
    researchSessionId:Optional[str]=Field(default=None,max_length=100)
    pinned:bool=False
    metadata:Dict[str,Any]=Field(default_factory=dict)

class StructuredNoteRequest(BaseModel):
    title:str=Field(default="Note",min_length=1,max_length=240)
    markdown:str=Field(default="",max_length=50000)
    researchSessionId:Optional[str]=Field(default=None,max_length=100)
    pinned:bool=False
    metadata:Dict[str,Any]=Field(default_factory=dict)

def _hash(x): return content_hash(x)

def _ensure_column(conn,table,column,definition):
    cols={r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def _migrate(conn):
    _migrate_notebooks(conn)
    _ensure_column(conn,"scwb_notebook_entries","title","TEXT NOT NULL DEFAULT ''")
    _ensure_column(conn,"scwb_notebook_entries","graph_id","TEXT")
    _ensure_column(conn,"scwb_notebook_entries","package_id","TEXT")
    _ensure_column(conn,"scwb_notebook_entries","research_session_id","TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scwb_notebook_entries_session_created ON scwb_notebook_entries(research_session_id,owner_subject,created_at DESC)")

def _assert_object(conn,project_id,owner,object_type,object_id):
    mapping={"calculation":"scwb_saved_calculations","graph":"scwb_graph_studies","package":"scwb_reproducibility_packages"}
    table=mapping[object_type]
    try:
        row=conn.execute(f"SELECT * FROM {table} WHERE id=? AND project_id=? AND owner_subject=?",(object_id,project_id,owner)).fetchone()
    except sqlite3.OperationalError:
        row=None
    if row is None:
        raise HTTPException(status_code=404,detail=f"{object_type.title()} object not found in notebook project")
    return row

def _entry_dict(row):
    body={
      "schema":"sc-workbench-notebook-entry/1.1","id":row["id"],"notebookId":row["notebook_id"],
      "projectId":row["project_id"],"ordinal":row["ordinal"],"kind":row["kind"],
      "title":row["title"] or "","markdown":row["markdown"],
      "savedCalculationId":row["saved_calculation_id"],"graphId":row["graph_id"],
      "packageId":row["package_id"],"researchSessionId":row["research_session_id"],
      "pinned":bool(row["pinned"]),"metadata":_json(row["metadata_json"],{}),
      "createdAt":row["created_at"],"updatedAt":row["updated_at"]
    }
    body["entryHash"]=_hash(body); return body

def create_structured_note(notebook_id,req,owner):
    now=int(time.time()); eid=str(uuid.uuid4())
    with _connection() as conn:
        _migrate(conn); nb=_assert_notebook(conn,notebook_id,owner)
        if req.researchSessionId:
            rs=get_research_session(req.researchSessionId,owner)
            if rs["projectId"]!=nb["project_id"]:
                raise HTTPException(status_code=409,detail="Research session belongs to another project")
        ordinal=int(conn.execute("SELECT COALESCE(MAX(ordinal),0)+1 AS n FROM scwb_notebook_entries WHERE notebook_id=?",(notebook_id,)).fetchone()["n"])
        conn.execute("""INSERT INTO scwb_notebook_entries
          (id,notebook_id,project_id,owner_subject,ordinal,kind,title,markdown,
           saved_calculation_id,graph_id,package_id,research_session_id,pinned,metadata_json,created_at,updated_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (eid,notebook_id,nb["project_id"],owner,ordinal,"note",req.title.strip(),req.markdown,
           None,None,None,req.researchSessionId,1 if req.pinned else 0,json.dumps(req.metadata,sort_keys=True),now,now))
        conn.execute("UPDATE scwb_notebooks SET updated_at=? WHERE id=?",(now,notebook_id))
        row=conn.execute("SELECT * FROM scwb_notebook_entries WHERE id=?",(eid,)).fetchone()
    return _entry_dict(row)

def attach_object(notebook_id,req,owner):
    now=int(time.time()); eid=str(uuid.uuid4())
    with _connection() as conn:
        _migrate(conn); nb=_assert_notebook(conn,notebook_id,owner)
        obj=_assert_object(conn,nb["project_id"],owner,req.objectType,req.objectId)
        if req.researchSessionId:
            rs=get_research_session(req.researchSessionId,owner)
            if rs["projectId"]!=nb["project_id"]:
                raise HTTPException(status_code=409,detail="Research session belongs to another project")
        ordinal=int(conn.execute("SELECT COALESCE(MAX(ordinal),0)+1 AS n FROM scwb_notebook_entries WHERE notebook_id=?",(notebook_id,)).fetchone()["n"])
        calc=req.objectId if req.objectType=="calculation" else None
        graph=req.objectId if req.objectType=="graph" else None
        package=req.objectId if req.objectType=="package" else None
        inferred=req.title or (obj["title"] if "title" in obj.keys() else f"{req.objectType.title()} reference")
        conn.execute("""INSERT INTO scwb_notebook_entries
          (id,notebook_id,project_id,owner_subject,ordinal,kind,title,markdown,
           saved_calculation_id,graph_id,package_id,research_session_id,pinned,metadata_json,created_at,updated_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (eid,notebook_id,nb["project_id"],owner,ordinal,f"{req.objectType}-reference",inferred,req.note,
           calc,graph,package,req.researchSessionId,1 if req.pinned else 0,json.dumps(req.metadata,sort_keys=True),now,now))
        conn.execute("UPDATE scwb_notebooks SET updated_at=? WHERE id=?",(now,notebook_id))
        row=conn.execute("SELECT * FROM scwb_notebook_entries WHERE id=?",(eid,)).fetchone()
    return _entry_dict(row)

def list_extended_entries(notebook_id,owner):
    with _connection() as conn:
        _migrate(conn); _assert_notebook(conn,notebook_id,owner)
        rows=conn.execute("SELECT * FROM scwb_notebook_entries WHERE notebook_id=? AND owner_subject=? ORDER BY pinned DESC,ordinal ASC,id",(notebook_id,owner)).fetchall()
    return [_entry_dict(r) for r in rows]

def _event(kind,object_id,title,created_at,route,object_type=None,session_id=None,metadata=None):
    body={"kind":kind,"id":object_id,"title":title,"createdAt":int(created_at),"route":route,
          "objectType":object_type or kind,"researchSessionId":session_id,"metadata":metadata or {}}
    body["eventHash"]=_hash(body); return body

def unified_project_timeline(project_id,owner,limit=500,kinds=None):
    limit=max(1,min(int(limit),2000)); allowed=set(kinds or []); items=[]
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,project_id,owner)
        for r in conn.execute("SELECT id,title,created_at,metadata_json FROM scwb_saved_calculations WHERE project_id=? AND owner_subject=?",(project_id,owner)).fetchall():
            items.append(_event("calculation",r["id"],r["title"],r["created_at"],"calculator",metadata=_json(r["metadata_json"],{})))
        for r in conn.execute("SELECT * FROM scwb_notebook_entries WHERE project_id=? AND owner_subject=?",(project_id,owner)).fetchall():
            title=r["title"] or r["markdown"][:80] or r["kind"]
            items.append(_event("notebook-entry",r["id"],title,r["created_at"],"history",r["kind"],r["research_session_id"],
              {"notebookId":r["notebook_id"],"savedCalculationId":r["saved_calculation_id"],"graphId":r["graph_id"],"packageId":r["package_id"],"pinned":bool(r["pinned"])}))
        try:
            for r in conn.execute("SELECT id,title,created_at,research_session_id,metadata_json FROM scwb_graph_studies WHERE project_id=? AND owner_subject=?",(project_id,owner)).fetchall():
                items.append(_event("graph",r["id"],r["title"],r["created_at"],"graphs",session_id=r["research_session_id"],metadata=_json(r["metadata_json"],{})))
        except sqlite3.OperationalError: pass
        try:
            for r in conn.execute("""SELECT a.id,a.label,a.created_at,g.research_session_id,g.id AS graph_id
              FROM scwb_graph_annotations a JOIN scwb_graph_studies g ON g.id=a.graph_id
              WHERE g.project_id=? AND a.owner_subject=?""",(project_id,owner)).fetchall():
                items.append(_event("graph-annotation",r["id"],r["label"],r["created_at"],"graphs",session_id=r["research_session_id"],metadata={"graphId":r["graph_id"]}))
        except sqlite3.OperationalError: pass
        try:
            for r in conn.execute("SELECT id,title,created_at,metadata_json FROM scwb_reproducibility_packages WHERE project_id=? AND owner_subject=?",(project_id,owner)).fetchall():
                meta=_json(r["metadata_json"],{})
                items.append(_event("package",r["id"],r["title"],r["created_at"],"packages",session_id=meta.get("researchSessionId"),metadata=meta))
        except sqlite3.OperationalError: pass
        try:
            for r in conn.execute("""SELECT id,session_id,kind,label,object_type,object_id,route,metadata_json,created_at
              FROM scwb_research_session_activity WHERE project_id=? AND owner_subject=?""",(project_id,owner)).fetchall():
                meta={"activityKind":r["kind"],"objectId":r["object_id"],**_json(r["metadata_json"],{})}
                items.append(_event("session-activity",r["id"],r["label"],r["created_at"],r["route"] or "workspace",r["object_type"] or r["kind"],r["session_id"],meta))
        except sqlite3.OperationalError: pass
    if allowed:
        items=[x for x in items if x["kind"] in allowed or x["objectType"] in allowed]
    items.sort(key=lambda x:(x["createdAt"],x["id"]),reverse=True); items=items[:limit]
    body={"schema":TIMELINE_SCHEMA,"scope":"project","projectId":project_id,"count":len(items),"items":items,"filters":{"kinds":sorted(allowed)}}
    body["timelineHash"]=_hash(body); return body

def session_timeline(session_id,owner,limit=500,kinds=None):
    rs=get_research_session(session_id,owner)
    project=unified_project_timeline(rs["projectId"],owner,2000,kinds)
    items=[x for x in project["items"] if x.get("researchSessionId")==session_id][:max(1,min(int(limit),2000))]
    body={"schema":TIMELINE_SCHEMA,"scope":"research-session","projectId":rs["projectId"],"researchSessionId":session_id,
          "count":len(items),"items":items,"filters":project["filters"]}
    body["timelineHash"]=_hash(body); return body

def history_export(session_id,owner):
    tl=session_timeline(session_id,owner,2000); rs=get_research_session(session_id,owner)
    lines=[f"# {rs['title']}","",rs.get("purpose") or "","",f"Research session: `{session_id}`",f"Project: `{rs['projectId']}`",f"Timeline hash: `{tl['timelineHash']}`","","## Research timeline",""]
    for item in reversed(tl["items"]):
        stamp=time.strftime("%Y-%m-%d %H:%M:%S UTC",time.gmtime(item["createdAt"]))
        lines.append(f"- **{stamp}** — `{item['kind']}` — {item['title']}")
    lines+=["","---","Export generated by Sustainable Catalyst Workbench v13.6.0.",""]
    text="\n".join(lines)
    return text,_hash({"sessionId":session_id,"timelineHash":tl["timelineHash"],"text":text})

def timeline_contract():
    prior=project_workspace_contract(); graph=studio_contract()
    features={"structuredNotebookNotes":True,"calculationAttachments":True,"graphAttachments":True,
      "packageAttachments":True,"researchSessionEntryBinding":True,"unifiedProjectTimeline":True,
      "researchSessionTimeline":True,"timelineFiltering":True,"objectNavigationMetadata":True,
      "timelineHashes":True,"humanReadableHistoryExport":True,"existingNotebookCompatibility":True,
      "graphStudioPreserved":all(graph["features"].values()),"wordpressRequiredFalse":True}
    body={"schema":"sc-workbench-notebook-history-timeline-contract/1.0","version":VERSION,
          "v134ProjectWorkspacePreserved":all(prior["features"].values()),"features":features,"wordpressRequired":False}
    body["contractHash"]=_hash(body); return body

def status():
    c=timeline_contract()
    checks={"projectWorkspacePreserved":c["v134ProjectWorkspacePreserved"],"timelineWorkspaceReady":all(c["features"].values()),
      "graphStudioPreserved":c["features"]["graphStudioPreserved"],"wordpressRequiredFalse":c["wordpressRequired"] is False}
    return {"ok":all(checks.values()),"schema":STATUS_SCHEMA,"version":VERSION,
      "release":"Notebook, History & Research Timeline Workspace","product":PRODUCT_KEY,"name":PRODUCT_NAME,
      "runtime":RUNTIME_KIND,"wordpressRequired":False,"timelineWorkspaceReady":all(checks.values()),
      "checks":checks,"contractHash":c["contractHash"]}

@router.get("/v1360/status")
def status_route(): return status()

@router.get("/standalone/v1/research-timeline/contract")
def contract_route(): return {"ok":True,"version":VERSION,"timeline":timeline_contract()}

@router.post("/standalone/v1/notebooks/{notebook_id}/structured-notes")
def structured_note_route(notebook_id:str,req:StructuredNoteRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"entry":create_structured_note(notebook_id,req,owner)}

@router.post("/standalone/v1/notebooks/{notebook_id}/attach")
def attach_route(notebook_id:str,req:NotebookAttachmentRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"attachment":attach_object(notebook_id,req,owner)}

@router.get("/standalone/v1/notebooks/{notebook_id}/research-entries")
def entries_route(notebook_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); items=list_extended_entries(notebook_id,owner)
    return {"ok":True,"version":VERSION,"entries":items,"count":len(items)}

@router.get("/standalone/v1/projects/{project_id}/research-timeline")
def project_timeline_route(project_id:str,limit:int=500,kinds:Optional[str]=None,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); parsed=[x.strip() for x in (kinds or "").split(",") if x.strip()]
    return {"ok":True,"version":VERSION,"timeline":unified_project_timeline(project_id,owner,limit,parsed)}

@router.get("/standalone/v1/research-sessions/{session_id}/timeline")
def session_timeline_route(session_id:str,limit:int=500,kinds:Optional[str]=None,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); parsed=[x.strip() for x in (kinds or "").split(",") if x.strip()]
    return {"ok":True,"version":VERSION,"timeline":session_timeline(session_id,owner,limit,parsed)}

@router.get("/standalone/v1/research-sessions/{session_id}/history-export")
def export_route(session_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); text,export_hash=history_export(session_id,owner)
    return PlainTextResponse(text,headers={"X-SC-Research-History-Hash":export_hash})

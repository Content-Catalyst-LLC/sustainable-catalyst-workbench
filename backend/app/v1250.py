"""Workbench v12.5.0 — Notebook & Calculation History.

Adds durable project notebooks, ordered notebook entries, and calculation
history/timeline APIs to the standalone Workbench application.

Persistence remains in the v12.2 SQLite store. Ownership remains bound to the
v12.1 standalone session subject. Saved CalculationObjects remain canonical.
"""
from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1210 import require_session
from .v1220 import _connection, _assert_project_owner
from .v510 import content_hash

VERSION=APP_VERSION
STATUS_SCHEMA="sc-workbench-notebook-calculation-history-status/1.0"
NOTEBOOK_SCHEMA="sc-workbench-notebook/1.0"
ENTRY_SCHEMA="sc-workbench-notebook-entry/1.0"
HISTORY_SCHEMA="sc-workbench-calculation-history/1.0"

router=APIRouter(tags=["workbench-v1250-notebook-calculation-history"])


class NotebookCreateRequest(BaseModel):
    projectId:str=Field(min_length=1,max_length=100)
    title:str=Field(default="Notebook",min_length=1,max_length=240)
    description:str=Field(default="",max_length=5000)
    metadata:Dict[str,Any]=Field(default_factory=dict)


class NotebookUpdateRequest(BaseModel):
    title:Optional[str]=Field(default=None,min_length=1,max_length=240)
    description:Optional[str]=Field(default=None,max_length=5000)
    metadata:Optional[Dict[str,Any]]=None


class NotebookEntryCreateRequest(BaseModel):
    kind:Literal["note","calculation-reference"]="note"
    markdown:str=Field(default="",max_length=50000)
    savedCalculationId:Optional[str]=Field(default=None,max_length=100)
    pinned:bool=False
    metadata:Dict[str,Any]=Field(default_factory=dict)


class NotebookEntryUpdateRequest(BaseModel):
    markdown:Optional[str]=Field(default=None,max_length=50000)
    pinned:Optional[bool]=None
    metadata:Optional[Dict[str,Any]]=None


def _hash(payload:Any)->str:
    return content_hash(payload)


def _owner(authorization:Optional[str]):
    session=require_session(authorization)
    return session["subject"]["id"],session


def _migrate(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS scwb_notebooks (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        owner_subject TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        FOREIGN KEY(project_id) REFERENCES scwb_projects(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_scwb_notebooks_project_updated
      ON scwb_notebooks(project_id, updated_at DESC);

    CREATE TABLE IF NOT EXISTS scwb_notebook_entries (
        id TEXT PRIMARY KEY,
        notebook_id TEXT NOT NULL,
        project_id TEXT NOT NULL,
        owner_subject TEXT NOT NULL,
        ordinal INTEGER NOT NULL,
        kind TEXT NOT NULL,
        markdown TEXT NOT NULL DEFAULT '',
        saved_calculation_id TEXT,
        pinned INTEGER NOT NULL DEFAULT 0,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        FOREIGN KEY(notebook_id) REFERENCES scwb_notebooks(id) ON DELETE CASCADE,
        FOREIGN KEY(project_id) REFERENCES scwb_projects(id) ON DELETE CASCADE,
        FOREIGN KEY(saved_calculation_id) REFERENCES scwb_saved_calculations(id) ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_scwb_notebook_entries_notebook_ordinal
      ON scwb_notebook_entries(notebook_id, ordinal ASC);

    CREATE INDEX IF NOT EXISTS idx_scwb_notebook_entries_project_created
      ON scwb_notebook_entries(project_id, created_at DESC);
    """)


def initialize_notebook_store():
    with _connection() as conn:
        _migrate(conn)
        n=conn.execute("SELECT COUNT(*) AS n FROM scwb_notebooks").fetchone()["n"]
        e=conn.execute("SELECT COUNT(*) AS n FROM scwb_notebook_entries").fetchone()["n"]
    return {"engine":"sqlite","persistent":True,"notebookCount":int(n),"entryCount":int(e),"schemaVersion":VERSION}


def _json(s,fallback):
    try: return json.loads(s)
    except Exception: return fallback


def _notebook_dict(row):
    body={
      "schema":NOTEBOOK_SCHEMA,"id":row["id"],"projectId":row["project_id"],
      "title":row["title"],"description":row["description"],
      "metadata":_json(row["metadata_json"],{}),
      "createdAt":row["created_at"],"updatedAt":row["updated_at"]
    }
    body["notebookHash"]=_hash(body)
    return body


def _entry_dict(row):
    body={
      "schema":ENTRY_SCHEMA,"id":row["id"],"notebookId":row["notebook_id"],
      "projectId":row["project_id"],"ordinal":row["ordinal"],"kind":row["kind"],
      "markdown":row["markdown"],"savedCalculationId":row["saved_calculation_id"],
      "pinned":bool(row["pinned"]),"metadata":_json(row["metadata_json"],{}),
      "createdAt":row["created_at"],"updatedAt":row["updated_at"]
    }
    body["entryHash"]=_hash(body)
    return body


def _assert_notebook(conn,notebook_id,owner):
    row=conn.execute(
      "SELECT * FROM scwb_notebooks WHERE id=? AND owner_subject=?",
      (notebook_id,owner)
    ).fetchone()
    if row is None: raise HTTPException(status_code=404,detail="Notebook not found")
    return row


def create_notebook(req,owner):
    now=int(time.time()); nid=str(uuid.uuid4())
    with _connection() as conn:
        _migrate(conn)
        _assert_project_owner(conn,req.projectId,owner)
        conn.execute("""INSERT INTO scwb_notebooks
          (id,project_id,owner_subject,title,description,metadata_json,created_at,updated_at)
          VALUES (?,?,?,?,?,?,?,?)""",
          (nid,req.projectId,owner,req.title.strip(),req.description,
           json.dumps(req.metadata,sort_keys=True,separators=(",",":")),now,now))
        row=_assert_notebook(conn,nid,owner)
    return _notebook_dict(row)


def list_notebooks(project_id,owner):
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,project_id,owner)
        rows=conn.execute("""SELECT * FROM scwb_notebooks
          WHERE project_id=? AND owner_subject=? ORDER BY updated_at DESC,id""",
          (project_id,owner)).fetchall()
    return [_notebook_dict(r) for r in rows]


def update_notebook(notebook_id,req,owner):
    with _connection() as conn:
        _migrate(conn); cur=_assert_notebook(conn,notebook_id,owner)
        title=req.title.strip() if req.title is not None else cur["title"]
        description=req.description if req.description is not None else cur["description"]
        metadata_json=json.dumps(req.metadata,sort_keys=True,separators=(",",":")) if req.metadata is not None else cur["metadata_json"]
        now=int(time.time())
        conn.execute("""UPDATE scwb_notebooks SET title=?,description=?,metadata_json=?,updated_at=?
          WHERE id=? AND owner_subject=?""",(title,description,metadata_json,now,notebook_id,owner))
        row=_assert_notebook(conn,notebook_id,owner)
    return _notebook_dict(row)


def delete_notebook(notebook_id,owner):
    with _connection() as conn:
        _migrate(conn); _assert_notebook(conn,notebook_id,owner)
        n=conn.execute("SELECT COUNT(*) AS n FROM scwb_notebook_entries WHERE notebook_id=? AND owner_subject=?",(notebook_id,owner)).fetchone()["n"]
        conn.execute("DELETE FROM scwb_notebooks WHERE id=? AND owner_subject=?",(notebook_id,owner))
    return {"ok":True,"deletedNotebookId":notebook_id,"cascadeDeletedEntries":int(n)}


def create_entry(notebook_id,req,owner):
    now=int(time.time()); eid=str(uuid.uuid4())
    with _connection() as conn:
        _migrate(conn); nb=_assert_notebook(conn,notebook_id,owner)
        if req.kind=="calculation-reference":
            if not req.savedCalculationId:
                raise HTTPException(status_code=422,detail="savedCalculationId required for calculation-reference entry")
            calc=conn.execute("""SELECT id FROM scwb_saved_calculations
              WHERE id=? AND project_id=? AND owner_subject=?""",
              (req.savedCalculationId,nb["project_id"],owner)).fetchone()
            if calc is None:
                raise HTTPException(status_code=404,detail="Saved calculation not found in notebook project")
        next_ord=conn.execute("SELECT COALESCE(MAX(ordinal),0)+1 AS n FROM scwb_notebook_entries WHERE notebook_id=?",(notebook_id,)).fetchone()["n"]
        conn.execute("""INSERT INTO scwb_notebook_entries
          (id,notebook_id,project_id,owner_subject,ordinal,kind,markdown,saved_calculation_id,pinned,metadata_json,created_at,updated_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
          (eid,notebook_id,nb["project_id"],owner,int(next_ord),req.kind,req.markdown,
           req.savedCalculationId,1 if req.pinned else 0,
           json.dumps(req.metadata,sort_keys=True,separators=(",",":")),now,now))
        row=conn.execute("SELECT * FROM scwb_notebook_entries WHERE id=?",(eid,)).fetchone()
        conn.execute("UPDATE scwb_notebooks SET updated_at=? WHERE id=?",(now,notebook_id))
    return _entry_dict(row)


def list_entries(notebook_id,owner):
    with _connection() as conn:
        _migrate(conn); _assert_notebook(conn,notebook_id,owner)
        rows=conn.execute("""SELECT * FROM scwb_notebook_entries
          WHERE notebook_id=? AND owner_subject=? ORDER BY pinned DESC, ordinal ASC""",
          (notebook_id,owner)).fetchall()
    return [_entry_dict(r) for r in rows]


def update_entry(entry_id,req,owner):
    with _connection() as conn:
        _migrate(conn)
        cur=conn.execute("SELECT * FROM scwb_notebook_entries WHERE id=? AND owner_subject=?",(entry_id,owner)).fetchone()
        if cur is None: raise HTTPException(status_code=404,detail="Notebook entry not found")
        markdown=req.markdown if req.markdown is not None else cur["markdown"]
        pinned=(1 if req.pinned else 0) if req.pinned is not None else cur["pinned"]
        metadata_json=json.dumps(req.metadata,sort_keys=True,separators=(",",":")) if req.metadata is not None else cur["metadata_json"]
        now=int(time.time())
        conn.execute("""UPDATE scwb_notebook_entries SET markdown=?,pinned=?,metadata_json=?,updated_at=?
          WHERE id=? AND owner_subject=?""",(markdown,pinned,metadata_json,now,entry_id,owner))
        conn.execute("UPDATE scwb_notebooks SET updated_at=? WHERE id=?",(now,cur["notebook_id"]))
        row=conn.execute("SELECT * FROM scwb_notebook_entries WHERE id=?",(entry_id,)).fetchone()
    return _entry_dict(row)


def delete_entry(entry_id,owner):
    with _connection() as conn:
        _migrate(conn)
        row=conn.execute("SELECT notebook_id FROM scwb_notebook_entries WHERE id=? AND owner_subject=?",(entry_id,owner)).fetchone()
        if row is None: raise HTTPException(status_code=404,detail="Notebook entry not found")
        conn.execute("DELETE FROM scwb_notebook_entries WHERE id=? AND owner_subject=?",(entry_id,owner))
        conn.execute("UPDATE scwb_notebooks SET updated_at=? WHERE id=?",(int(time.time()),row["notebook_id"]))
    return {"ok":True,"deletedEntryId":entry_id}


def calculation_history(project_id,owner,limit=200):
    with _connection() as conn:
        _migrate(conn); _assert_project_owner(conn,project_id,owner)
        rows=conn.execute("""SELECT id,title,calculation_object_hash,tags_json,metadata_json,created_at,updated_at
          FROM scwb_saved_calculations WHERE project_id=? AND owner_subject=?
          ORDER BY created_at DESC,id DESC LIMIT ?""",(project_id,owner,int(limit))).fetchall()
    items=[]
    for r in rows:
        items.append({
          "kind":"calculation","id":r["id"],"title":r["title"],
          "calculationObjectHash":r["calculation_object_hash"],
          "tags":_json(r["tags_json"],[]),"metadata":_json(r["metadata_json"],{}),
          "createdAt":r["created_at"],"updatedAt":r["updated_at"]
        })
    body={"schema":HISTORY_SCHEMA,"projectId":project_id,"count":len(items),"items":items}
    body["historyHash"]=_hash(body)
    return body


def project_timeline(project_id,owner,limit=300):
    history=calculation_history(project_id,owner,limit)
    with _connection() as conn:
        _migrate(conn)
        rows=conn.execute("""SELECT e.*,n.title AS notebook_title FROM scwb_notebook_entries e
          JOIN scwb_notebooks n ON n.id=e.notebook_id
          WHERE e.project_id=? AND e.owner_subject=?
          ORDER BY e.created_at DESC,e.id DESC LIMIT ?""",(project_id,owner,int(limit))).fetchall()
    items=[{
      "kind":"notebook-entry","id":r["id"],"notebookId":r["notebook_id"],
      "notebookTitle":r["notebook_title"],"entryKind":r["kind"],
      "markdown":r["markdown"],"savedCalculationId":r["saved_calculation_id"],
      "pinned":bool(r["pinned"]),"createdAt":r["created_at"],"updatedAt":r["updated_at"]
    } for r in rows]
    items.extend(history["items"])
    items.sort(key=lambda x:(x.get("createdAt",0),x.get("id","")),reverse=True)
    items=items[:limit]
    body={"schema":"sc-workbench-project-timeline/1.0","projectId":project_id,"count":len(items),"items":items}
    body["timelineHash"]=_hash(body)
    return body


def status():
    store=initialize_notebook_store()
    return {
      "ok":True,"schema":STATUS_SCHEMA,"version":VERSION,
      "release":"Notebook & Calculation History","product":PRODUCT_KEY,
      "runtime":RUNTIME_KIND,"wordpressRequired":False,"storage":store,
      "capabilities":{
        "persistentNotebooks":True,"orderedNotebookEntries":True,
        "noteEntries":True,"calculationReferenceEntries":True,
        "pinnedEntries":True,"calculationHistory":True,
        "projectTimeline":True,"sessionSubjectOwnership":True,
        "projectScopedHistory":True,"calculationObjectReferencesPreserved":True,
        "wordpressHistoryNotRequired":True
      }
    }


@router.get("/v1250/status")
def status_route(): return status()

@router.post("/standalone/v1/notebooks")
def create_notebook_route(req:NotebookCreateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"notebook":create_notebook(req,owner)}

@router.get("/standalone/v1/projects/{project_id}/notebooks")
def list_notebooks_route(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); items=list_notebooks(project_id,owner)
    return {"ok":True,"version":VERSION,"notebooks":items,"count":len(items)}

@router.patch("/standalone/v1/notebooks/{notebook_id}")
def update_notebook_route(notebook_id:str,req:NotebookUpdateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"notebook":update_notebook(notebook_id,req,owner)}

@router.delete("/standalone/v1/notebooks/{notebook_id}")
def delete_notebook_route(notebook_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return delete_notebook(notebook_id,owner)

@router.post("/standalone/v1/notebooks/{notebook_id}/entries")
def create_entry_route(notebook_id:str,req:NotebookEntryCreateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"entry":create_entry(notebook_id,req,owner)}

@router.get("/standalone/v1/notebooks/{notebook_id}/entries")
def list_entries_route(notebook_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); items=list_entries(notebook_id,owner)
    return {"ok":True,"version":VERSION,"entries":items,"count":len(items)}

@router.patch("/standalone/v1/notebook-entries/{entry_id}")
def update_entry_route(entry_id:str,req:NotebookEntryUpdateRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"entry":update_entry(entry_id,req,owner)}

@router.delete("/standalone/v1/notebook-entries/{entry_id}")
def delete_entry_route(entry_id:str,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return delete_entry(entry_id,owner)

@router.get("/standalone/v1/projects/{project_id}/history")
def history_route(project_id:str,limit:int=200,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"history":calculation_history(project_id,owner,min(max(limit,1),1000))}

@router.get("/standalone/v1/projects/{project_id}/timeline")
def timeline_route(project_id:str,limit:int=300,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization); return {"ok":True,"version":VERSION,"timeline":project_timeline(project_id,owner,min(max(limit,1),1000))}

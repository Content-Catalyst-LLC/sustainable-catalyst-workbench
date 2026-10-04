"""Workbench v12.2.0 — Persistent Calculation & Project Store.

Standalone, backend-owned persistence for projects and saved CalculationObjects.
SQLite is the production-ready default for the current single-node Contabo
deployment. The public repository contract remains storage-engine neutral so
PostgreSQL can replace SQLite later without changing API clients.

Ownership is derived from the v12.1 signed session subject, never WordPress.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1210 import require_session
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-persistent-project-store-status/1.0"
PROJECT_SCHEMA = "sc-workbench-project/1.0"
CALCULATION_SCHEMA = "sc-workbench-saved-calculation/1.0"
STORE_SCHEMA = "sc-workbench-project-store/1.0"

router = APIRouter(tags=["workbench-v1220-persistent-calculation-project-store"])

DEFAULT_DB_PATH = "/data/workbench-v12.sqlite3"


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=5000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=240)
    description: Optional[str] = Field(default=None, max_length=5000)
    metadata: Optional[Dict[str, Any]] = None


class SavedCalculationCreateRequest(BaseModel):
    projectId: str = Field(min_length=1, max_length=100)
    title: str = Field(default="Calculation", min_length=1, max_length=240)
    calculationObject: Dict[str, Any]
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _hash(payload: Any) -> str:
    return content_hash(payload)


def _db_path() -> Path:
    configured = os.getenv("SCWB_PROJECT_STORE_PATH", "").strip()
    return Path(configured or DEFAULT_DB_PATH)


@contextmanager
def _connection():
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        _migrate(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS scwb_projects (
        id TEXT PRIMARY KEY,
        owner_subject TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_scwb_projects_owner_updated
        ON scwb_projects(owner_subject, updated_at DESC);

    CREATE TABLE IF NOT EXISTS scwb_saved_calculations (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        owner_subject TEXT NOT NULL,
        title TEXT NOT NULL,
        calculation_object_json TEXT NOT NULL,
        calculation_object_hash TEXT NOT NULL,
        tags_json TEXT NOT NULL DEFAULT '[]',
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        FOREIGN KEY(project_id) REFERENCES scwb_projects(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_scwb_calculations_project_created
        ON scwb_saved_calculations(project_id, created_at DESC);

    CREATE INDEX IF NOT EXISTS idx_scwb_calculations_owner_created
        ON scwb_saved_calculations(owner_subject, created_at DESC);

    CREATE TABLE IF NOT EXISTS scwb_store_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    INSERT OR REPLACE INTO scwb_store_meta(key,value)
    VALUES ('schema_version','12.2.0');
    """)


def initialize_store() -> Dict[str, Any]:
    with _connection() as conn:
        project_count = conn.execute("SELECT COUNT(*) AS n FROM scwb_projects").fetchone()["n"]
        calc_count = conn.execute("SELECT COUNT(*) AS n FROM scwb_saved_calculations").fetchone()["n"]
    path = _db_path()
    return {
        "schema": STORE_SCHEMA,
        "engine": "sqlite",
        "path": str(path),
        "persistent": True,
        "projectCount": int(project_count),
        "calculationCount": int(calc_count),
        "schemaVersion": VERSION,
    }


def _owner(authorization: Optional[str]) -> tuple[str, Dict[str, Any]]:
    session = require_session(authorization)
    subject = session["subject"]["id"]
    return subject, session


def _json(text: str, fallback):
    try:
        return json.loads(text)
    except Exception:
        return fallback


def _project_dict(row: sqlite3.Row) -> Dict[str, Any]:
    body = {
        "schema": PROJECT_SCHEMA,
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "metadata": _json(row["metadata_json"], {}),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }
    body["projectHash"] = _hash(body)
    return body


def _calculation_dict(row: sqlite3.Row) -> Dict[str, Any]:
    calculation_object = _json(row["calculation_object_json"], {})
    body = {
        "schema": CALCULATION_SCHEMA,
        "id": row["id"],
        "projectId": row["project_id"],
        "title": row["title"],
        "calculationObject": calculation_object,
        "calculationObjectHash": row["calculation_object_hash"],
        "tags": _json(row["tags_json"], []),
        "metadata": _json(row["metadata_json"], {}),
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }
    body["savedCalculationHash"] = _hash({
        k: v for k, v in body.items() if k != "savedCalculationHash"
    })
    return body


def _assert_project_owner(conn: sqlite3.Connection, project_id: str, owner: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM scwb_projects WHERE id=? AND owner_subject=?",
        (project_id, owner),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return row


def create_project(req: ProjectCreateRequest, owner: str) -> Dict[str, Any]:
    now = int(time.time())
    project_id = str(uuid.uuid4())
    with _connection() as conn:
        conn.execute(
            """INSERT INTO scwb_projects
               (id,owner_subject,name,description,metadata_json,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (
                project_id, owner, req.name.strip(), req.description,
                json.dumps(req.metadata, sort_keys=True, separators=(",", ":")),
                now, now,
            ),
        )
        row = _assert_project_owner(conn, project_id, owner)
    return _project_dict(row)


def list_projects(owner: str) -> List[Dict[str, Any]]:
    with _connection() as conn:
        rows = conn.execute(
            "SELECT * FROM scwb_projects WHERE owner_subject=? ORDER BY updated_at DESC, id",
            (owner,),
        ).fetchall()
    return [_project_dict(row) for row in rows]


def get_project(project_id: str, owner: str) -> Dict[str, Any]:
    with _connection() as conn:
        row = _assert_project_owner(conn, project_id, owner)
    return _project_dict(row)


def update_project(project_id: str, req: ProjectUpdateRequest, owner: str) -> Dict[str, Any]:
    with _connection() as conn:
        current = _assert_project_owner(conn, project_id, owner)
        name = req.name.strip() if req.name is not None else current["name"]
        description = req.description if req.description is not None else current["description"]
        metadata_json = (
            json.dumps(req.metadata, sort_keys=True, separators=(",", ":"))
            if req.metadata is not None else current["metadata_json"]
        )
        now = int(time.time())
        conn.execute(
            """UPDATE scwb_projects
               SET name=?,description=?,metadata_json=?,updated_at=?
               WHERE id=? AND owner_subject=?""",
            (name, description, metadata_json, now, project_id, owner),
        )
        row = _assert_project_owner(conn, project_id, owner)
    return _project_dict(row)


def delete_project(project_id: str, owner: str) -> Dict[str, Any]:
    with _connection() as conn:
        _assert_project_owner(conn, project_id, owner)
        before = conn.execute(
            "SELECT COUNT(*) AS n FROM scwb_saved_calculations WHERE project_id=? AND owner_subject=?",
            (project_id, owner),
        ).fetchone()["n"]
        conn.execute(
            "DELETE FROM scwb_projects WHERE id=? AND owner_subject=?",
            (project_id, owner),
        )
    return {
        "ok": True,
        "deletedProjectId": project_id,
        "cascadeDeletedCalculations": int(before),
    }


def save_calculation(req: SavedCalculationCreateRequest, owner: str) -> Dict[str, Any]:
    now = int(time.time())
    calculation_id = str(uuid.uuid4())
    calculation_object_hash = (
        req.calculationObject.get("calculationObjectHash")
        or _hash(req.calculationObject)
    )
    with _connection() as conn:
        _assert_project_owner(conn, req.projectId, owner)
        conn.execute(
            """INSERT INTO scwb_saved_calculations
               (id,project_id,owner_subject,title,calculation_object_json,
                calculation_object_hash,tags_json,metadata_json,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                calculation_id, req.projectId, owner, req.title.strip(),
                json.dumps(req.calculationObject, sort_keys=True, separators=(",", ":")),
                str(calculation_object_hash),
                json.dumps(req.tags, sort_keys=True, separators=(",", ":")),
                json.dumps(req.metadata, sort_keys=True, separators=(",", ":")),
                now, now,
            ),
        )
        row = conn.execute(
            "SELECT * FROM scwb_saved_calculations WHERE id=? AND owner_subject=?",
            (calculation_id, owner),
        ).fetchone()
    return _calculation_dict(row)


def list_calculations(project_id: str, owner: str) -> List[Dict[str, Any]]:
    with _connection() as conn:
        _assert_project_owner(conn, project_id, owner)
        rows = conn.execute(
            """SELECT * FROM scwb_saved_calculations
               WHERE project_id=? AND owner_subject=?
               ORDER BY created_at DESC, id""",
            (project_id, owner),
        ).fetchall()
    return [_calculation_dict(row) for row in rows]


def get_calculation(calculation_id: str, owner: str) -> Dict[str, Any]:
    with _connection() as conn:
        row = conn.execute(
            "SELECT * FROM scwb_saved_calculations WHERE id=? AND owner_subject=?",
            (calculation_id, owner),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Saved calculation not found")
    return _calculation_dict(row)


def delete_calculation(calculation_id: str, owner: str) -> Dict[str, Any]:
    with _connection() as conn:
        row = conn.execute(
            "SELECT id FROM scwb_saved_calculations WHERE id=? AND owner_subject=?",
            (calculation_id, owner),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Saved calculation not found")
        conn.execute(
            "DELETE FROM scwb_saved_calculations WHERE id=? AND owner_subject=?",
            (calculation_id, owner),
        )
    return {"ok": True, "deletedCalculationId": calculation_id}


def status() -> Dict[str, Any]:
    store = initialize_store()
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Persistent Calculation & Project Store",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "storage": store,
        "capabilities": {
            "persistentProjects": True,
            "persistentCalculations": True,
            "sessionSubjectOwnership": True,
            "sqliteWalPersistence": True,
            "projectCrud": True,
            "calculationSaveLoadDelete": True,
            "projectCascadeDelete": True,
            "calculationObjectHashPreservation": True,
            "storageEngineAbstractionBoundary": True,
            "postgresMigrationPath": True,
            "wordpressStateNotRequired": True,
        },
    }


@router.get("/v1220/status")
def status_route():
    return status()


@router.get("/standalone/v1/store/status")
def store_status_route(authorization: Optional[str] = Header(default=None)):
    owner, session = _owner(authorization)
    store = initialize_store()
    return {
        "ok": True,
        "version": VERSION,
        "ownerSubject": owner,
        "sessionId": session["sessionId"],
        "store": store,
    }


@router.post("/standalone/v1/projects")
def create_project_route(req: ProjectCreateRequest, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    return {"ok": True, "version": VERSION, "project": create_project(req, owner)}


@router.get("/standalone/v1/projects")
def list_projects_route(authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    items = list_projects(owner)
    return {"ok": True, "version": VERSION, "projects": items, "count": len(items)}


@router.get("/standalone/v1/projects/{project_id}")
def get_project_route(project_id: str, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    return {"ok": True, "version": VERSION, "project": get_project(project_id, owner)}


@router.patch("/standalone/v1/projects/{project_id}")
def update_project_route(project_id: str, req: ProjectUpdateRequest, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    return {"ok": True, "version": VERSION, "project": update_project(project_id, req, owner)}


@router.delete("/standalone/v1/projects/{project_id}")
def delete_project_route(project_id: str, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    return delete_project(project_id, owner)


@router.post("/standalone/v1/calculations")
def save_calculation_route(req: SavedCalculationCreateRequest, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    return {"ok": True, "version": VERSION, "calculation": save_calculation(req, owner)}


@router.get("/standalone/v1/projects/{project_id}/calculations")
def list_calculations_route(project_id: str, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    items = list_calculations(project_id, owner)
    return {"ok": True, "version": VERSION, "calculations": items, "count": len(items)}


@router.get("/standalone/v1/calculations/{calculation_id}")
def get_calculation_route(calculation_id: str, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    return {"ok": True, "version": VERSION, "calculation": get_calculation(calculation_id, owner)}


@router.delete("/standalone/v1/calculations/{calculation_id}")
def delete_calculation_route(calculation_id: str, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    return delete_calculation(calculation_id, owner)

"""Workbench v3.1.0 — Persistent Project Workspace.

The FastAPI layer validates project/revision records and produces deterministic
sync decisions. WordPress remains the optional authenticated persistence store;
the browser remains the local-first baseline.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

VERSION = "3.1.0"
PROJECT_SCHEMA = "sc-workbench-persistent-project/1.0"
REVISION_SCHEMA = "sc-workbench-project-revision/1.0"
SYNC_SCHEMA = "sc-workbench-project-sync-plan/1.0"
PACKAGE_SCHEMA = "sc-workbench-project-workspace-package/1.0"

router = APIRouter(prefix="/v310", tags=["workbench-v310"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:80] or "project"


class ProjectRecord(BaseModel):
    schema_id: str = Field(default=PROJECT_SCHEMA, alias="schema")
    project_id: str
    title: str = "Untitled Workbench project"
    description: str = ""
    status: Literal["draft", "active", "review", "complete", "archived"] = "draft"
    owner_id: str = ""
    storage_mode: Literal["browser", "wordpress", "hybrid"] = "browser"
    tags: list[str] = Field(default_factory=list)
    pinned: bool = False
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)
    local_revision: int = 0
    server_revision: int = 0
    active_studio: str = "unified"
    studio_records: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    content_hash: str = ""

    model_config = {"populate_by_name": True}

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, value: str) -> str:
        value = _slug(value)
        if not value:
            raise ValueError("project_id is required")
        return value

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title is required")
        return value[:180]


class ProjectValidationRequest(BaseModel):
    project: ProjectRecord


class RevisionBuildRequest(BaseModel):
    project: ProjectRecord
    reason: str = "manual-save"
    author_id: str = ""
    parent_hash: str = ""
    changed_paths: list[str] = Field(default_factory=list)


class SyncPlanRequest(BaseModel):
    local: ProjectRecord | None = None
    remote: ProjectRecord | None = None
    strategy: Literal["newest", "local", "remote", "manual"] = "newest"


class WorkspacePackageRequest(BaseModel):
    project: ProjectRecord
    revisions: list[dict[str, Any]] = Field(default_factory=list)
    include_studio_records: bool = True


def normalize_project(project: ProjectRecord) -> dict[str, Any]:
    data = project.model_dump(by_alias=True)
    data["schema"] = PROJECT_SCHEMA
    data["project_id"] = _slug(data["project_id"])
    data["title"] = data["title"].strip()[:180]
    data["tags"] = sorted({str(tag).strip()[:60] for tag in data.get("tags", []) if str(tag).strip()})
    data["evidence_ids"] = sorted({str(item).strip() for item in data.get("evidence_ids", []) if str(item).strip()})
    data["artifact_ids"] = sorted({str(item).strip() for item in data.get("artifact_ids", []) if str(item).strip()})
    data["local_revision"] = max(0, int(data.get("local_revision", 0)))
    data["server_revision"] = max(0, int(data.get("server_revision", 0)))
    data["updated_at"] = data.get("updated_at") or _now()
    data["created_at"] = data.get("created_at") or data["updated_at"]
    unhashed = dict(data)
    unhashed.pop("content_hash", None)
    data["content_hash"] = _hash(unhashed)
    return data


def validate_project(project: ProjectRecord) -> dict[str, Any]:
    normalized = normalize_project(project)
    warnings: list[str] = []
    if not normalized["studio_records"]:
        warnings.append("No studio records are attached yet.")
    if normalized["storage_mode"] == "wordpress" and not normalized["owner_id"]:
        warnings.append("WordPress storage records should identify an owner.")
    if normalized["local_revision"] < normalized["server_revision"]:
        warnings.append("The local record is behind the server revision.")
    return {
        "ok": True,
        "schema": PROJECT_SCHEMA,
        "version": VERSION,
        "generatedAt": _now(),
        "project": normalized,
        "warnings": warnings,
        "studioCount": len(normalized["studio_records"]),
        "recordCount": sum(1 for _ in normalized["studio_records"].values()),
        "projectHash": normalized["content_hash"],
    }


def build_revision(request: RevisionBuildRequest) -> dict[str, Any]:
    project = normalize_project(request.project)
    revision_number = max(project["local_revision"], project["server_revision"]) + 1
    revision = {
        "schema": REVISION_SCHEMA,
        "version": VERSION,
        "projectId": project["project_id"],
        "revision": revision_number,
        "reason": request.reason.strip()[:100] or "manual-save",
        "authorId": request.author_id.strip(),
        "parentHash": request.parent_hash.strip(),
        "changedPaths": sorted({path.strip() for path in request.changed_paths if path.strip()}),
        "createdAt": _now(),
        "projectHash": project["content_hash"],
        "snapshot": project,
    }
    revision["revisionHash"] = _hash(revision)
    return {
        "ok": True,
        "schema": REVISION_SCHEMA,
        "version": VERSION,
        "revision": revision,
        "revisionHash": revision["revisionHash"],
    }


def plan_sync(request: SyncPlanRequest) -> dict[str, Any]:
    local = normalize_project(request.local) if request.local else None
    remote = normalize_project(request.remote) if request.remote else None
    warnings: list[str] = []

    if not local and not remote:
        return {
            "ok": False,
            "schema": SYNC_SCHEMA,
            "version": VERSION,
            "decision": "none",
            "conflict": False,
            "warnings": ["No local or remote project was supplied."],
        }
    if local and not remote:
        decision = "upload-local"
        winner = local
        conflict = False
    elif remote and not local:
        decision = "download-remote"
        winner = remote
        conflict = False
    elif local["content_hash"] == remote["content_hash"]:
        decision = "already-synchronized"
        winner = local
        conflict = False
    else:
        conflict = True
        if request.strategy == "local":
            decision, winner = "upload-local", local
        elif request.strategy == "remote":
            decision, winner = "download-remote", remote
        elif request.strategy == "manual":
            decision, winner = "manual-review", None
        else:
            local_rank = (local["local_revision"], local["server_revision"], local["updated_at"])
            remote_rank = (remote["server_revision"], remote["local_revision"], remote["updated_at"])
            if local_rank > remote_rank:
                decision, winner = "upload-local", local
            elif remote_rank > local_rank:
                decision, winner = "download-remote", remote
            else:
                decision, winner = "manual-review", None
        warnings.append("Local and remote project hashes differ.")

    return {
        "ok": decision != "manual-review",
        "schema": SYNC_SCHEMA,
        "version": VERSION,
        "generatedAt": _now(),
        "projectId": (local or remote)["project_id"],
        "decision": decision,
        "strategy": request.strategy,
        "conflict": conflict,
        "localHash": local["content_hash"] if local else "",
        "remoteHash": remote["content_hash"] if remote else "",
        "winner": winner,
        "warnings": warnings,
        "planHash": _hash({"local": local, "remote": remote, "decision": decision, "strategy": request.strategy}),
    }


def build_workspace_package(request: WorkspacePackageRequest) -> dict[str, Any]:
    project = normalize_project(request.project)
    packaged_project = dict(project)
    if not request.include_studio_records:
        packaged_project["studio_records"] = {}
    revisions = sorted(request.revisions, key=lambda item: (int(item.get("revision", 0)), str(item.get("createdAt", ""))))
    package = {
        "schema": PACKAGE_SCHEMA,
        "version": VERSION,
        "generatedAt": _now(),
        "project": packaged_project,
        "revisions": revisions,
        "revisionCount": len(revisions),
    }
    package["packageHash"] = _hash(package)
    return {
        "ok": True,
        "schema": PACKAGE_SCHEMA,
        "version": VERSION,
        "package": package,
        "packageHash": package["packageHash"],
    }


@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "schema": PROJECT_SCHEMA,
        "capabilities": [
            "project-validation",
            "revision-snapshots",
            "sync-conflict-planning",
            "workspace-packages",
            "browser-local-fallback",
            "optional-wordpress-storage",
        ],
    }


@router.post("/project/validate")
def project_validate(request: ProjectValidationRequest) -> dict[str, Any]:
    return validate_project(request.project)


@router.post("/revision/build")
def revision_build(request: RevisionBuildRequest) -> dict[str, Any]:
    return build_revision(request)


@router.post("/sync/plan")
def sync_plan(request: SyncPlanRequest) -> dict[str, Any]:
    return plan_sync(request)


@router.post("/package/build")
def package_build(request: WorkspacePackageRequest) -> dict[str, Any]:
    return build_workspace_package(request)

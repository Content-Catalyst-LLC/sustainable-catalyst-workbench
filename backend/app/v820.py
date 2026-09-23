"""Workbench v8.2.0 — Unified Research Project Workspace.

Project-centric consolidation above v8.0 environments and v8.1 persistence. A project
workspace resolves one active, integrity-validated persisted research environment and
summarizes its datasets, notebooks, workflows, executions, visuals, validation and
packages into a durable navigation/dashboard object. Project metadata is persisted
atomically with optimistic revision checks; environment revision history remains owned
by v8.1 and is never duplicated or rewritten here.

This layer prepares surface and Platform Core binding plans only. It performs no
scientific computation, notebook replay, workflow execution, or outbound Core dispatch.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v660 import CORE_PATHS, CORE_UNIFIED_RUNTIME_CONTRACT
from .v800 import (
    ENVIRONMENT_SCHEMA,
    SURFACE_ENDPOINTS,
    CoreEnvironmentPlanRequest,
    SurfacePlanRequest,
    core_environment_plan,
    surface_plan,
    validate_environment,
)
from .v810 import _atomic_json_write, _json_read, _store_root, load_environment

VERSION = APP_VERSION
SCHEMA = "sc-workbench-unified-research-project-workspace/1.0"
WORKSPACE_SCHEMA = "sc-workbench-research-project-workspace/1.0"
PROJECT_RECORD_SCHEMA = "sc-workbench-research-project-record/1.0"
SURFACE_PLAN_SCHEMA = "sc-workbench-research-project-surface-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-core-research-project-workspace-plan/1.0"
ACTIVITY_SCHEMA = "sc-workbench-research-project-activity/1.0"
MAX_TAGS = 64
MAX_OBJECTIVES = 64
MAX_PROJECTS_RETURNED = 500
MAX_ACTIVITY_RETURNED = 500

router = APIRouter(tags=["workbench-v820-unified-research-project-workspace"])

ProjectStatus = Literal["planning", "active", "paused", "complete", "archived"]
ProjectSurface = Literal[
    "overview", "data", "notebook", "workflow", "visual", "validation",
    "solver", "simulation", "engineering", "design-space", "packages",
]

COMPONENT_SURFACE = {
    "data-workspace": "data",
    "notebook-run": "notebook",
    "workflow-graph-run": "workflow",
    "visual-workspace": "visual",
    "validation-report": "validation",
    "solver-run": "solver",
    "simulation-run": "simulation",
    "engineering-run": "engineering",
    "design-space-run": "design-space",
    "reproducible-package": "packages",
    "execution-object": "overview",
    "predictive-run": "overview",
    "forensic-run": "overview",
    "artifact": "overview",
    "source": "overview",
    "other": "overview",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _project_id(project_key: str) -> str:
    return hashlib.sha256(project_key.encode("utf-8")).hexdigest()


def _project_dir(project_key: str) -> Path:
    return _store_root() / "projects" / _project_id(project_key)


def _project_path(project_key: str) -> Path:
    return _project_dir(project_key) / "project.json"


def _activity_path(project_key: str) -> Path:
    return _project_dir(project_key) / "activity.json"


@contextmanager
def _project_lock(project_key: str):
    path = _store_root() / "locks" / f"project-{_project_id(project_key)}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _workspace_hash(workspace: Dict[str, Any]) -> str:
    candidate = deepcopy(workspace)
    candidate.pop("workspaceHash", None)
    candidate.pop("workspaceRef", None)
    return content_hash(candidate)


def _record_hash(record: Dict[str, Any]) -> str:
    candidate = deepcopy(record)
    candidate.pop("recordHash", None)
    return content_hash(candidate)


def _validate_workspace(workspace: Dict[str, Any]) -> bool:
    if workspace.get("schema") != WORKSPACE_SCHEMA:
        return False
    if workspace.get("workspaceHash") != _workspace_hash(workspace):
        return False
    env = workspace.get("researchEnvironment")
    return isinstance(env, dict) and bool(validate_environment(env).get("valid")) and workspace.get("activeEnvironmentHash") == env.get("environmentHash")


def _load_project_record(project_key: str) -> Dict[str, Any]:
    path = _project_path(project_key)
    if not path.exists():
        raise FileNotFoundError(f"research project {project_key} not found")
    record = _json_read(path)
    if record.get("projectKey") != project_key or record.get("recordHash") != _record_hash(record):
        raise ValueError("stored research project record failed integrity validation")
    if not _validate_workspace(record.get("workspace") or {}):
        raise ValueError("stored research project workspace failed integrity validation")
    return record


def _read_activity(project_key: str) -> List[Dict[str, Any]]:
    path = _activity_path(project_key)
    if not path.exists():
        return []
    raw = _json_read(path)
    items = raw.get("items") or []
    if not isinstance(items, list):
        raise ValueError("invalid project activity store")
    return items


def _write_activity(project_key: str, items: List[Dict[str, Any]]) -> None:
    _atomic_json_write(_activity_path(project_key), {
        "schema": ACTIVITY_SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "items": items[-5000:],
    })


class ProjectSpec(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=4000)
    researchQuestion: str = Field(default="", max_length=4000)
    objectives: List[str] = Field(default_factory=list, max_length=MAX_OBJECTIVES)
    tags: List[str] = Field(default_factory=list, max_length=MAX_TAGS)
    status: ProjectStatus = "active"
    activeEnvironmentKey: str = Field(min_length=1, max_length=160)
    activeEnvironmentRevision: Optional[int] = Field(default=None, ge=1)
    coreProjectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectBuildRequest(BaseModel):
    project: ProjectSpec
    researchEnvironment: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def environment_identity(self):
        if self.researchEnvironment is not None:
            key = _safe(self.researchEnvironment.get("environmentKey"), 160)
            if key != self.project.activeEnvironmentKey:
                raise ValueError("researchEnvironment.environmentKey must match activeEnvironmentKey")
        return self


class ProjectSaveRequest(BaseModel):
    workspace: Dict[str, Any]
    expectedProjectRevision: Optional[int] = Field(default=None, ge=0)
    actor: str = Field(default="workbench", min_length=1, max_length=160)
    reason: str = Field(default="save", min_length=1, max_length=500)


class ProjectSurfacePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    surface: ProjectSurface
    action: str = Field(default="", max_length=120)
    payload: Dict[str, Any] = Field(default_factory=dict)


class ProjectCorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", min_length=1, max_length=160)


def manifest() -> Dict[str, Any]:
    result = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "workspaceSchema": WORKSPACE_SCHEMA,
        "persistenceContract": "sc-workbench-research-environment-persistence-recovery/1.0",
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "surfaces": list(SURFACE_ENDPOINTS.keys()),
        "capabilities": {
            "projectCentricWorkspace": True,
            "persistedActiveEnvironment": True,
            "dashboardSummaries": True,
            "surfaceNavigationPlans": True,
            "projectActivity": True,
            "optimisticProjectRevisionChecks": True,
            "coreProjectSessionPlanning": True,
        },
        "boundaries": {
            "environmentHistoryAuthority": "v8.1 persistence/recovery",
            "duplicateEnvironmentSnapshotsStoredInProjectMetadata": False,
            "scientificExecutionPerformed": False,
            "automaticNotebookReplayAuthorized": False,
            "automaticWorkflowExecutionAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
        },
    }
    result["manifestHash"] = content_hash(result)
    return result


def _resolve_environment(req: ProjectBuildRequest) -> tuple[Dict[str, Any], int, str]:
    if req.researchEnvironment is not None:
        env = deepcopy(req.researchEnvironment)
        if not validate_environment(env).get("valid"):
            raise ValueError("researchEnvironment integrity validation failed")
        revision = req.project.activeEnvironmentRevision or 0
        revision_hash = ""
        return env, revision, revision_hash
    loaded = load_environment(req.project.activeEnvironmentKey, req.project.activeEnvironmentRevision)
    rec = loaded["revision"]
    return deepcopy(loaded["researchEnvironment"]), int(rec["revision"]), _safe(rec.get("revisionHash"), 256)


def _summarize_environment(env: Dict[str, Any]) -> Dict[str, Any]:
    counts = {surface: 0 for surface in SURFACE_ENDPOINTS}
    counts["overview"] = 0
    component_refs: Dict[str, List[str]] = {surface: [] for surface in counts}
    for comp in env.get("components", []):
        surface = COMPONENT_SURFACE.get(comp.get("componentType"), "overview")
        counts[surface] = counts.get(surface, 0) + 1
        ref = _safe(comp.get("componentRef"), 1000)
        if ref:
            component_refs.setdefault(surface, []).append(ref)
    execution_count = len(env.get("executionObjects") or [])
    counts["overview"] += execution_count
    available = [name for name in SURFACE_ENDPOINTS if counts.get(name, 0) > 0 or name in ("overview", "data", "notebook", "workflow", "visual", "validation", "packages")]
    return {
        "componentCount": len(env.get("components") or []),
        "executionObjectCount": execution_count,
        "countsBySurface": counts,
        "refsBySurface": {k: sorted(set(v)) for k, v in component_refs.items() if v},
        "availableSurfaces": available,
        "activeEnvironmentSurface": env.get("activeSurface", "overview"),
    }


def build_project_workspace(req: ProjectBuildRequest) -> Dict[str, Any]:
    env, env_revision, env_revision_hash = _resolve_environment(req)
    p = req.project
    if _safe(env.get("projectEntityId"), 255) and _safe(env.get("projectEntityId"), 255) != p.projectKey and _safe(env.get("projectEntityId"), 255) != _safe(p.metadata.get("projectEntityId"), 255):
        # Environment project ids can be external/core identifiers; preserve but surface the distinction.
        project_identity_match = False
    else:
        project_identity_match = True
    workspace: Dict[str, Any] = {
        "ok": True,
        "schema": WORKSPACE_SCHEMA,
        "version": VERSION,
        "projectKey": p.projectKey,
        "title": p.title,
        "description": p.description,
        "researchQuestion": p.researchQuestion,
        "objectives": sorted({_safe(x, 1000) for x in p.objectives if _safe(x, 1000)}),
        "tags": sorted({_safe(x, 160) for x in p.tags if _safe(x, 160)}),
        "status": p.status,
        "coreProjectRef": p.coreProjectRef or env.get("coreProjectRef", ""),
        "coreSessionId": p.coreSessionId or env.get("coreSessionId", ""),
        "activeEnvironmentKey": p.activeEnvironmentKey,
        "activeEnvironmentRevision": env_revision or None,
        "activeEnvironmentRevisionHash": env_revision_hash or None,
        "activeEnvironmentRef": env.get("environmentRef"),
        "activeEnvironmentHash": env.get("environmentHash"),
        "researchEnvironment": env,
        "dashboard": _summarize_environment(env),
        "navigation": {surface: deepcopy(SURFACE_ENDPOINTS[surface]) for surface in SURFACE_ENDPOINTS},
        "metadata": deepcopy(p.metadata),
        "projectIdentityMatchesEnvironment": project_identity_match,
        "scientificExecutionPerformed": False,
        "automaticNotebookReplayAuthorized": False,
        "automaticWorkflowExecutionAuthorized": False,
        "automaticCoreDispatchAuthorized": False,
        "workspaceHash": "",
        "workspaceRef": "",
    }
    wh = _workspace_hash(workspace)
    workspace["workspaceHash"] = wh
    workspace["workspaceRef"] = f"sc://workbench/research-project/{p.projectKey}/workspace/{wh}"
    return workspace


def save_project(req: ProjectSaveRequest) -> Dict[str, Any]:
    workspace = deepcopy(req.workspace)
    if not _validate_workspace(workspace):
        raise ValueError("workspace integrity validation failed")
    key = _safe(workspace.get("projectKey"), 160)
    with _project_lock(key):
        path = _project_path(key)
        current_revision = 0
        current_hash: Optional[str] = None
        if path.exists():
            current = _load_project_record(key)
            current_revision = int(current.get("projectRevision", 0))
            current_hash = current.get("recordHash")
        if req.expectedProjectRevision is not None and req.expectedProjectRevision != current_revision:
            raise RuntimeError(f"project revision conflict: expected {req.expectedProjectRevision}, current {current_revision}")
        revision = current_revision + 1
        record: Dict[str, Any] = {
            "ok": True,
            "schema": PROJECT_RECORD_SCHEMA,
            "version": VERSION,
            "projectKey": key,
            "projectRevision": revision,
            "parentProjectRevision": current_revision or None,
            "parentRecordHash": current_hash,
            "workspaceHash": workspace.get("workspaceHash"),
            "activeEnvironmentKey": workspace.get("activeEnvironmentKey"),
            "activeEnvironmentRevision": workspace.get("activeEnvironmentRevision"),
            "activeEnvironmentHash": workspace.get("activeEnvironmentHash"),
            "workspace": workspace,
            "savedAt": _now(),
            "actor": req.actor,
            "reason": req.reason,
            "recordHash": "",
        }
        record["recordHash"] = _record_hash(record)
        _atomic_json_write(path, record)
        items = _read_activity(key)
        items.append({
            "activityId": content_hash({"projectKey": key, "projectRevision": revision, "recordHash": record["recordHash"]}),
            "type": "project-workspace-saved",
            "at": record["savedAt"],
            "actor": req.actor,
            "reason": req.reason,
            "projectRevision": revision,
            "workspaceHash": workspace.get("workspaceHash"),
            "activeEnvironmentRevision": workspace.get("activeEnvironmentRevision"),
            "activeEnvironmentHash": workspace.get("activeEnvironmentHash"),
        })
        _write_activity(key, items)
        return record


def list_projects() -> Dict[str, Any]:
    root = _store_root() / "projects"
    items: List[Dict[str, Any]] = []
    if root.exists():
        for path in sorted(root.glob("*/project.json")):
            try:
                record = _json_read(path)
                key = _safe(record.get("projectKey"), 160)
                checked = _load_project_record(key)
                ws = checked["workspace"]
                items.append({
                    "projectKey": key,
                    "title": ws.get("title"),
                    "status": ws.get("status"),
                    "projectRevision": checked.get("projectRevision"),
                    "activeEnvironmentKey": ws.get("activeEnvironmentKey"),
                    "activeEnvironmentRevision": ws.get("activeEnvironmentRevision"),
                    "activeEnvironmentHash": ws.get("activeEnvironmentHash"),
                    "workspaceRef": ws.get("workspaceRef"),
                    "savedAt": checked.get("savedAt"),
                })
            except Exception:
                continue
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "projectCount": len(items), "projects": items[:MAX_PROJECTS_RETURNED]}


def load_project(project_key: str) -> Dict[str, Any]:
    return _load_project_record(project_key)


def project_activity(project_key: str) -> Dict[str, Any]:
    _load_project_record(project_key)
    items = _read_activity(project_key)
    return {"ok": True, "schema": ACTIVITY_SCHEMA, "version": VERSION, "projectKey": project_key, "activityCount": len(items), "activity": items[-MAX_ACTIVITY_RETURNED:]}


def project_surface_plan(req: ProjectSurfacePlanRequest) -> Dict[str, Any]:
    record = _load_project_record(req.projectKey)
    ws = record["workspace"]
    env = ws["researchEnvironment"]
    plan = surface_plan(SurfacePlanRequest(researchEnvironment=env, surface=req.surface, action=req.action, payload=req.payload))
    result = {
        "ok": True,
        "schema": SURFACE_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "projectRevision": record["projectRevision"],
        "workspaceRef": ws.get("workspaceRef"),
        "activeEnvironmentRevision": ws.get("activeEnvironmentRevision"),
        "surface": req.surface,
        "surfacePlan": plan,
        "scientificExecutionPerformed": False,
        "automaticDispatchAuthorized": False,
    }
    result["planHash"] = content_hash(result)
    return result


def core_project_plan(req: ProjectCorePlanRequest) -> Dict[str, Any]:
    record = _load_project_record(req.projectKey)
    ws = record["workspace"]
    sid = _safe(req.coreSessionId or ws.get("coreSessionId"), 255)
    env_plan = core_environment_plan(CoreEnvironmentPlanRequest(
        researchEnvironment=ws["researchEnvironment"],
        coreProjectEntityId=req.coreProjectEntityId or req.projectKey,
        coreSessionId=sid,
        visibility=req.visibility,
        createdBy=req.createdBy,
    ))
    result: Dict[str, Any] = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "phase": env_plan.get("phase"),
        "projectKey": req.projectKey,
        "projectRevision": record.get("projectRevision"),
        "workspaceRef": ws.get("workspaceRef"),
        "workspaceHash": ws.get("workspaceHash"),
        "activeEnvironmentRef": ws.get("activeEnvironmentRef"),
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "coreSessionId": sid or None,
        "coreSessionIdMustComeFromCore": True,
        "environmentPlan": env_plan,
        "coreRequests": list(env_plan.get("coreRequests") or []),
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "coreExecutesWorkbenchComputation": False,
    }
    if sid:
        project_binding = {
            "path": CORE_PATHS["objectBindings"],
            "method": "POST",
            "phase": "project-workspace-bind",
            "data": {
                "session_id": sid,
                "object_type": "workbench.research-project-workspace",
                "object_ref": ws.get("workspaceRef"),
                "version_ref": f"{ws.get('workspaceRef')}@{str(ws.get('workspaceHash',''))[:16]}",
                "content_hash": ws.get("workspaceHash"),
                "role": "research-project-workspace",
                "visibility": req.visibility,
                "metadata": {
                    "workbenchVersion": VERSION,
                    "projectKey": req.projectKey,
                    "projectRevision": record.get("projectRevision"),
                    "activeEnvironmentRef": ws.get("activeEnvironmentRef"),
                },
            },
            "dispatchPerformed": False,
        }
        result["coreRequests"].append(project_binding)
    result["planHash"] = content_hash(result)
    return result


@router.get("/research-projects/manifest")
def manifest_endpoint():
    return manifest()


@router.post("/research-projects/build")
def build_endpoint(req: ProjectBuildRequest):
    try:
        return build_project_workspace(req)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/research-projects/save")
def save_endpoint(req: ProjectSaveRequest):
    try:
        return save_project(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/research-projects")
def list_endpoint():
    return list_projects()


@router.get("/research-projects/{project_key}")
def load_endpoint(project_key: str):
    try:
        return load_project(project_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/research-projects/{project_key}/activity")
def activity_endpoint(project_key: str):
    try:
        return project_activity(project_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/research-projects/surface/plan")
def surface_endpoint(req: ProjectSurfacePlanRequest):
    try:
        return project_surface_plan(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/integration/core/research-project-workspace/plan")
def core_endpoint(req: ProjectCorePlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    try:
        return core_project_plan(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/v820/status")
def status():
    return {
        "ok": True,
        "version": VERSION,
        "release": "Unified Research Project Workspace",
        "schema": SCHEMA,
        "projectCentricWorkspace": True,
        "persistedActiveEnvironment": True,
        "dashboardSummaries": True,
        "surfaceNavigationPlanning": True,
        "projectActivityHistory": True,
        "optimisticProjectRevisionChecks": True,
        "environmentHistoryAuthority": "v8.1",
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "scientificExecutionPerformed": False,
        "automaticNotebookReplayAuthorized": False,
        "automaticWorkflowExecutionAuthorized": False,
        "automaticCoreDispatchAuthorized": False,
        "v8Milestone": "unified-research-project-workspace",
    }

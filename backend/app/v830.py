"""Workbench v8.3.0 — Research Asset & Artifact Registry.

Durable, project-scoped registry above the v8.2 project workspace and v8.1 research
environment persistence layer. The registry stores content-addressed metadata, references,
provenance and revision history for research assets without copying scientific payloads
or becoming a competing source of truth for project/environment state.

Project indexing derives registry entries from the active integrity-validated v8.1
environment resolved by v8.2. Explicit external assets require a content hash. Registry
updates are append-only revisions with optimistic concurrency. Search is metadata-only;
no scientific computation, notebook/workflow execution, remote retrieval, filesystem
artifact copying, or automatic Platform Core dispatch is authorized here.
"""
from __future__ import annotations

import fcntl
import hashlib
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v660 import CORE_PATHS, CORE_UNIFIED_RUNTIME_CONTRACT
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import ProjectCorePlanRequest, core_project_plan, load_project

VERSION = APP_VERSION
SCHEMA = "sc-workbench-research-asset-artifact-registry/1.0"
ASSET_SCHEMA = "sc-workbench-research-asset/1.0"
ASSET_RECORD_SCHEMA = "sc-workbench-research-asset-revision/1.0"
SEARCH_SCHEMA = "sc-workbench-research-asset-search/1.0"
PROJECT_INDEX_SCHEMA = "sc-workbench-research-project-asset-index/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-core-research-asset-registry-plan/1.0"
MAX_TAGS = 64
MAX_RESULTS = 1000
MAX_CORE_ASSETS = 100

router = APIRouter(tags=["workbench-v830-research-asset-artifact-registry"])

AssetType = Literal[
    "dataset", "parameter-set", "model", "notebook", "workflow", "execution",
    "solver-result", "simulation", "engineering-analysis", "design-space",
    "validation-report", "figure", "visualization", "report", "evidence",
    "source", "reproducible-package", "artifact", "external", "other",
]
AssetOrigin = Literal["project-environment", "explicit", "external"]

COMPONENT_ASSET_TYPES = {
    "data-workspace": "dataset",
    "notebook-run": "notebook",
    "workflow-graph-run": "workflow",
    "visual-workspace": "visualization",
    "validation-report": "validation-report",
    "reproducible-package": "reproducible-package",
    "execution-object": "execution",
    "solver-run": "solver-result",
    "simulation-run": "simulation",
    "engineering-run": "engineering-analysis",
    "design-space-run": "design-space",
    "predictive-run": "model",
    "forensic-run": "evidence",
    "artifact": "artifact",
    "source": "source",
    "other": "other",
}


def _safe(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _project_registry_dir(project_key: str) -> Path:
    return _store_root() / "asset-registry" / _id(project_key)


def _asset_dir(project_key: str, asset_key: str) -> Path:
    return _project_registry_dir(project_key) / "assets" / _id(asset_key)


def _asset_index_path(project_key: str, asset_key: str) -> Path:
    return _asset_dir(project_key, asset_key) / "index.json"


def _asset_revision_path(project_key: str, asset_key: str, revision: int) -> Path:
    return _asset_dir(project_key, asset_key) / "revisions" / f"{revision:08d}.json"


@contextmanager
def _asset_lock(project_key: str, asset_key: str):
    path = _store_root() / "locks" / f"asset-{_id(project_key)}-{_id(asset_key)}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _asset_hash(asset: Dict[str, Any]) -> str:
    candidate = deepcopy(asset)
    candidate.pop("assetHash", None)
    candidate.pop("assetRef", None)
    return content_hash(candidate)


def _record_hash(record: Dict[str, Any]) -> str:
    candidate = deepcopy(record)
    candidate.pop("recordHash", None)
    return content_hash(candidate)


def _validate_asset(asset: Dict[str, Any]) -> bool:
    return (
        asset.get("schema") == ASSET_SCHEMA
        and bool(asset.get("projectKey"))
        and bool(asset.get("assetKey"))
        and bool(asset.get("contentHash"))
        and asset.get("assetHash") == _asset_hash(asset)
    )


def _load_asset_record(project_key: str, asset_key: str, revision: Optional[int] = None) -> Dict[str, Any]:
    index_path = _asset_index_path(project_key, asset_key)
    if not index_path.exists():
        raise FileNotFoundError(f"research asset {project_key}/{asset_key} not found")
    idx = _json_read(index_path)
    if idx.get("projectKey") != project_key or idx.get("assetKey") != asset_key:
        raise ValueError("research asset index identity mismatch")
    rev = revision or int(idx.get("currentRevision") or 0)
    if rev < 1:
        raise ValueError("research asset has no persisted revision")
    path = _asset_revision_path(project_key, asset_key, rev)
    if not path.exists():
        raise FileNotFoundError(f"research asset revision {rev} not found")
    record = _json_read(path)
    if record.get("recordHash") != _record_hash(record):
        raise ValueError("stored research asset revision failed integrity validation")
    if not _validate_asset(record.get("asset") or {}):
        raise ValueError("stored research asset failed integrity validation")
    return record


class AssetSpec(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    assetKey: str = Field(min_length=1, max_length=200)
    assetType: AssetType
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=4000)
    assetRef: str = Field(default="", max_length=1200)
    contentHash: str = Field(min_length=8, max_length=256)
    mediaType: str = Field(default="", max_length=255)
    sizeBytes: Optional[int] = Field(default=None, ge=0)
    tags: List[str] = Field(default_factory=list, max_length=MAX_TAGS)
    origin: AssetOrigin = "explicit"
    environmentKey: str = Field(default="", max_length=160)
    environmentRevision: Optional[int] = Field(default=None, ge=1)
    environmentHash: str = Field(default="", max_length=256)
    sourceComponentKey: str = Field(default="", max_length=200)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def external_integrity(self):
        if self.origin == "external" and not self.assetRef:
            raise ValueError("external assets require assetRef")
        return self


class RegisterAssetRequest(BaseModel):
    asset: AssetSpec
    expectedAssetRevision: Optional[int] = Field(default=None, ge=0)
    actor: str = Field(default="workbench", min_length=1, max_length=160)
    reason: str = Field(default="register", min_length=1, max_length=500)


class ProjectIndexRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    expectedExistingRevision: Optional[int] = Field(default=None, ge=0)
    actor: str = Field(default="workbench", min_length=1, max_length=160)
    reason: str = Field(default="project-environment-index", min_length=1, max_length=500)
    includeExecutionObjects: bool = True


class CoreAssetPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    assetKeys: List[str] = Field(default_factory=list, max_length=MAX_CORE_ASSETS)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", min_length=1, max_length=160)


def manifest() -> Dict[str, Any]:
    result = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "assetSchema": ASSET_SCHEMA,
        "assetTypes": list(AssetType.__args__),
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "capabilities": {
            "projectScopedAssetRegistry": True,
            "contentAddressedAssetMetadata": True,
            "appendOnlyAssetRevisions": True,
            "optimisticAssetRevisionChecks": True,
            "projectEnvironmentIndexing": True,
            "assetSearch": True,
            "assetIntegrityValidation": True,
            "coreAssetBindingPlanning": True,
        },
        "boundaries": {
            "projectStateAuthority": "v8.2 project workspace",
            "environmentStateAuthority": "v8.1 persistence/recovery",
            "scientificPayloadsDuplicated": False,
            "automaticRemoteRetrievalAuthorized": False,
            "scientificExecutionPerformed": False,
            "automaticCoreDispatchAuthorized": False,
        },
    }
    result["manifestHash"] = content_hash(result)
    return result


def _normalize_asset(spec: AssetSpec) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "ok": True,
        "schema": ASSET_SCHEMA,
        "version": VERSION,
        "projectKey": spec.projectKey,
        "assetKey": spec.assetKey,
        "assetType": spec.assetType,
        "title": spec.title,
        "description": spec.description,
        "assetRef": spec.assetRef or f"sc://workbench/research-asset/{spec.projectKey}/{spec.assetKey}/{spec.contentHash}",
        "contentHash": spec.contentHash,
        "mediaType": spec.mediaType or None,
        "sizeBytes": spec.sizeBytes,
        "tags": sorted({_safe(x, 160) for x in spec.tags if _safe(x, 160)}),
        "origin": spec.origin,
        "environmentKey": spec.environmentKey or None,
        "environmentRevision": spec.environmentRevision,
        "environmentHash": spec.environmentHash or None,
        "sourceComponentKey": spec.sourceComponentKey or None,
        "provenance": deepcopy(spec.provenance),
        "metadata": deepcopy(spec.metadata),
        "assetHash": "",
    }
    base["assetHash"] = _asset_hash(base)
    return base


def register_asset(req: RegisterAssetRequest) -> Dict[str, Any]:
    asset = _normalize_asset(req.asset)
    project_key, asset_key = req.asset.projectKey, req.asset.assetKey
    # Project must exist; v8.2 remains project authority.
    load_project(project_key)
    with _asset_lock(project_key, asset_key):
        index_path = _asset_index_path(project_key, asset_key)
        current_revision = 0
        parent_hash: Optional[str] = None
        if index_path.exists():
            current = _load_asset_record(project_key, asset_key)
            current_revision = int(current.get("assetRevision") or 0)
            parent_hash = current.get("recordHash")
        if req.expectedAssetRevision is not None and req.expectedAssetRevision != current_revision:
            raise RuntimeError(f"asset revision conflict: expected {req.expectedAssetRevision}, current {current_revision}")
        revision = current_revision + 1
        record: Dict[str, Any] = {
            "ok": True,
            "schema": ASSET_RECORD_SCHEMA,
            "version": VERSION,
            "projectKey": project_key,
            "assetKey": asset_key,
            "assetRevision": revision,
            "parentAssetRevision": current_revision or None,
            "parentRecordHash": parent_hash,
            "assetHash": asset["assetHash"],
            "contentHash": asset["contentHash"],
            "asset": asset,
            "actor": req.actor,
            "reason": req.reason,
            "recordHash": "",
        }
        record["recordHash"] = _record_hash(record)
        _atomic_json_write(_asset_revision_path(project_key, asset_key, revision), record)
        _atomic_json_write(index_path, {
            "schema": PROJECT_INDEX_SCHEMA,
            "version": VERSION,
            "projectKey": project_key,
            "assetKey": asset_key,
            "assetType": asset["assetType"],
            "title": asset["title"],
            "contentHash": asset["contentHash"],
            "assetHash": asset["assetHash"],
            "currentRevision": revision,
            "currentRecordHash": record["recordHash"],
        })
        return record


def _component_asset_spec(project_key: str, workspace: Dict[str, Any], comp: Dict[str, Any]) -> AssetSpec:
    ctype = _safe(comp.get("componentType"), 120)
    key = _safe(comp.get("componentKey"), 200)
    ch = _safe(comp.get("contentHash"), 256)
    if not ch:
        raise ValueError(f"component {key} has no contentHash")
    metadata = deepcopy(comp.get("metadata") or {})
    title = _safe(metadata.get("title") or key or ctype, 500)
    return AssetSpec(
        projectKey=project_key,
        assetKey=f"environment:{key}",
        assetType=COMPONENT_ASSET_TYPES.get(ctype, "other"),
        title=title,
        description=_safe(metadata.get("description"), 4000),
        assetRef=_safe(comp.get("componentRef"), 1200),
        contentHash=ch,
        tags=[ctype, "environment-component"],
        origin="project-environment",
        environmentKey=_safe(workspace.get("activeEnvironmentKey"), 160),
        environmentRevision=workspace.get("activeEnvironmentRevision"),
        environmentHash=_safe(workspace.get("activeEnvironmentHash"), 256),
        sourceComponentKey=key,
        provenance={"indexedFrom": workspace.get("workspaceRef"), "componentRole": comp.get("role")},
        metadata={"componentType": ctype, "required": comp.get("required", True)},
    )


def index_project(req: ProjectIndexRequest) -> Dict[str, Any]:
    record = load_project(req.projectKey)
    ws = record["workspace"]
    env = ws["researchEnvironment"]
    indexed: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for comp in env.get("components") or []:
        try:
            spec = _component_asset_spec(req.projectKey, ws, comp)
            existing = 0
            path = _asset_index_path(req.projectKey, spec.assetKey)
            if path.exists():
                existing = int(_json_read(path).get("currentRevision") or 0)
            out = register_asset(RegisterAssetRequest(asset=spec, expectedAssetRevision=existing, actor=req.actor, reason=req.reason))
            indexed.append({"assetKey": spec.assetKey, "assetType": spec.assetType, "assetRevision": out["assetRevision"], "contentHash": spec.contentHash})
        except Exception as exc:
            skipped.append({"componentKey": comp.get("componentKey"), "reason": str(exc)})
    if req.includeExecutionObjects:
        for i, ex in enumerate(env.get("executionObjects") or []):
            try:
                ch = _safe(ex.get("objectHash"), 256)
                if not ch:
                    raise ValueError("execution object missing objectHash")
                asset_key = f"execution:{i}:{ch[:16]}"
                spec = AssetSpec(
                    projectKey=req.projectKey, assetKey=asset_key, assetType="execution",
                    title=f"Execution object {i + 1}", assetRef=_safe(ex.get("executionObjectRef"), 1200),
                    contentHash=ch, tags=["execution-object"], origin="project-environment",
                    environmentKey=_safe(ws.get("activeEnvironmentKey"), 160),
                    environmentRevision=ws.get("activeEnvironmentRevision"),
                    environmentHash=_safe(ws.get("activeEnvironmentHash"), 256),
                    provenance={"indexedFrom": ws.get("workspaceRef")},
                )
                existing = int(_json_read(_asset_index_path(req.projectKey, asset_key)).get("currentRevision") or 0) if _asset_index_path(req.projectKey, asset_key).exists() else 0
                out = register_asset(RegisterAssetRequest(asset=spec, expectedAssetRevision=existing, actor=req.actor, reason=req.reason))
                indexed.append({"assetKey": asset_key, "assetType": "execution", "assetRevision": out["assetRevision"], "contentHash": ch})
            except Exception as exc:
                skipped.append({"executionIndex": i, "reason": str(exc)})
    result = {
        "ok": True,
        "schema": PROJECT_INDEX_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "projectRevision": record.get("projectRevision"),
        "activeEnvironmentKey": ws.get("activeEnvironmentKey"),
        "activeEnvironmentRevision": ws.get("activeEnvironmentRevision"),
        "activeEnvironmentHash": ws.get("activeEnvironmentHash"),
        "indexedCount": len(indexed),
        "skippedCount": len(skipped),
        "indexed": indexed,
        "skipped": skipped,
        "scientificPayloadsDuplicated": False,
        "scientificExecutionPerformed": False,
    }
    result["indexHash"] = content_hash(result)
    return result


def _latest_records(project_key: str) -> List[Dict[str, Any]]:
    root = _project_registry_dir(project_key) / "assets"
    items: List[Dict[str, Any]] = []
    if not root.exists():
        return items
    for idx_path in sorted(root.glob("*/index.json")):
        try:
            idx = _json_read(idx_path)
            items.append(_load_asset_record(project_key, _safe(idx.get("assetKey"), 200)))
        except Exception:
            continue
    return items


def search_assets(project_key: str, q: str = "", asset_type: str = "", tag: str = "", content_hash_value: str = "", limit: int = 200) -> Dict[str, Any]:
    load_project(project_key)
    qn = _safe(q, 500).lower()
    tn = _safe(tag, 160).lower()
    at = _safe(asset_type, 120)
    hv = _safe(content_hash_value, 256)
    matches: List[Dict[str, Any]] = []
    for record in _latest_records(project_key):
        asset = record["asset"]
        if at and asset.get("assetType") != at:
            continue
        if hv and asset.get("contentHash") != hv:
            continue
        tags = [str(x).lower() for x in asset.get("tags") or []]
        if tn and tn not in tags:
            continue
        hay = " ".join([
            _safe(asset.get("assetKey")), _safe(asset.get("title")), _safe(asset.get("description")),
            _safe(asset.get("assetRef")), _safe(asset.get("contentHash")), " ".join(tags),
            _safe(asset.get("sourceComponentKey")),
        ]).lower()
        if qn and qn not in hay:
            continue
        matches.append({
            "projectKey": project_key,
            "assetKey": asset.get("assetKey"),
            "assetType": asset.get("assetType"),
            "title": asset.get("title"),
            "assetRef": asset.get("assetRef"),
            "contentHash": asset.get("contentHash"),
            "assetHash": asset.get("assetHash"),
            "assetRevision": record.get("assetRevision"),
            "origin": asset.get("origin"),
            "tags": asset.get("tags") or [],
            "environmentRevision": asset.get("environmentRevision"),
        })
    matches.sort(key=lambda x: (str(x.get("assetType")), str(x.get("title")), str(x.get("assetKey"))))
    lim = max(1, min(int(limit), MAX_RESULTS))
    return {"ok": True, "schema": SEARCH_SCHEMA, "version": VERSION, "projectKey": project_key, "resultCount": len(matches), "results": matches[:lim]}


def asset_revisions(project_key: str, asset_key: str) -> Dict[str, Any]:
    current = _load_asset_record(project_key, asset_key)
    root = _asset_dir(project_key, asset_key) / "revisions"
    rows = []
    for path in sorted(root.glob("*.json")):
        rec = _json_read(path)
        if rec.get("recordHash") != _record_hash(rec):
            raise ValueError("stored research asset revision failed integrity validation")
        rows.append({"assetRevision": rec.get("assetRevision"), "recordHash": rec.get("recordHash"), "assetHash": rec.get("assetHash"), "contentHash": rec.get("contentHash"), "reason": rec.get("reason"), "actor": rec.get("actor")})
    return {"ok": True, "schema": ASSET_RECORD_SCHEMA, "version": VERSION, "projectKey": project_key, "assetKey": asset_key, "currentRevision": current.get("assetRevision"), "revisionCount": len(rows), "revisions": rows}


def core_asset_plan(req: CoreAssetPlanRequest) -> Dict[str, Any]:
    project = load_project(req.projectKey)
    ws = project["workspace"]
    sid = _safe(req.coreSessionId or ws.get("coreSessionId"), 255)
    project_plan = core_project_plan(ProjectCorePlanRequest(
        projectKey=req.projectKey,
        coreProjectEntityId=req.coreProjectEntityId or req.projectKey,
        coreSessionId=sid,
        visibility=req.visibility,
        createdBy=req.createdBy,
    ))
    selected = req.assetKeys or [x["asset"]["assetKey"] for x in _latest_records(req.projectKey)[:MAX_CORE_ASSETS]]
    assets = []
    for key in selected[:MAX_CORE_ASSETS]:
        assets.append(_load_asset_record(req.projectKey, key))
    result: Dict[str, Any] = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "phase": project_plan.get("phase"),
        "projectKey": req.projectKey,
        "projectRevision": project.get("projectRevision"),
        "coreSessionId": sid or None,
        "coreSessionIdMustComeFromCore": True,
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "projectPlan": project_plan,
        "assetCount": len(assets),
        "coreRequests": list(project_plan.get("coreRequests") or []),
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "scientificExecutionPerformed": False,
    }
    if sid:
        for rec in assets:
            asset = rec["asset"]
            result["coreRequests"].append({
                "path": CORE_PATHS["objectBindings"],
                "method": "POST",
                "phase": "research-asset-bind",
                "data": {
                    "session_id": sid,
                    "object_type": f"workbench.research-asset.{asset['assetType']}",
                    "object_ref": asset.get("assetRef"),
                    "version_ref": f"{asset.get('assetRef')}@{str(asset.get('assetHash',''))[:16]}",
                    "content_hash": asset.get("contentHash"),
                    "role": "research-asset",
                    "visibility": req.visibility,
                    "metadata": {"workbenchVersion": VERSION, "projectKey": req.projectKey, "assetKey": asset.get("assetKey"), "assetRevision": rec.get("assetRevision"), "assetHash": asset.get("assetHash")},
                },
                "dispatchPerformed": False,
            })
    result["planHash"] = content_hash(result)
    return result


@router.get("/research-assets/manifest")
def manifest_endpoint():
    return manifest()


@router.post("/research-assets/register")
def register_endpoint(req: RegisterAssetRequest):
    try:
        return register_asset(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/research-assets/index/project")
def index_project_endpoint(req: ProjectIndexRequest):
    try:
        return index_project(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/research-assets/search")
def search_endpoint(
    project_key: str = Query(min_length=1, max_length=160),
    q: str = Query(default="", max_length=500),
    asset_type: str = Query(default="", max_length=120),
    tag: str = Query(default="", max_length=160),
    content_hash: str = Query(default="", max_length=256),
    limit: int = Query(default=200, ge=1, le=MAX_RESULTS),
):
    try:
        return search_assets(project_key, q, asset_type, tag, content_hash, limit)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/research-assets/{project_key}/{asset_key}/revisions")
def revisions_endpoint(project_key: str, asset_key: str):
    try:
        return asset_revisions(project_key, asset_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/research-assets/{project_key}/{asset_key}")
def load_endpoint(project_key: str, asset_key: str, revision: Optional[int] = Query(default=None, ge=1)):
    try:
        return _load_asset_record(project_key, asset_key, revision)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/integration/core/research-assets/plan")
def core_endpoint(req: CoreAssetPlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    try:
        return core_asset_plan(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/v830/status")
def status():
    return {
        "ok": True,
        "version": VERSION,
        "release": "Research Asset & Artifact Registry",
        "schema": SCHEMA,
        "projectScopedAssetRegistry": True,
        "projectEnvironmentIndexing": True,
        "contentAddressedAssetMetadata": True,
        "appendOnlyAssetRevisions": True,
        "assetSearch": True,
        "assetIntegrityValidation": True,
        "projectStateAuthority": "v8.2",
        "environmentStateAuthority": "v8.1",
        "scientificPayloadsDuplicated": False,
        "scientificExecutionPerformed": False,
        "automaticRemoteRetrievalAuthorized": False,
        "automaticCoreDispatchAuthorized": False,
        "v8Milestone": "research-asset-artifact-registry",
    }

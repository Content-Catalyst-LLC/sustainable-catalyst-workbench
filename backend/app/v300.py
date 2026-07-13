"""Workbench v3.0.0 unified prototyping workbench routes."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "3.0.0"
router = APIRouter(prefix="/v300", tags=["workbench-v300"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class StudioRecord(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    label: str = Field(default="", max_length=300)
    version: str = Field(default="", max_length=120)
    status: Literal["not-started", "active", "complete", "blocked", "archived"] = "not-started"
    record_count: int = Field(default=0, ge=0, le=10_000_000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=5000)
    warnings: list[str] = Field(default_factory=list, max_length=5000)


class ArtifactRecord(BaseModel):
    path: str = Field(min_length=1, max_length=1000)
    kind: str = Field(default="other", max_length=100)
    content_hash: str = Field(default="", max_length=128)
    size_bytes: int = Field(default=0, ge=0, le=10_000_000_000)
    studio_id: str = Field(default="", max_length=100)


class ProjectManifest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    title: str = Field(default="Unified Workbench project", max_length=300)
    revision: str = Field(default="0.1.0", max_length=120)
    owner: str = Field(default="", max_length=300)
    studios: list[StudioRecord] = Field(default_factory=list, max_length=1000)
    artifacts: list[ArtifactRecord] = Field(default_factory=list, max_length=20000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=20000)
    assumptions: list[str] = Field(default_factory=list, max_length=5000)
    limitations: list[str] = Field(default_factory=list, max_length=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DependencyEdge(BaseModel):
    source: str = Field(min_length=1, max_length=100)
    target: str = Field(min_length=1, max_length=100)
    kind: Literal["data", "evidence", "execution", "review", "handoff"] = "data"


class ProjectAuditRequest(BaseModel):
    manifest: ProjectManifest
    dependencies: list[DependencyEdge] = Field(default_factory=list, max_length=10000)


class HandoffRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    revision: str = Field(default="0.1.0", max_length=120)
    source: str = Field(default="workbench", max_length=100)
    target: Literal["site-intelligence", "decision-studio", "research-librarian", "workbench"]
    record_ids: list[str] = Field(default_factory=list, max_length=10000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=10000)
    summary: str = Field(default="", max_length=20000)
    assumptions: list[str] = Field(default_factory=list, max_length=5000)
    limitations: list[str] = Field(default_factory=list, max_length=5000)
    requested_action: str = Field(default="review", max_length=500)


class WorkspaceRecord(BaseModel):
    key: str = Field(min_length=1, max_length=500)
    category: Literal["project", "calculation", "dataset", "code", "device", "experiment", "visualization", "documentation", "settings", "other"] = "other"
    size_bytes: int = Field(default=0, ge=0, le=10_000_000_000)
    revision: str = Field(default="", max_length=120)
    content_hash: str = Field(default="", max_length=128)
    protected: bool = False
    updated_at: str = Field(default="", max_length=80)


class WorkspaceHealthRequest(BaseModel):
    records: list[WorkspaceRecord] = Field(default_factory=list, max_length=50000)
    expected_categories: list[str] = Field(default_factory=list, max_length=100)


class PackageRequest(BaseModel):
    manifest: ProjectManifest
    files: list[ArtifactRecord] = Field(default_factory=list, max_length=50000)
    include_categories: list[str] = Field(default_factory=list, max_length=100)
    previous_package_hash: str = Field(default="", max_length=128)


class ResetPlanRequest(BaseModel):
    records: list[WorkspaceRecord] = Field(default_factory=list, max_length=50000)
    scope: Literal["selected", "category", "all"] = "selected"
    selected_keys: list[str] = Field(default_factory=list, max_length=50000)
    categories: list[str] = Field(default_factory=list, max_length=100)
    backup_confirmed: bool = False
    confirmation_text: str = Field(default="", max_length=200)


class MigrationRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    source_version: str = Field(default="2.9.0", max_length=120)
    storage_keys: list[str] = Field(default_factory=list, max_length=50000)
    records: list[WorkspaceRecord] = Field(default_factory=list, max_length=50000)


def _find_cycles(nodes: set[str], edges: list[DependencyEdge]) -> list[list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    indegree = {node: 0 for node in nodes}
    for edge in edges:
        if edge.source in nodes and edge.target in nodes:
            graph[edge.source].append(edge.target)
            indegree[edge.target] += 1
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    visited = []
    while queue:
        node = queue.popleft()
        visited.append(node)
        for target in graph[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(visited) == len(nodes):
        return []
    cyclic = sorted(node for node, degree in indegree.items() if degree > 0)
    return [cyclic]


@router.post("/project/audit")
def audit_project(request: ProjectAuditRequest) -> dict[str, Any]:
    studio_ids = [studio.id for studio in request.manifest.studios]
    artifact_paths = [artifact.path for artifact in request.manifest.artifacts]
    duplicate_studios = sorted(key for key, count in Counter(studio_ids).items() if count > 1)
    duplicate_artifacts = sorted(key for key, count in Counter(artifact_paths).items() if count > 1)
    known = set(studio_ids)
    unknown_dependencies = [edge.model_dump() for edge in request.dependencies if edge.source not in known or edge.target not in known]
    cycles = _find_cycles(known, request.dependencies)
    active = [studio for studio in request.manifest.studios if studio.status in {"active", "complete"}]
    complete = [studio for studio in request.manifest.studios if studio.status == "complete"]
    blocked = [studio.id for studio in request.manifest.studios if studio.status == "blocked"]
    missing_hashes = [artifact.path for artifact in request.manifest.artifacts if not artifact.content_hash]
    warning_count = sum(len(studio.warnings) for studio in request.manifest.studios)
    completeness = (len(complete) / len(request.manifest.studios) * 100) if request.manifest.studios else 0.0
    integrity = 100.0 if not request.manifest.artifacts else (1 - len(missing_hashes) / len(request.manifest.artifacts)) * 100
    health = max(0.0, min(100.0, 0.5 * completeness + 0.35 * integrity + 15 - len(blocked) * 10 - warning_count))
    return {
        "ok": not duplicate_studios and not duplicate_artifacts and not unknown_dependencies and not cycles and not blocked,
        "schema": "sc-workbench-unified-project-audit/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "projectId": request.manifest.project_id,
        "revision": request.manifest.revision,
        "studioCount": len(request.manifest.studios),
        "activeStudioCount": len(active),
        "completeStudioCount": len(complete),
        "artifactCount": len(request.manifest.artifacts),
        "evidenceCount": len(set(request.manifest.evidence_ids)),
        "completenessPercent": round(completeness, 4),
        "integrityPercent": round(integrity, 4),
        "healthScore": round(health, 4),
        "duplicateStudioIds": duplicate_studios,
        "duplicateArtifactPaths": duplicate_artifacts,
        "unknownDependencies": unknown_dependencies,
        "dependencyCycles": cycles,
        "blockedStudios": blocked,
        "artifactsMissingHash": missing_hashes,
        "warningCount": warning_count,
        "projectHash": _sha256(request.manifest.model_dump()),
    }


@router.post("/handoff/build")
def build_handoff(request: HandoffRequest) -> dict[str, Any]:
    packet = {
        "projectId": request.project_id,
        "revision": request.revision,
        "source": request.source,
        "target": request.target,
        "generatedAt": _now(),
        "recordIds": sorted(set(request.record_ids)),
        "evidenceIds": sorted(set(request.evidence_ids)),
        "summary": request.summary,
        "assumptions": request.assumptions,
        "limitations": request.limitations,
        "requestedAction": request.requested_action,
        "responsibleUse": "Target applications must revalidate imported records, freshness, scope, and professional-review boundaries.",
    }
    return {
        "ok": bool(request.summary.strip()) and bool(request.record_ids or request.evidence_ids),
        "schema": "sc-workbench-platform-handoff/1.0",
        "version": VERSION,
        "packet": packet,
        "packetHash": _sha256(packet),
        "warnings": ([] if request.summary.strip() else ["A handoff summary is required"]) + ([] if request.record_ids or request.evidence_ids else ["At least one record or evidence identifier is required"]),
    }


@router.post("/workspace/health")
def evaluate_workspace_health(request: WorkspaceHealthRequest) -> dict[str, Any]:
    keys = [record.key for record in request.records]
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    missing_hashes = [record.key for record in request.records if not record.content_hash]
    categories = Counter(record.category for record in request.records)
    missing_categories = sorted(set(request.expected_categories) - set(categories))
    protected = [record.key for record in request.records if record.protected]
    total_bytes = sum(record.size_bytes for record in request.records)
    hashed_ratio = 1.0 if not request.records else (len(request.records) - len(missing_hashes)) / len(request.records)
    score = max(0.0, 100 * hashed_ratio - 10 * len(duplicates) - 5 * len(missing_categories))
    return {
        "ok": not duplicates,
        "schema": "sc-workbench-workspace-health/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "recordCount": len(request.records),
        "totalBytes": total_bytes,
        "categoryCounts": dict(categories),
        "duplicateKeys": duplicates,
        "recordsMissingHash": missing_hashes,
        "missingExpectedCategories": missing_categories,
        "protectedKeys": protected,
        "healthScore": round(score, 4),
        "workspaceHash": _sha256([record.model_dump() for record in sorted(request.records, key=lambda value: value.key)]),
    }


@router.post("/package/build")
def build_package(request: PackageRequest) -> dict[str, Any]:
    paths = [record.path for record in request.files]
    duplicates = sorted(key for key, count in Counter(paths).items() if count > 1)
    missing_hashes = [record.path for record in request.files if not record.content_hash]
    categories = set(request.include_categories)
    included = [record for record in request.files if not categories or record.kind in categories]
    package_manifest = {
        "project": request.manifest.model_dump(),
        "generatedAt": _now(),
        "previousPackageHash": request.previous_package_hash,
        "files": [record.model_dump() for record in sorted(included, key=lambda value: value.path)],
        "format": "sc-workbench-project-package/1.0",
    }
    return {
        "ok": not duplicates and not missing_hashes,
        "schema": "sc-workbench-project-package/1.0",
        "version": VERSION,
        "manifest": package_manifest,
        "fileCount": len(included),
        "totalBytes": sum(record.size_bytes for record in included),
        "duplicatePaths": duplicates,
        "filesMissingHash": missing_hashes,
        "packageHash": _sha256(package_manifest),
        "chainLinked": bool(request.previous_package_hash),
    }


@router.post("/reset/plan")
def plan_reset(request: ResetPlanRequest) -> dict[str, Any]:
    selected = []
    if request.scope == "all":
        selected = list(request.records)
    elif request.scope == "category":
        wanted = set(request.categories)
        selected = [record for record in request.records if record.category in wanted]
    else:
        wanted = set(request.selected_keys)
        selected = [record for record in request.records if record.key in wanted]
    protected = [record.key for record in selected if record.protected]
    confirmation_ok = request.confirmation_text.strip().upper() == "RESET WORKBENCH"
    backup_required = request.scope == "all" or bool(protected)
    executable = bool(selected) and confirmation_ok and (request.backup_confirmed or not backup_required)
    return {
        "ok": executable,
        "schema": "sc-workbench-reset-plan/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "scope": request.scope,
        "selectedKeys": [record.key for record in selected],
        "selectedCount": len(selected),
        "selectedBytes": sum(record.size_bytes for record in selected),
        "protectedKeys": protected,
        "backupRequired": backup_required,
        "backupConfirmed": request.backup_confirmed,
        "confirmationValid": confirmation_ok,
        "executionAllowed": executable,
        "warnings": ([] if selected else ["No records matched the reset scope"]) + ([] if confirmation_ok else ["Type RESET WORKBENCH to authorize the plan"]) + ([] if request.backup_confirmed or not backup_required else ["Create or confirm a backup before resetting protected or all workspace data"]),
        "planHash": _sha256({"scope": request.scope, "keys": sorted(record.key for record in selected), "backup": request.backup_confirmed}),
    }


@router.post("/migration/plan")
def plan_migration(request: MigrationRequest) -> dict[str, Any]:
    legacy_prefixes = {
        "scwb-v200": "research",
        "scwb-v210": "embedded",
        "scwb-v220": "electronics",
        "scwb-v230": "robotics",
        "scwb-v240": "instrumentation",
        "scwb-v250": "simulation",
        "scwb-v260": "runtime",
        "scwb-v270": "visualization",
        "scwb-v280": "experiments",
        "scwb-v290": "documentation",
    }
    mapped = []
    unknown = []
    for key in request.storage_keys:
        studio = next((value for prefix, value in legacy_prefixes.items() if key.startswith(prefix)), None)
        if studio:
            mapped.append({"legacyKey": key, "studioId": studio, "targetKey": f"scwb-v300:{request.project_id}:{studio}:{key}"})
        else:
            unknown.append(key)
    return {
        "ok": True,
        "schema": "sc-workbench-v3-migration-plan/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "projectId": request.project_id,
        "sourceVersion": request.source_version,
        "targetVersion": VERSION,
        "mappedKeys": mapped,
        "unknownKeys": unknown,
        "recordCount": len(request.records),
        "backupRequired": True,
        "destructiveActions": False,
        "migrationHash": _sha256({"projectId": request.project_id, "sourceVersion": request.source_version, "mapped": mapped, "records": [record.model_dump() for record in request.records]}),
    }

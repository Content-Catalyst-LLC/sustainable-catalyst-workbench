"""Workbench v9.0.0 — Unified Scientific Study Composer.

Top-level research-study orchestration over authoritative Workbench projects,
assets, execution jobs, reproducible analysis snapshots, and publication/evidence
handoff packages. The composer reports explicit stage readiness and persists
content-addressed study records without inferring scientific validity or replacing
Platform Core governance.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import load_project
from .v830 import _load_asset_record, search_assets
from .v840 import _load_job, list_jobs
from .v8100 import list_snapshots, load_snapshot
from .v8110 import list_packages, load_package

VERSION = APP_VERSION
SCHEMA = "sc-workbench-unified-scientific-study-composer/1.0"
STUDY_SCHEMA = "sc-workbench-unified-scientific-study/1.0"
CATALOG_SCHEMA = "sc-workbench-unified-scientific-study-source-catalog/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-unified-scientific-study-core-plan/1.0"
router = APIRouter(tags=["workbench-v900-unified-scientific-study-composer"])

StudyStatus = Literal["draft", "active", "analysis", "publication", "complete", "archived"]
Visibility = Literal["private", "internal", "public"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _study_dir(project_key: str) -> Path:
    return _store_root() / "scientific-studies" / _stable_id(project_key)


def _study_path(project_key: str, study_hash: str) -> Path:
    return _study_dir(project_key) / f"{study_hash}.json"


class StudyProtocol(BaseModel):
    designType: str = Field(default="", max_length=160)
    hypothesis: str = Field(default="", max_length=4000)
    methods: List[str] = Field(default_factory=list, max_length=100)
    preregistrationRef: str = Field(default="", max_length=1200)
    inclusionCriteria: List[str] = Field(default_factory=list, max_length=100)
    exclusionCriteria: List[str] = Field(default_factory=list, max_length=100)
    notes: str = Field(default="", max_length=8000)

    @model_validator(mode="after")
    def normalize(self):
        for name in ("methods", "inclusionCriteria", "exclusionCriteria"):
            values = [str(x).strip() for x in getattr(self, name) if str(x).strip()]
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must be unique")
            setattr(self, name, values)
        return self


class ResearchFinding(BaseModel):
    findingId: str = Field(min_length=1, max_length=120)
    statement: str = Field(min_length=1, max_length=8000)
    evidenceRefs: List[str] = Field(default_factory=list, max_length=100)
    state: Literal["working", "final"] = "working"

    @model_validator(mode="after")
    def normalize(self):
        self.findingId = self.findingId.strip()
        self.evidenceRefs = [str(x).strip() for x in self.evidenceRefs if str(x).strip()]
        if len(self.evidenceRefs) != len(set(self.evidenceRefs)):
            raise ValueError("evidenceRefs must be unique")
        return self


class StudyComposerRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    studyKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=8000)
    researchQuestion: str = Field(default="", max_length=8000)
    objectives: List[str] = Field(default_factory=list, max_length=100)
    protocol: StudyProtocol = Field(default_factory=StudyProtocol)
    assetKeys: List[str] = Field(default_factory=list, max_length=200)
    parameterSetRefs: List[str] = Field(default_factory=list, max_length=200)
    executionJobIds: List[str] = Field(default_factory=list, max_length=200)
    analysisSnapshotHash: str = Field(default="", max_length=128)
    publicationPackageHash: str = Field(default="", max_length=128)
    findings: List[ResearchFinding] = Field(default_factory=list, max_length=200)
    status: StudyStatus = "draft"
    tags: List[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def normalize(self):
        self.projectKey = self.projectKey.strip()
        self.studyKey = self.studyKey.strip()
        self.analysisSnapshotHash = self.analysisSnapshotHash.strip()
        self.publicationPackageHash = self.publicationPackageHash.strip()
        for name in ("objectives", "assetKeys", "parameterSetRefs", "executionJobIds", "tags"):
            values = [str(x).strip() for x in getattr(self, name) if str(x).strip()]
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must be unique")
            setattr(self, name, values)
        ids = [x.findingId for x in self.findings]
        if len(ids) != len(set(ids)):
            raise ValueError("findingId values must be unique")
        return self


class SaveStudyRequest(StudyComposerRequest):
    createdBy: str = Field(default="workbench", min_length=1, max_length=160)
    recordLabel: str = Field(default="Unified scientific study", max_length=500)


class CoreStudyPlanRequest(StudyComposerRequest):
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Visibility = "internal"
    createdBy: str = Field(default="workbench", min_length=1, max_length=160)


def manifest() -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Unified Scientific Study Composer",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "studyStages": ["question", "protocol", "inputs", "execution", "analysis", "publication"],
        "capabilities": {
            "topLevelScientificStudyObject": True,
            "explicitStageReadiness": True,
            "projectAssetExecutionBinding": True,
            "analysisSnapshotBinding": True,
            "publicationPackageBinding": True,
            "researcherAuthoredFindings": True,
            "contentAddressedStudyRecords": True,
            "platformCoreStudyPlanning": True,
        },
        "boundaries": {
            "stageReadinessIsScientificValidity": False,
            "automaticHypothesisAcceptance": False,
            "automaticFindingGeneration": False,
            "automaticPreferredModelSelection": False,
            "automaticCausalInference": False,
            "automaticStatisticalSignificanceInference": False,
            "automaticPublication": False,
            "automaticCoreDispatch": False,
            "platformCoreGovernanceReplaced": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _asset_binding(project_key: str, asset_key: str) -> Dict[str, Any]:
    rec = _load_asset_record(project_key, asset_key)
    asset = rec.get("asset") or {}
    return {
        "assetKey": asset_key,
        "assetType": asset.get("assetType"),
        "title": asset.get("title"),
        "contentHash": asset.get("contentHash"),
        "assetHash": asset.get("assetHash"),
        "recordHash": rec.get("recordHash"),
        "revision": rec.get("assetRevision") or rec.get("revision"),
    }


def _job_binding(project_key: str, job_id: str) -> Dict[str, Any]:
    job = _load_job(job_id)
    if job.get("projectKey") != project_key:
        raise ValueError(f"job {job_id} belongs to another project")
    return {
        "jobId": job_id,
        "runtimeKind": job.get("runtimeKind"),
        "label": job.get("label"),
        "status": job.get("status"),
        "jobRevision": job.get("jobRevision"),
        "requestHash": job.get("requestHash"),
        "resultHash": job.get("resultHash"),
        "jobHash": job.get("jobHash"),
        "completedAt": job.get("completedAt"),
    }


def _stage(stage: str, ready: bool, evidence: Dict[str, Any], note: str = "") -> Dict[str, Any]:
    return {"stage": stage, "ready": bool(ready), "evidence": evidence, "note": note}


def compose_study(req: StudyComposerRequest) -> Dict[str, Any]:
    project = load_project(req.projectKey)
    workspace = project.get("workspace") or {}
    assets = [_asset_binding(req.projectKey, key) for key in req.assetKeys]
    jobs = [_job_binding(req.projectKey, jid) for jid in req.executionJobIds]
    snapshot = load_snapshot(req.projectKey, req.analysisSnapshotHash) if req.analysisSnapshotHash else None
    package = load_package(req.projectKey, req.publicationPackageHash) if req.publicationPackageHash else None
    if package and req.analysisSnapshotHash and package.get("snapshotHash") != req.analysisSnapshotHash:
        raise ValueError("publication package is not bound to the selected analysis snapshot")

    stages = [
        _stage("question", bool(req.researchQuestion.strip()), {"researchQuestionPresent": bool(req.researchQuestion.strip()), "objectiveCount": len(req.objectives)}),
        _stage("protocol", bool(req.protocol.designType.strip() or req.protocol.methods), {"designType": req.protocol.designType, "methodCount": len(req.protocol.methods), "hypothesisPresent": bool(req.protocol.hypothesis.strip()), "preregistrationRefPresent": bool(req.protocol.preregistrationRef.strip())}),
        _stage("inputs", bool(assets or req.parameterSetRefs), {"assetCount": len(assets), "parameterSetRefCount": len(req.parameterSetRefs)}),
        _stage("execution", bool(jobs) and all(j.get("status") == "completed" for j in jobs), {"jobCount": len(jobs), "completedJobCount": sum(1 for j in jobs if j.get("status") == "completed")}),
        _stage("analysis", snapshot is not None, {"analysisSnapshotHash": snapshot.get("snapshotHash") if snapshot else "", "findingCount": len(req.findings)}),
        _stage("publication", package is not None, {"publicationPackageHash": package.get("packageHash") if package else "", "destinationCount": len((package or {}).get("destinations") or [])}),
    ]
    ready_count = sum(1 for s in stages if s["ready"])
    source_hashes = {
        "projectHash": workspace.get("projectHash") or project.get("projectHash"),
        "assetRecordHashes": {a["assetKey"]: a.get("recordHash") or a.get("assetHash") for a in assets},
        "jobHashes": {j["jobId"]: j.get("jobHash") for j in jobs},
        "analysisSnapshotHash": snapshot.get("snapshotHash") if snapshot else None,
        "analysisSnapshotRecordHash": snapshot.get("recordHash") if snapshot else None,
        "publicationPackageHash": package.get("packageHash") if package else None,
        "publicationPackageRecordHash": package.get("recordHash") if package else None,
    }
    out: Dict[str, Any] = {
        "ok": True,
        "schema": STUDY_SCHEMA,
        "version": VERSION,
        "release": "Unified Scientific Study Composer",
        "projectKey": req.projectKey,
        "studyKey": req.studyKey,
        "title": req.title,
        "description": req.description,
        "status": req.status,
        "researchQuestion": req.researchQuestion,
        "objectives": req.objectives,
        "protocol": req.protocol.model_dump(),
        "inputs": {"assets": assets, "parameterSetRefs": req.parameterSetRefs},
        "execution": {"jobs": jobs},
        "analysis": {"snapshot": snapshot, "findings": [x.model_dump() for x in req.findings]},
        "publication": {"package": package},
        "tags": req.tags,
        "stageReadiness": stages,
        "readinessSummary": {"ready": ready_count, "total": len(stages), "allStagesReady": ready_count == len(stages)},
        "sourceHashes": source_hashes,
        "boundaries": manifest()["boundaries"],
    }
    out["studyHash"] = content_hash({k: v for k, v in out.items() if k != "studyHash"})
    out["studyRef"] = f"sc://workbench/study/{req.projectKey}/{out['studyHash']}"
    return out


def save_study(req: SaveStudyRequest) -> Dict[str, Any]:
    base_fields = set(StudyComposerRequest.model_fields)
    study = compose_study(StudyComposerRequest(**req.model_dump(include=base_fields)))
    record: Dict[str, Any] = {
        **study,
        "recordLabel": req.recordLabel,
        "createdBy": req.createdBy,
        "createdAt": _now(),
    }
    record_hash_basis = {k: v for k, v in record.items() if k not in {"createdAt", "recordHash", "idempotent"}}
    record["recordHash"] = content_hash(record_hash_basis)
    path = _study_path(req.projectKey, study["studyHash"])
    if path.exists():
        existing = _json_read(path)
        expected = content_hash({k: v for k, v in existing.items() if k not in {"createdAt", "recordHash", "idempotent"}})
        if existing.get("recordHash") != expected:
            raise ValueError("stored scientific study failed integrity validation")
        existing["idempotent"] = True
        return existing
    _atomic_json_write(path, record)
    record["idempotent"] = False
    return record


def list_studies(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    root = _study_dir(project_key)
    rows: List[Dict[str, Any]] = []
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                rec = _json_read(path)
                if rec.get("projectKey") != project_key:
                    continue
                rows.append({k: rec.get(k) for k in ("studyHash", "studyRef", "studyKey", "title", "status", "recordLabel", "createdBy", "createdAt", "recordHash")})
            except Exception:
                continue
    rows.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return {"ok": True, "schema": STUDY_SCHEMA, "version": VERSION, "projectKey": project_key, "studyCount": len(rows), "studies": rows}


def load_study(project_key: str, study_hash: str) -> Dict[str, Any]:
    load_project(project_key)
    path = _study_path(project_key, study_hash)
    if not path.exists():
        raise FileNotFoundError("scientific study not found")
    rec = _json_read(path)
    if rec.get("projectKey") != project_key or rec.get("studyHash") != study_hash:
        raise ValueError("scientific study identity mismatch")
    expected = content_hash({k: v for k, v in rec.items() if k not in {"createdAt", "recordHash", "idempotent"}})
    if rec.get("recordHash") != expected:
        raise ValueError("scientific study failed integrity validation")
    return rec


def source_catalog(project_key: str) -> Dict[str, Any]:
    project = load_project(project_key)
    jobs = list_jobs(project_key=project_key)
    assets = search_assets(project_key, limit=200)
    snapshots = list_snapshots(project_key)
    packages = list_packages(project_key)
    studies = list_studies(project_key)
    out: Dict[str, Any] = {
        "ok": True,
        "schema": CATALOG_SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "projectRevision": project.get("projectRevision") or (project.get("workspace") or {}).get("projectRevision"),
        "jobCount": jobs.get("jobCount", 0),
        "jobs": jobs.get("jobs", []),
        "assetCount": len(assets.get("results") or []),
        "assets": assets.get("results", []),
        "analysisSnapshotCount": snapshots.get("snapshotCount", 0),
        "analysisSnapshots": snapshots.get("snapshots", []),
        "publicationPackageCount": packages.get("packageCount", 0),
        "publicationPackages": packages.get("packages", []),
        "studyCount": studies.get("studyCount", 0),
        "studies": studies.get("studies", []),
        "boundaries": {"catalogMutatesSources": False, "catalogInfersScientificValidity": False, "catalogDispatchesToCore": False},
    }
    out["catalogHash"] = content_hash(out)
    return out


def core_study_plan(req: CoreStudyPlanRequest) -> Dict[str, Any]:
    base_fields = set(StudyComposerRequest.model_fields)
    study = compose_study(StudyComposerRequest(**req.model_dump(include=base_fields)))
    project = load_project(req.projectKey)
    workspace = project.get("workspace") or {}
    cfg = core_config()
    out: Dict[str, Any] = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "studyKey": req.studyKey,
        "studyHash": study["studyHash"],
        "coreProjectEntityId": req.coreProjectEntityId or req.projectKey,
        "coreSessionId": req.coreSessionId or workspace.get("coreSessionId") or "",
        "visibility": req.visibility,
        "createdBy": req.createdBy,
        "coreEnabled": bool(cfg.get("enabled")),
        "coreTarget": cfg.get("baseUrl") or "",
        "bindingPlan": {
            "objectType": "workbench.unified-scientific-study",
            "objectRef": study["studyRef"],
            "objectHash": study["studyHash"],
            "projectRef": workspace.get("workspaceRef") or f"sc://workbench/project/{req.projectKey}",
            "stageReadiness": study["stageReadiness"],
            "sourceHashes": study["sourceHashes"],
        },
        "boundaries": {
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "coreGovernanceAuthorityPreserved": True,
            "scientificValidityInferred": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


@router.get("/study-composer/manifest")
def study_composer_manifest() -> Dict[str, Any]:
    return manifest()


@router.get("/study-composer/source-catalog/{project_key}")
def study_composer_source_catalog(project_key: str) -> Dict[str, Any]:
    try:
        return source_catalog(project_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/study-composer/compose")
def study_composer_compose(req: StudyComposerRequest) -> Dict[str, Any]:
    try:
        return compose_study(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/study-composer/studies")
def study_composer_save(req: SaveStudyRequest) -> Dict[str, Any]:
    try:
        return save_study(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/study-composer/studies/{project_key}")
def study_composer_list(project_key: str) -> Dict[str, Any]:
    try:
        return list_studies(project_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/study-composer/studies/{project_key}/{study_hash}")
def study_composer_get(project_key: str, study_hash: str) -> Dict[str, Any]:
    try:
        return load_study(project_key, study_hash)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/study-composer/plan")
def study_composer_core_plan(req: CoreStudyPlanRequest) -> Dict[str, Any]:
    try:
        return core_study_plan(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/v900/status")
def status() -> Dict[str, Any]:
    m = manifest()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": m["release"],
        "unifiedScientificStudyComposer": True,
        "explicitStageReadiness": True,
        "contentAddressedStudyRecords": True,
        "analysisSnapshotBinding": True,
        "publicationPackageBinding": True,
        "automaticScientificValidityInference": False,
        "automaticCoreDispatch": False,
        "manifestHash": m["manifestHash"],
    }

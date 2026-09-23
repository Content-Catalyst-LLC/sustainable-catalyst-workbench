"""Workbench v8.10.0 — Reproducible Analysis Board.

Content-addressed research analysis assembly over authoritative Workbench project,
asset, execution, comparison, figure, timeline, and lineage objects. The board binds
existing source objects and explicit researcher-authored narrative into a reproducible
analytical surface without replacing those source systems or inferring scientific truth.
Immutable snapshots are persisted under the existing v8.1 Workbench data root.
Platform Core integration remains explicit, two-phase, and plan-only.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
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
from .v830 import _load_asset_record, search_assets
from .v840 import _load_job, list_jobs
from .v850 import collect_timeline, lineage_graph
from .v880 import ComparisonRequest, compare
from .v890 import FigureComposeRequest, compose_figure

VERSION = APP_VERSION
SCHEMA = "sc-workbench-reproducible-analysis-board/1.0"
BOARD_SCHEMA = "sc-workbench-reproducible-analysis-board-specification/1.0"
SNAPSHOT_SCHEMA = "sc-workbench-reproducible-analysis-board-snapshot/1.0"
CATALOG_SCHEMA = "sc-workbench-reproducible-analysis-board-source-catalog/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-reproducible-analysis-board-core-plan/1.0"
MAX_JOBS = 40
MAX_ASSETS = 100
MAX_FIGURES = 12
MAX_NARRATIVE_ITEMS = 100
MAX_TIMELINE_EVENTS = 250
router = APIRouter(tags=["workbench-v8100-reproducible-analysis-board"])

NarrativeKind = Literal["assumption", "method", "finding", "note"]
NarrativeState = Literal["working", "final"]
Visibility = Literal["private", "internal", "public"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _snapshot_dir(project_key: str) -> Path:
    return _store_root() / "analysis-boards" / _stable_id(project_key) / "snapshots"


def _snapshot_path(project_key: str, snapshot_hash: str) -> Path:
    return _snapshot_dir(project_key) / f"{snapshot_hash}.json"


class NarrativeItem(BaseModel):
    itemId: str = Field(min_length=1, max_length=100)
    kind: NarrativeKind
    title: str = Field(default="", max_length=300)
    text: str = Field(min_length=1, max_length=10000)
    evidenceRefs: List[str] = Field(default_factory=list, max_length=100)
    state: NarrativeState = "working"

    @model_validator(mode="after")
    def normalize(self):
        self.itemId = self.itemId.strip()
        self.evidenceRefs = [str(x).strip() for x in self.evidenceRefs if str(x).strip()]
        if len(self.evidenceRefs) != len(set(self.evidenceRefs)):
            raise ValueError("evidenceRefs must be unique")
        return self


class AnalysisBoardRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    title: str = Field(default="Reproducible analysis board", max_length=500)
    description: str = Field(default="", max_length=4000)
    jobIds: List[str] = Field(default_factory=list, max_length=MAX_JOBS)
    assetKeys: List[str] = Field(default_factory=list, max_length=MAX_ASSETS)
    comparison: Optional[ComparisonRequest] = None
    figures: List[FigureComposeRequest] = Field(default_factory=list, max_length=MAX_FIGURES)
    narrative: List[NarrativeItem] = Field(default_factory=list, max_length=MAX_NARRATIVE_ITEMS)
    includeTimeline: bool = True
    timelineEventIds: List[str] = Field(default_factory=list, max_length=MAX_TIMELINE_EVENTS)
    includeLineage: bool = True

    @model_validator(mode="after")
    def validate_sources(self):
        self.jobIds = [str(x).strip() for x in self.jobIds if str(x).strip()]
        self.assetKeys = [str(x).strip() for x in self.assetKeys if str(x).strip()]
        self.timelineEventIds = [str(x).strip() for x in self.timelineEventIds if str(x).strip()]
        for label, values in (("jobIds", self.jobIds), ("assetKeys", self.assetKeys), ("timelineEventIds", self.timelineEventIds)):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} must be unique")
        if self.comparison and self.comparison.projectKey != self.projectKey:
            raise ValueError("comparison projectKey must match board projectKey")
        for fig in self.figures:
            if fig.projectKey != self.projectKey:
                raise ValueError("figure projectKey must match board projectKey")
        item_ids = [x.itemId for x in self.narrative]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("narrative itemId values must be unique")
        return self


class SnapshotRequest(AnalysisBoardRequest):
    snapshotLabel: str = Field(default="Analysis board snapshot", max_length=500)
    createdBy: str = Field(default="workbench", min_length=1, max_length=160)


class CoreAnalysisBoardPlanRequest(AnalysisBoardRequest):
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Visibility = "internal"
    createdBy: str = Field(default="workbench", min_length=1, max_length=160)


def _job_source(project_key: str, job_id: str) -> Dict[str, Any]:
    job = _load_job(job_id)
    if job.get("projectKey") != project_key:
        raise ValueError(f"job {job_id} belongs to another project")
    return {
        "jobId": job_id,
        "label": job.get("label") or job_id,
        "status": job.get("status"),
        "runtimeKind": job.get("runtimeKind"),
        "jobRevision": job.get("jobRevision"),
        "requestHash": job.get("requestHash"),
        "resultHash": job.get("resultHash"),
        "jobHash": job.get("jobHash"),
        "createdAt": job.get("createdAt"),
        "completedAt": job.get("completedAt"),
    }


def _asset_source(project_key: str, asset_key: str) -> Dict[str, Any]:
    rec = _load_asset_record(project_key, asset_key)
    asset = rec.get("asset") or {}
    return {
        "assetKey": asset_key,
        "assetRevision": rec.get("assetRevision") or rec.get("revision"),
        "assetType": asset.get("assetType"),
        "title": asset.get("title"),
        "contentHash": asset.get("contentHash"),
        "assetHash": asset.get("assetHash"),
        "recordHash": rec.get("recordHash"),
        "assetRef": asset.get("assetRef"),
        "origin": asset.get("origin"),
    }


def _narrative_groups(items: List[NarrativeItem]) -> Dict[str, List[Dict[str, Any]]]:
    grouped = {"assumptions": [], "methods": [], "findings": [], "notes": []}
    mapping = {"assumption": "assumptions", "method": "methods", "finding": "findings", "note": "notes"}
    for item in items:
        grouped[mapping[item.kind]].append(item.model_dump())
    return grouped


def _all_job_ids(req: AnalysisBoardRequest) -> List[str]:
    ids = list(req.jobIds)
    if req.comparison:
        ids.extend(req.comparison.jobIds)
    for fig in req.figures:
        ids.extend(fig.jobIds)
    return list(dict.fromkeys(ids))


def source_catalog(project_key: str) -> Dict[str, Any]:
    project = load_project(project_key)
    jobs = list_jobs(project_key=project_key).get("jobs") or []
    assets = search_assets(project_key, limit=MAX_ASSETS).get("results") or []
    timeline = collect_timeline(project_key)
    snapshots = list_snapshots(project_key)
    out = {
        "ok": True,
        "schema": CATALOG_SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "projectRevision": (project.get("workspace") or {}).get("projectRevision"),
        "jobs": jobs[:MAX_JOBS],
        "assets": assets[:MAX_ASSETS],
        "timelineEventCount": len(timeline.get("events") or []),
        "snapshotCount": snapshots.get("snapshotCount", 0),
        "snapshots": snapshots.get("snapshots", []),
        "boundaries": {
            "catalogMutatesSources": False,
            "catalogInfersScientificValidity": False,
            "catalogDispatchesToCore": False,
        },
    }
    out["catalogHash"] = content_hash(out)
    return out


def build_board(req: AnalysisBoardRequest) -> Dict[str, Any]:
    project_record = load_project(req.projectKey)
    workspace = project_record.get("workspace") or {}
    all_job_ids = _all_job_ids(req)
    jobs = [_job_source(req.projectKey, jid) for jid in all_job_ids]
    assets = [_asset_source(req.projectKey, key) for key in req.assetKeys]

    comparison = compare(req.comparison) if req.comparison else None
    figures = [compose_figure(fig) for fig in req.figures]

    timeline_block = None
    if req.includeTimeline:
        timeline = collect_timeline(req.projectKey)
        events = timeline.get("events") or []
        if req.timelineEventIds:
            wanted = set(req.timelineEventIds)
            events = [e for e in events if e.get("eventId") in wanted or e.get("eventHash") in wanted]
            missing = wanted - {str(e.get("eventId") or e.get("eventHash") or "") for e in events}
            # eventHash and eventId are both accepted references; only fail if none match a supplied ref.
            for ref in list(missing):
                if any(ref == str(e.get("eventHash") or "") for e in events):
                    missing.discard(ref)
            if missing:
                raise ValueError("timeline event references not found: " + ", ".join(sorted(missing)))
        events = events[:MAX_TIMELINE_EVENTS]
        timeline_block = {
            "schema": timeline.get("schema"),
            "timelineHash": timeline.get("timelineHash"),
            "eventCount": len(events),
            "events": events,
            "selectionWasExplicit": bool(req.timelineEventIds),
        }

    lineage = lineage_graph(req.projectKey) if req.includeLineage else None
    narrative = _narrative_groups(req.narrative)

    source_hashes = {
        "projectHash": workspace.get("projectHash") or project_record.get("projectHash"),
        "jobHashes": {j["jobId"]: j.get("jobHash") for j in jobs},
        "assetHashes": {a["assetKey"]: a.get("recordHash") or a.get("assetHash") for a in assets},
        "comparisonHash": comparison.get("comparisonHash") if comparison else None,
        "figureHashes": [f.get("figureHash") for f in figures],
        "timelineHash": timeline_block.get("timelineHash") if timeline_block else None,
        "lineageHash": lineage.get("lineageHash") if lineage else None,
    }

    sections = [
        {"sectionId": "sources", "title": "Sources", "kind": "sources", "jobCount": len(jobs), "assetCount": len(assets)},
        {"sectionId": "analysis", "title": "Analysis", "kind": "analysis", "comparisonCount": 1 if comparison else 0, "figureCount": len(figures)},
        {"sectionId": "narrative", "title": "Research narrative", "kind": "narrative", "itemCount": len(req.narrative)},
    ]
    if timeline_block:
        sections.append({"sectionId": "timeline", "title": "Timeline context", "kind": "timeline", "eventCount": timeline_block["eventCount"]})
    if lineage:
        sections.append({"sectionId": "lineage", "title": "Lineage", "kind": "lineage", "nodeCount": len(lineage.get("nodes") or []), "edgeCount": len(lineage.get("edges") or [])})

    out: Dict[str, Any] = {
        "ok": True,
        "schema": BOARD_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "title": req.title,
        "description": req.description,
        "project": {
            "projectRevision": workspace.get("projectRevision"),
            "projectHash": workspace.get("projectHash") or project_record.get("projectHash"),
            "activeEnvironmentKey": workspace.get("activeEnvironmentKey"),
            "activeEnvironmentRevision": workspace.get("activeEnvironmentRevision"),
        },
        "sections": sections,
        "sources": {"jobs": jobs, "assets": assets},
        "analysis": {"comparison": comparison, "figures": figures},
        "narrative": narrative,
        "timeline": timeline_block,
        "lineage": lineage,
        "provenance": {
            "sourceHashes": source_hashes,
            "authoritativeSystems": {
                "project": "v8.2 unified research project workspace",
                "assets": "v8.3 research asset registry",
                "executions": "v8.4 execution console",
                "timelineAndLineage": "v8.5 research timeline",
                "comparisons": "v8.8 comparative analysis",
                "figures": "v8.9 scientific figure composer",
            },
            "sourceHashesPreserved": True,
            "narrativeIsResearcherAuthored": True,
        },
        "reproducibility": {
            "contentAddressed": True,
            "sourceVersionsPinnedByHash": True,
            "comparisonRegenerationDeterministic": comparison is None or bool(comparison.get("comparisonHash")),
            "figureRegenerationDeterministic": all(bool(f.get("figureHash")) for f in figures),
            "snapshotEligible": True,
            "automaticReexecutionPerformed": False,
        },
        "boundaries": {
            "boardIsScientificSourceOfTruth": False,
            "sourceObjectsMutated": False,
            "findingsAutomaticallyGenerated": False,
            "scientificValidityInferred": False,
            "causalInferencePerformed": False,
            "statisticalSignificanceInferred": False,
            "automaticWinnerSelectionPerformed": False,
            "automaticCoreDispatchPerformed": False,
        },
    }
    out["boardHash"] = content_hash(out)
    return out


def save_snapshot(req: SnapshotRequest) -> Dict[str, Any]:
    board_fields = set(AnalysisBoardRequest.model_fields)
    board = build_board(AnalysisBoardRequest(**req.model_dump(include=board_fields)))
    immutable = {
        "schema": SNAPSHOT_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "boardHash": board["boardHash"],
        "board": board,
    }
    snapshot_hash = content_hash(immutable)
    path = _snapshot_path(req.projectKey, snapshot_hash)
    if path.exists():
        record = _json_read(path)
        if record.get("snapshotHash") != snapshot_hash:
            raise ValueError("stored analysis board snapshot failed identity validation")
        record["idempotent"] = True
        return record
    record = {
        "ok": True,
        "schema": SNAPSHOT_SCHEMA,
        "version": VERSION,
        "snapshotHash": snapshot_hash,
        "snapshotRef": f"sc://workbench/analysis-boards/{req.projectKey}/{snapshot_hash[:24]}",
        "snapshotLabel": req.snapshotLabel,
        "createdBy": req.createdBy,
        "createdAt": _now(),
        "projectKey": req.projectKey,
        "boardHash": board["boardHash"],
        "board": board,
        "immutable": True,
        "idempotent": False,
    }
    record["recordHash"] = content_hash({k: v for k, v in record.items() if k not in ("recordHash", "idempotent")})
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(path, record)
    return record


def list_snapshots(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    root = _snapshot_dir(project_key)
    rows: List[Dict[str, Any]] = []
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r = _json_read(p)
            except Exception:
                continue
            if r.get("projectKey") != project_key:
                continue
            rows.append({
                "snapshotHash": r.get("snapshotHash"),
                "snapshotRef": r.get("snapshotRef"),
                "snapshotLabel": r.get("snapshotLabel"),
                "boardHash": r.get("boardHash"),
                "createdBy": r.get("createdBy"),
                "createdAt": r.get("createdAt"),
                "recordHash": r.get("recordHash"),
            })
    rows.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return {"ok": True, "schema": SNAPSHOT_SCHEMA, "version": VERSION, "projectKey": project_key, "snapshotCount": len(rows), "snapshots": rows}


def load_snapshot(project_key: str, snapshot_hash: str) -> Dict[str, Any]:
    load_project(project_key)
    path = _snapshot_path(project_key, snapshot_hash)
    if not path.exists():
        raise FileNotFoundError("analysis board snapshot not found")
    record = _json_read(path)
    if record.get("projectKey") != project_key or record.get("snapshotHash") != snapshot_hash:
        raise ValueError("analysis board snapshot identity mismatch")
    expected = content_hash({k: v for k, v in record.items() if k not in ("recordHash", "idempotent")})
    if record.get("recordHash") != expected:
        raise ValueError("analysis board snapshot failed integrity validation")
    return record


def core_analysis_board_plan(req: CoreAnalysisBoardPlanRequest) -> Dict[str, Any]:
    board_fields = set(AnalysisBoardRequest.model_fields)
    board = build_board(AnalysisBoardRequest(**req.model_dump(include=board_fields)))
    project = load_project(req.projectKey)
    workspace = project.get("workspace") or {}
    sid = str(req.coreSessionId or workspace.get("coreSessionId") or "").strip()[:255]
    base = core_project_plan(ProjectCorePlanRequest(
        projectKey=req.projectKey,
        coreProjectEntityId=req.coreProjectEntityId or req.projectKey,
        coreSessionId=sid,
        visibility=req.visibility,
        createdBy=req.createdBy,
    ))
    out = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "coreSessionId": sid or None,
        "coreSessionIdMustComeFromCore": True,
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "projectPlan": base,
        "boardHash": board["boardHash"],
        "coreRequests": list(base.get("coreRequests") or []),
        "boardBindingIsReproducibleAnalyticalViewOnly": True,
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "scientificValidityInferenceAuthorized": False,
    }
    if sid:
        out["coreRequests"].append({
            "path": CORE_PATHS["objectBindings"],
            "method": "POST",
            "phase": "reproducible-analysis-board-bind",
            "data": {
                "session_id": sid,
                "object_type": "workbench.reproducible-analysis-board",
                "object_ref": f"sc://workbench/analysis-boards/{req.projectKey}/{board['boardHash'][:24]}",
                "version_ref": f"sc://workbench/analysis-boards/{req.projectKey}@{VERSION}",
                "content_hash": board["boardHash"],
                "role": "reproducible-analytical-view",
                "visibility": req.visibility,
                "metadata": {
                    "workbenchVersion": VERSION,
                    "projectKey": req.projectKey,
                    "scientificSourceOfTruth": False,
                    "sourceHashesPreserved": True,
                    "narrativeResearcherAuthored": True,
                },
            },
            "dispatchPerformed": False,
        })
    out["planHash"] = content_hash(out)
    return out


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Reproducible Analysis Board",
        "capabilities": {
            "crossObjectAnalysisAssembly": True,
            "projectAssetExecutionBinding": True,
            "comparisonEmbedding": True,
            "scientificFigureEmbedding": True,
            "timelineContextBinding": True,
            "lineageContextBinding": True,
            "researcherAuthoredNarrative": True,
            "contentAddressedBoardHash": True,
            "immutableAnalysisSnapshots": True,
            "snapshotIntegrityValidation": True,
            "coreAnalysisBoardPlanning": True,
        },
        "authorities": {
            "projects": "v8.2",
            "assets": "v8.3",
            "executions": "v8.4",
            "timelineAndLineage": "v8.5",
            "comparisons": "v8.8",
            "figures": "v8.9",
        },
        "boundaries": {
            "boardIsScientificSourceOfTruth": False,
            "automaticFindingGenerationAuthorized": False,
            "scientificValidityInferenceAuthorized": False,
            "causalInferenceAuthorized": False,
            "statisticalSignificanceInferenceAuthorized": False,
            "automaticWinnerSelectionAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


@router.get("/analysis-board/manifest")
def manifest_route():
    return manifest()


@router.get("/analysis-board/source-catalog/{project_key}")
def source_catalog_route(project_key: str):
    try:
        return source_catalog(project_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/analysis-board/build")
def build_route(req: AnalysisBoardRequest):
    try:
        return build_board(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/analysis-board/snapshots")
def snapshot_route(req: SnapshotRequest):
    try:
        return save_snapshot(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/analysis-board/snapshots/{project_key}")
def snapshots_route(project_key: str):
    try:
        return list_snapshots(project_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/analysis-board/snapshots/{project_key}/{snapshot_hash}")
def snapshot_load_route(project_key: str, snapshot_hash: str):
    try:
        return load_snapshot(project_key, snapshot_hash)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/analysis-board/plan")
def core_plan_route(req: CoreAnalysisBoardPlanRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    try:
        return core_analysis_board_plan(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/v8100/status")
def status_route():
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Reproducible Analysis Board",
        "crossObjectAnalysisAssembly": True,
        "immutableAnalysisSnapshots": True,
        "sourceHashesPreserved": True,
        "researcherAuthoredNarrative": True,
        "automaticFindingGeneration": False,
        "scientificValidityInference": False,
        "automaticCoreDispatch": False,
    }

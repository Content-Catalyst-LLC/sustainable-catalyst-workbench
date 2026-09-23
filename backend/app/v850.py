"""Workbench v8.5.0 — Research Timeline & Run History.

Project-wide chronological history derived from the authoritative v8 stores. The timeline
never becomes a competing source of truth: project activity remains owned by v8.2,
environment revisions/checkpoints/recovery by v8.1, asset revisions by v8.3, and execution
job lifecycle/results by v8.4. Timeline events are content-addressed projections with
explicit timestamp provenance, neutral comparison, lineage navigation, and two-phase
Platform Core binding plans. No scientific execution or automatic Core dispatch occurs.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v660 import CORE_PATHS, CORE_UNIFIED_RUNTIME_CONTRACT
from .v810 import list_checkpoints, list_revisions, _json_read
from .v820 import ProjectCorePlanRequest, core_project_plan, load_project, project_activity
from .v830 import _project_registry_dir, _record_hash
from .v840 import _jobs_root, _load_job

VERSION = APP_VERSION
SCHEMA = "sc-workbench-research-timeline-run-history/1.0"
EVENT_SCHEMA = "sc-workbench-research-timeline-event/1.0"
RUN_HISTORY_SCHEMA = "sc-workbench-research-run-history/1.0"
LINEAGE_SCHEMA = "sc-workbench-research-timeline-lineage/1.0"
COMPARE_SCHEMA = "sc-workbench-research-timeline-comparison/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-research-timeline-core-plan/1.0"
MAX_EVENTS = 2000
MAX_RUNS = 500
MAX_CORE_EVENTS = 100

TimelineSource = Literal["project", "environment", "checkpoint", "asset", "execution"]

router = APIRouter(tags=["workbench-v850-research-timeline-run-history"])


def _safe(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _event_hash(event: Dict[str, Any]) -> str:
    candidate = deepcopy(event)
    candidate.pop("eventHash", None)
    candidate.pop("eventId", None)
    return content_hash(candidate)


def _make_event(*, project_key: str, source: TimelineSource, event_type: str,
                title: str, at: Optional[str], time_source: str,
                actor: str = "", reason: str = "", status: str = "",
                source_ref: str = "", revision: Optional[int] = None,
                hashes: Optional[Dict[str, Any]] = None,
                metadata: Optional[Dict[str, Any]] = None,
                lineage: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "ok": True,
        "schema": EVENT_SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "source": source,
        "eventType": _safe(event_type, 160),
        "title": _safe(title, 500),
        "at": at or None,
        "timeSource": _safe(time_source, 80),
        "chronologyAuthoritative": time_source in {"recorded", "checkpoint-recorded", "job-history-recorded"},
        "actor": _safe(actor, 160) or None,
        "reason": _safe(reason, 1000) or None,
        "status": _safe(status, 120) or None,
        "sourceRef": _safe(source_ref, 1200) or None,
        "revision": revision,
        "hashes": deepcopy(hashes or {}),
        "metadata": deepcopy(metadata or {}),
        "lineage": deepcopy(lineage or {}),
    }
    event["eventHash"] = _event_hash(event)
    event["eventId"] = "tle-" + content_hash({"projectKey": project_key, "source": source, "eventHash": event["eventHash"]})[:28]
    return event


def _sort_key(event: Dict[str, Any]):
    at = event.get("at")
    # Undated historical records remain explicit and deterministic instead of using
    # filesystem mtimes that may change after backup/restore.
    return (0 if at else 1, at or "", event.get("source") or "", event.get("revision") or 0, event.get("eventId") or "")


def _project_events(project_key: str) -> List[Dict[str, Any]]:
    activity = project_activity(project_key).get("activity") or []
    out: List[Dict[str, Any]] = []
    for item in activity:
        rev = item.get("projectRevision")
        out.append(_make_event(
            project_key=project_key, source="project", event_type=item.get("type") or "project-activity",
            title=f"Project workspace revision {rev}", at=item.get("at"), time_source="recorded",
            actor=item.get("actor") or "", reason=item.get("reason") or "", revision=rev,
            source_ref=f"sc://workbench/research-project/{project_key}/revision/{rev}",
            hashes={"activityId": item.get("activityId"), "workspaceHash": item.get("workspaceHash"), "activeEnvironmentHash": item.get("activeEnvironmentHash")},
            metadata={"activeEnvironmentRevision": item.get("activeEnvironmentRevision")},
            lineage={"parentProjectRevision": (int(rev) - 1) if isinstance(rev, int) and rev > 1 else None},
        ))
    return out


def _environment_events(project_key: str, environment_key: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    revisions = list_revisions(environment_key).get("revisions") or []
    for rec in revisions:
        rev = rec.get("revision")
        recovered = rec.get("recoveredFrom") or None
        etype = "environment-recovery-applied" if recovered else "environment-revision-saved"
        title = f"Environment revision {rev}" + (" recovered" if recovered else " saved")
        out.append(_make_event(
            project_key=project_key, source="environment", event_type=etype, title=title,
            at=rec.get("savedAt"), time_source="recorded", actor=rec.get("actor") or "",
            reason=rec.get("reason") or "", revision=rev, source_ref=rec.get("revisionRef") or "",
            hashes={"revisionHash": rec.get("revisionHash"), "environmentHash": rec.get("environmentHash"), "parentRevisionHash": rec.get("parentRevisionHash")},
            metadata={"environmentKey": environment_key, "recoveredFrom": recovered},
            lineage={"parentRevision": rec.get("parentRevision"), "recoveredFrom": recovered},
        ))
    checkpoints = list_checkpoints(environment_key).get("checkpoints") or []
    for cp in checkpoints:
        out.append(_make_event(
            project_key=project_key, source="checkpoint", event_type="environment-checkpoint-created",
            title=f"Checkpoint {cp.get('label') or cp.get('checkpointId')}", at=cp.get("createdAt"),
            time_source="checkpoint-recorded", actor=cp.get("actor") or "", reason=cp.get("note") or "",
            revision=cp.get("revision"), source_ref=f"sc://workbench/research-environment/{environment_key}/checkpoint/{cp.get('checkpointId')}",
            hashes={"checkpointHash": cp.get("checkpointHash"), "revisionHash": cp.get("revisionHash"), "environmentHash": cp.get("environmentHash")},
            metadata={"environmentKey": environment_key, "checkpointId": cp.get("checkpointId"), "label": cp.get("label")},
            lineage={"checkpointOfRevision": cp.get("revision")},
        ))
    return out


def _asset_events(project_key: str) -> List[Dict[str, Any]]:
    root = _project_registry_dir(project_key) / "assets"
    out: List[Dict[str, Any]] = []
    if not root.exists():
        return out
    for asset_dir in sorted(root.iterdir()):
        if not asset_dir.is_dir():
            continue
        idx_path = asset_dir / "index.json"
        if not idx_path.exists():
            continue
        idx = _json_read(idx_path)
        asset_key = _safe(idx.get("assetKey"), 240)
        rev_root = asset_dir / "revisions"
        if not asset_key or not rev_root.exists():
            continue
        for path in sorted(rev_root.glob("*.json")):
            rec = _json_read(path)
            if rec.get("recordHash") != _record_hash(rec):
                raise ValueError(f"research asset {asset_key} revision failed integrity validation")
            asset = rec.get("asset") or {}
            rev = rec.get("assetRevision")
            registered_at = rec.get("registeredAt")
            out.append(_make_event(
                project_key=project_key, source="asset", event_type="research-asset-revision-registered",
                title=f"{asset.get('title') or asset_key} · revision {rev}", at=registered_at,
                time_source="recorded" if registered_at else "unavailable-in-v8.3-record",
                actor=rec.get("actor") or "", reason=rec.get("reason") or "", revision=rev,
                source_ref=asset.get("assetRef") or f"sc://workbench/research-asset/{project_key}/{asset_key}",
                hashes={"recordHash": rec.get("recordHash"), "assetHash": rec.get("assetHash"), "contentHash": rec.get("contentHash")},
                metadata={"assetKey": asset_key, "assetType": asset.get("assetType"), "tags": asset.get("tags") or [], "origin": asset.get("origin")},
                lineage={"parentAssetRevision": rec.get("parentAssetRevision"), "environmentRevision": asset.get("environmentRevision"), "environmentHash": asset.get("environmentHash")},
            ))
    return out


def _execution_events(project_key: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    root = _jobs_root()
    if not root.exists():
        return out
    for path in sorted(root.glob("*.json")):
        try:
            raw = _json_read(path)
            job = _load_job(raw.get("jobId", ""))
        except Exception as exc:
            raise ValueError(f"execution job integrity validation failed: {exc}") from exc
        if job.get("projectKey") != project_key:
            continue
        history = job.get("history") or []
        previous_revision = None
        for h in history:
            rev = h.get("revision")
            status = h.get("status") or "unknown"
            hashes = {"jobHash": job.get("jobHash"), "requestHash": job.get("requestHash")}
            if status in ("completed", "failed"):
                hashes["resultHash"] = job.get("resultHash")
            out.append(_make_event(
                project_key=project_key, source="execution", event_type=f"execution-{status}",
                title=f"{job.get('label') or job.get('runtimeKind')} · {status}", at=h.get("at"),
                time_source="job-history-recorded", actor=h.get("actor") or "", reason=h.get("reason") or "",
                status=status, revision=rev, source_ref=f"sc://workbench/execution-console/job/{job.get('jobId')}",
                hashes=hashes,
                metadata={"jobId": job.get("jobId"), "runtimeKind": job.get("runtimeKind"), "label": job.get("label"), "scientificExecutionPerformed": job.get("scientificExecutionPerformed", False)},
                lineage={"previousJobRevision": previous_revision, "environmentRevision": job.get("environmentRevision"), "environmentHash": job.get("environmentHash")},
            ))
            previous_revision = rev
    return out


def collect_timeline(project_key: str) -> Dict[str, Any]:
    project = load_project(project_key)
    ws = project["workspace"]
    environment_key = ws.get("activeEnvironmentKey")
    events: List[Dict[str, Any]] = []
    events.extend(_project_events(project_key))
    if environment_key:
        events.extend(_environment_events(project_key, environment_key))
    events.extend(_asset_events(project_key))
    events.extend(_execution_events(project_key))
    events.sort(key=_sort_key)
    summary: Dict[str, int] = {}
    for e in events:
        summary[e["source"]] = summary.get(e["source"], 0) + 1
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key,
        "projectRevision": project.get("projectRevision"), "activeEnvironmentKey": environment_key,
        "activeEnvironmentRevision": ws.get("activeEnvironmentRevision"), "activeEnvironmentHash": ws.get("activeEnvironmentHash"),
        "eventCount": len(events), "sourceCounts": summary, "events": events,
        "derivedFromAuthoritativeStores": True, "timelineIsSourceOfTruth": False,
    }
    out["timelineHash"] = content_hash({k: v for k, v in out.items() if k != "timelineHash"})
    return out


def filtered_timeline(project_key: str, source: str = "", event_type: str = "", q: str = "", limit: int = 500) -> Dict[str, Any]:
    base = collect_timeline(project_key)
    rows = base["events"]
    if source:
        rows = [e for e in rows if e.get("source") == source]
    if event_type:
        rows = [e for e in rows if e.get("eventType") == event_type]
    if q:
        needle = q.lower()
        rows = [e for e in rows if needle in (" ".join([str(e.get("title") or ""), str(e.get("reason") or ""), str(e.get("metadata") or "")])).lower()]
    lim = max(1, min(int(limit), MAX_EVENTS))
    rows = rows[-lim:]
    result = {**{k: v for k, v in base.items() if k not in ("events", "eventCount", "timelineHash")}, "eventCount": len(rows), "events": rows, "filters": {"source": source or None, "eventType": event_type or None, "q": q or None, "limit": lim}}
    result["timelineHash"] = content_hash({k: v for k, v in result.items() if k != "timelineHash"})
    return result


def run_history(project_key: str, limit: int = 200) -> Dict[str, Any]:
    load_project(project_key)
    rows: List[Dict[str, Any]] = []
    root = _jobs_root()
    if root.exists():
        for path in sorted(root.glob("*.json")):
            raw = _json_read(path)
            job = _load_job(raw.get("jobId", ""))
            if job.get("projectKey") != project_key:
                continue
            rows.append({
                "jobId": job.get("jobId"), "runtimeKind": job.get("runtimeKind"), "label": job.get("label"),
                "status": job.get("status"), "jobRevision": job.get("jobRevision"), "requestHash": job.get("requestHash"),
                "resultHash": job.get("resultHash"), "createdAt": job.get("createdAt"), "startedAt": job.get("startedAt"),
                "completedAt": job.get("completedAt"), "cancelledAt": job.get("cancelledAt"), "history": deepcopy(job.get("history") or []),
                "scientificExecutionPerformed": job.get("scientificExecutionPerformed", False), "jobHash": job.get("jobHash"),
            })
    rows.sort(key=lambda x: (x.get("createdAt") or "", x.get("jobId") or ""), reverse=True)
    lim = max(1, min(int(limit), MAX_RUNS))
    out = {"ok": True, "schema": RUN_HISTORY_SCHEMA, "version": VERSION, "projectKey": project_key, "runCount": len(rows[:lim]), "runs": rows[:lim], "runHistoryDerivedFromExecutionConsole": True}
    out["runHistoryHash"] = content_hash(out)
    return out


def lineage_graph(project_key: str) -> Dict[str, Any]:
    timeline = collect_timeline(project_key)
    nodes, edges = [], []
    seen = set()
    env_nodes: Dict[int, str] = {}
    asset_nodes: Dict[tuple, str] = {}
    job_nodes: Dict[tuple, str] = {}
    project_nodes: Dict[int, str] = {}
    for e in timeline["events"]:
        nid = e["eventId"]
        if nid not in seen:
            nodes.append({"nodeId": nid, "source": e["source"], "eventType": e["eventType"], "title": e["title"], "revision": e.get("revision"), "eventHash": e["eventHash"], "sourceRef": e.get("sourceRef")})
            seen.add(nid)
        rev = e.get("revision")
        if e["source"] == "project" and isinstance(rev, int): project_nodes[rev] = nid
        if e["source"] == "environment" and isinstance(rev, int): env_nodes[rev] = nid
        if e["source"] == "asset" and isinstance(rev, int): asset_nodes[(e.get("metadata",{}).get("assetKey"), rev)] = nid
        if e["source"] == "execution" and isinstance(rev, int): job_nodes[(e.get("metadata",{}).get("jobId"), rev)] = nid
    for e in timeline["events"]:
        nid = e["eventId"]; rev = e.get("revision"); lin = e.get("lineage") or {}
        if e["source"] == "project" and isinstance(rev, int) and rev > 1 and rev-1 in project_nodes:
            edges.append({"from": project_nodes[rev-1], "to": nid, "relation": "project-revision-parent"})
        elif e["source"] == "environment" and lin.get("parentRevision") in env_nodes:
            edges.append({"from": env_nodes[lin["parentRevision"]], "to": nid, "relation": "environment-revision-parent"})
            src = lin.get("recoveredFrom") or {}
            if isinstance(src, dict) and src.get("revision") in env_nodes:
                edges.append({"from": env_nodes[src["revision"]], "to": nid, "relation": "recovery-source"})
        elif e["source"] == "checkpoint" and lin.get("checkpointOfRevision") in env_nodes:
            edges.append({"from": env_nodes[lin["checkpointOfRevision"]], "to": nid, "relation": "checkpoint-of"})
        elif e["source"] == "asset" and isinstance(rev, int):
            key=e.get("metadata",{}).get("assetKey"); parent=lin.get("parentAssetRevision")
            if (key,parent) in asset_nodes: edges.append({"from": asset_nodes[(key,parent)], "to": nid, "relation": "asset-revision-parent"})
            er=lin.get("environmentRevision")
            if er in env_nodes: edges.append({"from": env_nodes[er], "to": nid, "relation": "derived-from-environment-revision"})
        elif e["source"] == "execution" and isinstance(rev, int):
            jid=e.get("metadata",{}).get("jobId"); parent=lin.get("previousJobRevision")
            if (jid,parent) in job_nodes: edges.append({"from": job_nodes[(jid,parent)], "to": nid, "relation": "job-transition"})
            er=lin.get("environmentRevision")
            if er in env_nodes and rev == 1: edges.append({"from": env_nodes[er], "to": nid, "relation": "executed-against-environment-revision"})
    out = {"ok": True, "schema": LINEAGE_SCHEMA, "version": VERSION, "projectKey": project_key, "nodeCount": len(nodes), "edgeCount": len(edges), "nodes": nodes, "edges": edges, "automaticCausalInferencePerformed": False, "automaticScientificInterpretationPerformed": False}
    out["lineageHash"] = content_hash(out)
    return out


class TimelineCompareRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    leftEventId: str = Field(min_length=1, max_length=160)
    rightEventId: str = Field(min_length=1, max_length=160)


class CoreTimelinePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    eventIds: List[str] = Field(default_factory=list, max_length=MAX_CORE_EVENTS)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def compare_events(req: TimelineCompareRequest) -> Dict[str, Any]:
    timeline = collect_timeline(req.projectKey)
    by_id = {e["eventId"]: e for e in timeline["events"]}
    if req.leftEventId not in by_id or req.rightEventId not in by_id:
        raise FileNotFoundError("one or both timeline event IDs were not found")
    left, right = by_id[req.leftEventId], by_id[req.rightEventId]
    fields = ["source", "eventType", "at", "status", "revision", "hashes", "metadata", "lineage"]
    changes = {field: {"left": left.get(field), "right": right.get(field)} for field in fields if left.get(field) != right.get(field)}
    out = {"ok": True, "schema": COMPARE_SCHEMA, "version": VERSION, "projectKey": req.projectKey, "leftEvent": left, "rightEvent": right, "changedFieldCount": len(changes), "changes": changes, "automaticWinnerSelected": False, "automaticScientificInterpretationPerformed": False, "automaticCausalInferencePerformed": False}
    out["comparisonHash"] = content_hash(out)
    return out


def core_timeline_plan(req: CoreTimelinePlanRequest) -> Dict[str, Any]:
    project = load_project(req.projectKey); ws = project["workspace"]
    sid = _safe(req.coreSessionId or ws.get("coreSessionId"), 255)
    base = core_project_plan(ProjectCorePlanRequest(projectKey=req.projectKey, coreProjectEntityId=req.coreProjectEntityId or req.projectKey, coreSessionId=sid, visibility=req.visibility, createdBy=req.createdBy))
    timeline = collect_timeline(req.projectKey)
    by_id = {e["eventId"]: e for e in timeline["events"]}
    ids = req.eventIds or [e["eventId"] for e in timeline["events"][-MAX_CORE_EVENTS:]]
    selected = []
    for eid in ids[:MAX_CORE_EVENTS]:
        if eid not in by_id: raise FileNotFoundError(f"timeline event {eid} not found")
        selected.append(by_id[eid])
    out: Dict[str, Any] = {"ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION, "projectKey": req.projectKey, "projectRevision": project.get("projectRevision"), "phase": base.get("phase"), "coreSessionId": sid or None, "coreSessionIdMustComeFromCore": True, "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT, "projectPlan": base, "eventCount": len(selected), "events": [{"eventId": e["eventId"], "eventHash": e["eventHash"], "source": e["source"], "eventType": e["eventType"]} for e in selected], "coreRequests": list(base.get("coreRequests") or []), "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False, "coreExecutesWorkbenchComputation": False}
    if sid:
        for e in selected:
            out["coreRequests"].append({"path": CORE_PATHS["objectBindings"], "method": "POST", "phase": "research-timeline-event-bind", "data": {"session_id": sid, "object_type": "workbench.research-timeline-event", "object_ref": e.get("sourceRef") or f"sc://workbench/research-timeline/{req.projectKey}/{e['eventId']}", "version_ref": f"sc://workbench/research-timeline/{req.projectKey}/{e['eventId']}@{e['eventHash'][:16]}", "content_hash": e["eventHash"], "role": "research-timeline-event", "visibility": req.visibility, "metadata": {"workbenchVersion": VERSION, "projectKey": req.projectKey, "eventId": e["eventId"], "source": e["source"], "eventType": e["eventType"], "at": e.get("at")}}, "dispatchPerformed": False})
    out["planHash"] = content_hash(out)
    return out


def manifest() -> Dict[str, Any]:
    out = {"ok": True, "schema": SCHEMA, "version": VERSION, "release": "Research Timeline & Run History", "sources": ["project", "environment", "checkpoint", "asset", "execution"], "capabilities": {"derivedProjectTimeline": True, "executionRunHistory": True, "revisionLineageGraph": True, "neutralTimelineComparison": True, "explicitTimestampProvenance": True, "coreTimelineEventPlanning": True}, "authorities": {"projectActivity": "v8.2", "environmentHistory": "v8.1", "assetHistory": "v8.3", "executionHistory": "v8.4"}, "boundaries": {"timelineIsCompetingSourceOfTruth": False, "filesystemMtimeUsedAsAuthoritativeChronology": False, "automaticScientificExecutionAuthorized": False, "automaticCausalInferenceAuthorized": False, "automaticWinnerSelectionAuthorized": False, "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False}}
    out["manifestHash"] = content_hash(out)
    return out


@router.get("/research-timeline/manifest")
def manifest_route(): return manifest()

@router.get("/research-timeline/{project_key}/runs")
def runs_route(project_key: str, limit: int = Query(default=200, ge=1, le=MAX_RUNS)):
    try: return run_history(project_key, limit)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/research-timeline/{project_key}/lineage")
def lineage_route(project_key: str):
    try: return lineage_graph(project_key)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/research-timeline/{project_key}")
def timeline_route(project_key: str, source: str = Query(default=""), event_type: str = Query(default=""), q: str = Query(default=""), limit: int = Query(default=500, ge=1, le=MAX_EVENTS)):
    try: return filtered_timeline(project_key, source, event_type, q, limit)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/research-timeline/compare")
def compare_route(req: TimelineCompareRequest):
    try: return compare_events(req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/integration/core/research-timeline/plan")
def core_plan_route(req: CoreTimelinePlanRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    try: return core_timeline_plan(req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/v850/status")
def status_route():
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "release": "Research Timeline & Run History", "derivedTimeline": True, "runHistory": True, "lineageGraph": True, "neutralComparison": True, "timelineIsSourceOfTruth": False, "automaticScientificExecution": False, "automaticCoreDispatch": False}

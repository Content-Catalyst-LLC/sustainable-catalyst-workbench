"""Workbench v8.6.0 — Visual Research Canvas.

A project-scoped visual composition layer over authoritative Workbench v8 research
objects. The canvas projects projects, active environments, research assets, execution
jobs, and timeline events as linked visual nodes. Only view state (positions, visibility,
viewport, layers) and explicit researcher-authored visual links are persisted. Scientific
payloads, execution results, provenance records, project/environment state, and timeline
history remain owned by their authoritative subsystems.

The canvas performs no scientific execution, causal inference, evidence grading, winner
selection, or automatic Platform Core dispatch. Platform Core integration is emitted as
an explicit two-phase plan.
"""
from __future__ import annotations

import fcntl
import hashlib
from contextlib import contextmanager
from copy import deepcopy
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
from .v830 import search_assets
from .v840 import list_jobs
from .v850 import collect_timeline, lineage_graph

VERSION = APP_VERSION
SCHEMA = "sc-workbench-visual-research-canvas/1.0"
CANVAS_SCHEMA = "sc-workbench-visual-research-canvas-projection/1.0"
LAYOUT_SCHEMA = "sc-workbench-visual-research-canvas-layout/1.0"
SELECTION_SCHEMA = "sc-workbench-visual-research-canvas-selection/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-visual-research-canvas-core-plan/1.0"
MAX_NODES = 1000
MAX_LINKS = 2000
MAX_TIMELINE_NODES = 250
MAX_CORE_NODES = 100

router = APIRouter(tags=["workbench-v860-visual-research-canvas"])

NodeKind = Literal["project", "environment", "asset", "execution", "timeline"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _project_id(project_key: str) -> str:
    return hashlib.sha256(project_key.encode("utf-8")).hexdigest()


def _canvas_dir(project_key: str) -> Path:
    return _store_root() / "visual-research-canvas" / _project_id(project_key)


def _layout_path(project_key: str) -> Path:
    return _canvas_dir(project_key) / "layout.json"


@contextmanager
def _canvas_lock(project_key: str):
    path = _store_root() / "locks" / f"visual-canvas-{_project_id(project_key)}.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _layout_hash(record: Dict[str, Any]) -> str:
    candidate = deepcopy(record)
    candidate.pop("layoutHash", None)
    return content_hash(candidate)


def _node_id(kind: str, source_ref: str, source_hash: str = "") -> str:
    return "vrc-" + content_hash({"kind": kind, "sourceRef": source_ref, "sourceHash": source_hash})[:28]


def _node(*, kind: NodeKind, title: str, source_ref: str, source_hash: str,
          authority: str, x: float, y: float, width: float = 240, height: float = 112,
          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "nodeId": _node_id(kind, source_ref, source_hash),
        "kind": kind,
        "title": _safe(title, 500),
        "sourceRef": _safe(source_ref, 1200),
        "sourceHash": _safe(source_hash, 256) or None,
        "sourceAuthority": _safe(authority, 120),
        "x": float(x), "y": float(y), "width": float(width), "height": float(height),
        "hidden": False, "pinned": False,
        "metadata": deepcopy(metadata or {}),
    }


def _edge(source: str, target: str, relation: str, *, kind: str = "derived", label: str = "") -> Dict[str, Any]:
    eid = "vrc-edge-" + content_hash({"source": source, "target": target, "relation": relation, "kind": kind, "label": label})[:24]
    return {"edgeId": eid, "from": source, "to": target, "relation": _safe(relation, 160), "kind": kind, "label": _safe(label, 240) or None}


def _load_layout(project_key: str) -> Dict[str, Any]:
    path = _layout_path(project_key)
    if not path.exists():
        return {
            "ok": True, "schema": LAYOUT_SCHEMA, "version": VERSION, "projectKey": project_key,
            "layoutRevision": 0, "layoutHash": None, "savedAt": None, "actor": None, "reason": None,
            "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0},
            "layers": {"timeline": True, "lineage": True, "assets": True, "executions": True},
            "nodes": [], "links": [],
        }
    record = _json_read(path)
    if record.get("schema") != LAYOUT_SCHEMA or record.get("projectKey") != project_key or record.get("layoutHash") != _layout_hash(record):
        raise ValueError("stored visual research canvas layout failed integrity validation")
    return record


class CanvasNodeLayout(BaseModel):
    nodeId: str = Field(min_length=1, max_length=160)
    x: float = Field(ge=-100000, le=100000)
    y: float = Field(ge=-100000, le=100000)
    width: float = Field(default=240, ge=80, le=1600)
    height: float = Field(default=112, ge=48, le=1200)
    hidden: bool = False
    pinned: bool = False


class CanvasLink(BaseModel):
    linkId: str = Field(default="", max_length=160)
    fromNodeId: str = Field(min_length=1, max_length=160)
    toNodeId: str = Field(min_length=1, max_length=160)
    relation: str = Field(default="researcher-link", min_length=1, max_length=160)
    label: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def distinct_nodes(self):
        if self.fromNodeId == self.toNodeId:
            raise ValueError("visual research canvas links must connect two different nodes")
        return self


class CanvasLayoutSaveRequest(BaseModel):
    expectedLayoutRevision: Optional[int] = Field(default=None, ge=0)
    nodes: List[CanvasNodeLayout] = Field(default_factory=list, max_length=MAX_NODES)
    links: List[CanvasLink] = Field(default_factory=list, max_length=MAX_LINKS)
    viewport: Dict[str, Any] = Field(default_factory=dict)
    layers: Dict[str, bool] = Field(default_factory=dict)
    actor: str = Field(default="workbench", min_length=1, max_length=160)
    reason: str = Field(default="canvas-layout-save", min_length=1, max_length=500)


class CanvasSelectionRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    nodeIds: List[str] = Field(default_factory=list, max_length=MAX_CORE_NODES)


class CoreCanvasPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    nodeIds: List[str] = Field(default_factory=list, max_length=MAX_CORE_NODES)
    includeLayout: bool = True
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def _project_environment_nodes(project_key: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    record = load_project(project_key)
    ws = record["workspace"]
    project_ref = ws.get("workspaceRef") or f"sc://workbench/research-project/{project_key}"
    p = _node(kind="project", title=ws.get("title") or project_key, source_ref=project_ref,
              source_hash=ws.get("workspaceHash") or "", authority="v8.2-project-workspace", x=0, y=0,
              width=300, height=132,
              metadata={"projectKey": project_key, "projectRevision": record.get("projectRevision"), "status": ws.get("status")})
    env = ws.get("researchEnvironment") or {}
    env_key = ws.get("activeEnvironmentKey") or env.get("environmentKey") or ""
    env_ref = env.get("environmentRef") or f"sc://workbench/research-environment/{env_key}"
    e = _node(kind="environment", title=env.get("title") or env_key or "Active research environment",
              source_ref=env_ref, source_hash=ws.get("activeEnvironmentHash") or env.get("environmentHash") or "",
              authority="v8.1-research-environment", x=380, y=0, width=300, height=132,
              metadata={"environmentKey": env_key, "environmentRevision": ws.get("activeEnvironmentRevision")})
    return [p, e], [_edge(p["nodeId"], e["nodeId"], "active-environment")]


def build_canvas_projection(project_key: str, *, include_timeline: bool = True, timeline_limit: int = 80) -> Dict[str, Any]:
    nodes, edges = _project_environment_nodes(project_key)
    project_node, environment_node = nodes[0], nodes[1]

    assets = search_assets(project_key, limit=300).get("results") or []
    for idx, asset in enumerate(assets):
        col, row = idx % 3, idx // 3
        ref = asset.get("assetRef") or f"sc://workbench/research-asset/{project_key}/{asset.get('assetKey')}"
        h = asset.get("assetHash") or asset.get("contentHash") or ""
        n = _node(kind="asset", title=asset.get("title") or asset.get("assetKey") or "Research asset",
                  source_ref=ref, source_hash=h, authority="v8.3-asset-registry",
                  x=col * 280, y=220 + row * 150,
                  metadata={"assetKey": asset.get("assetKey"), "assetType": asset.get("assetType"), "assetRevision": asset.get("assetRevision"), "origin": asset.get("origin"), "tags": asset.get("tags") or []})
        nodes.append(n); edges.append(_edge(project_node["nodeId"], n["nodeId"], "project-asset"))
        if asset.get("environmentRevision"):
            edges.append(_edge(environment_node["nodeId"], n["nodeId"], "registered-from-environment"))

    jobs = list_jobs(project_key=project_key).get("jobs") or []
    for idx, job in enumerate(jobs):
        ref = f"sc://workbench/execution-console/job/{job.get('jobId')}"
        h = job.get("resultHash") or job.get("requestHash") or ""
        n = _node(kind="execution", title=job.get("label") or f"{job.get('runtimeKind') or 'execution'} · {job.get('status') or ''}",
                  source_ref=ref, source_hash=h, authority="v8.4-execution-console",
                  x=900 + (idx % 2) * 280, y=220 + (idx // 2) * 150,
                  metadata={"jobId": job.get("jobId"), "runtimeKind": job.get("runtimeKind"), "status": job.get("status"), "jobRevision": job.get("jobRevision"), "resultHash": job.get("resultHash")})
        nodes.append(n); edges.append(_edge(project_node["nodeId"], n["nodeId"], "project-execution"))

    timeline_node_map: Dict[str, str] = {}
    if include_timeline:
        timeline = collect_timeline(project_key)
        selected = (timeline.get("events") or [])[-max(1, min(int(timeline_limit), MAX_TIMELINE_NODES)):]
        for idx, event in enumerate(selected):
            ref = event.get("sourceRef") or f"sc://workbench/research-timeline/{project_key}/{event.get('eventId')}"
            n = _node(kind="timeline", title=event.get("title") or event.get("eventType") or "Timeline event",
                      source_ref=ref, source_hash=event.get("eventHash") or "", authority="v8.5-research-timeline",
                      x=1480 + (idx % 2) * 280, y=100 + (idx // 2) * 132, width=250, height=96,
                      metadata={"eventId": event.get("eventId"), "source": event.get("source"), "eventType": event.get("eventType"), "at": event.get("at"), "revision": event.get("revision"), "chronologyAuthoritative": event.get("chronologyAuthoritative")})
            nodes.append(n); timeline_node_map[event.get("eventId")] = n["nodeId"]
        lineage = lineage_graph(project_key)
        for le in lineage.get("edges") or []:
            a, b = timeline_node_map.get(le.get("from")), timeline_node_map.get(le.get("to"))
            if a and b: edges.append(_edge(a, b, le.get("relation") or "timeline-lineage", kind="lineage"))

    layout = _load_layout(project_key)
    positions = {x.get("nodeId"): x for x in layout.get("nodes") or []}
    live_ids = {n["nodeId"] for n in nodes}
    for n in nodes:
        pos = positions.get(n["nodeId"])
        if pos:
            for key in ("x", "y", "width", "height", "hidden", "pinned"):
                if key in pos: n[key] = pos[key]
    for link in layout.get("links") or []:
        if link.get("fromNodeId") in live_ids and link.get("toNodeId") in live_ids:
            edges.append(_edge(link["fromNodeId"], link["toNodeId"], link.get("relation") or "researcher-link", kind="researcher", label=link.get("label") or ""))

    out = {
        "ok": True, "schema": CANVAS_SCHEMA, "version": VERSION, "projectKey": project_key,
        "nodeCount": len(nodes), "edgeCount": len(edges), "nodes": nodes[:MAX_NODES], "edges": edges[:MAX_LINKS],
        "layoutRevision": layout.get("layoutRevision", 0), "layoutHash": layout.get("layoutHash"),
        "viewport": layout.get("viewport") or {"x": 0.0, "y": 0.0, "zoom": 1.0},
        "layers": layout.get("layers") or {"timeline": True, "lineage": True, "assets": True, "executions": True},
        "orphanLayoutNodeIds": sorted(set(positions) - live_ids),
        "derivedFromAuthoritativeStores": True,
        "canvasIsScientificSourceOfTruth": False,
        "layoutPersistsScientificPayloads": False,
        "automaticScientificInterpretationPerformed": False,
        "automaticCausalInferencePerformed": False,
    }
    out["canvasHash"] = content_hash(out)
    return out


def save_layout(project_key: str, req: CanvasLayoutSaveRequest) -> Dict[str, Any]:
    projection = build_canvas_projection(project_key, include_timeline=True, timeline_limit=MAX_TIMELINE_NODES)
    live_ids = {n["nodeId"] for n in projection["nodes"]}
    supplied_ids = [n.nodeId for n in req.nodes]
    if len(supplied_ids) != len(set(supplied_ids)):
        raise ValueError("duplicate nodeId in canvas layout")
    unknown = sorted(set(supplied_ids) - live_ids)
    if unknown:
        raise ValueError(f"canvas layout contains unknown node IDs: {', '.join(unknown[:10])}")
    for link in req.links:
        if link.fromNodeId not in live_ids or link.toNodeId not in live_ids:
            raise ValueError("canvas link references an unknown node")
    with _canvas_lock(project_key):
        current = _load_layout(project_key)
        current_rev = int(current.get("layoutRevision") or 0)
        if req.expectedLayoutRevision is not None and req.expectedLayoutRevision != current_rev:
            raise RuntimeError(f"layout revision conflict: expected {req.expectedLayoutRevision}, current {current_rev}")
        revision = current_rev + 1
        links = []
        for link in req.links:
            lid = link.linkId or ("vrc-user-" + content_hash({"from": link.fromNodeId, "to": link.toNodeId, "relation": link.relation, "label": link.label})[:24])
            links.append({"linkId": lid, "fromNodeId": link.fromNodeId, "toNodeId": link.toNodeId, "relation": link.relation, "label": link.label})
        viewport = {"x": float(req.viewport.get("x", 0.0)), "y": float(req.viewport.get("y", 0.0)), "zoom": max(0.1, min(8.0, float(req.viewport.get("zoom", 1.0))))}
        layers = {"timeline": bool(req.layers.get("timeline", True)), "lineage": bool(req.layers.get("lineage", True)), "assets": bool(req.layers.get("assets", True)), "executions": bool(req.layers.get("executions", True))}
        record = {
            "ok": True, "schema": LAYOUT_SCHEMA, "version": VERSION, "projectKey": project_key,
            "layoutRevision": revision, "savedAt": _now(), "actor": _safe(req.actor, 160), "reason": _safe(req.reason, 500),
            "viewport": viewport, "layers": layers,
            "nodes": [x.model_dump() for x in req.nodes], "links": links,
            "scientificPayloadsPersisted": False, "scientificResultsRewritten": False,
            "automaticScientificInterpretationPerformed": False,
        }
        record["layoutHash"] = _layout_hash(record)
        _canvas_dir(project_key).mkdir(parents=True, exist_ok=True)
        _atomic_json_write(_layout_path(project_key), record)
        return record


def resolve_selection(req: CanvasSelectionRequest) -> Dict[str, Any]:
    canvas = build_canvas_projection(req.projectKey, include_timeline=True, timeline_limit=MAX_TIMELINE_NODES)
    by_id = {n["nodeId"]: n for n in canvas["nodes"]}
    selected = []
    for nid in req.nodeIds:
        if nid not in by_id: raise FileNotFoundError(f"visual research canvas node {nid} not found")
        selected.append(by_id[nid])
    out = {"ok": True, "schema": SELECTION_SCHEMA, "version": VERSION, "projectKey": req.projectKey, "selectionCount": len(selected), "nodes": selected,
           "selectionIsViewStateOnly": True, "automaticScientificInterpretationPerformed": False, "automaticWinnerSelected": False}
    out["selectionHash"] = content_hash(out)
    return out


def core_canvas_plan(req: CoreCanvasPlanRequest) -> Dict[str, Any]:
    project = load_project(req.projectKey); ws = project["workspace"]
    sid = _safe(req.coreSessionId or ws.get("coreSessionId"), 255)
    base = core_project_plan(ProjectCorePlanRequest(projectKey=req.projectKey, coreProjectEntityId=req.coreProjectEntityId or req.projectKey, coreSessionId=sid, visibility=req.visibility, createdBy=req.createdBy))
    canvas = build_canvas_projection(req.projectKey, include_timeline=True, timeline_limit=MAX_TIMELINE_NODES)
    by_id = {n["nodeId"]: n for n in canvas["nodes"]}
    ids = req.nodeIds or [n["nodeId"] for n in canvas["nodes"][:MAX_CORE_NODES]]
    selected = []
    for nid in ids[:MAX_CORE_NODES]:
        if nid not in by_id: raise FileNotFoundError(f"visual research canvas node {nid} not found")
        n = by_id[nid]
        selected.append({"nodeId": nid, "kind": n.get("kind"), "sourceRef": n.get("sourceRef"), "sourceHash": n.get("sourceHash"), "sourceAuthority": n.get("sourceAuthority")})
    out: Dict[str, Any] = {"ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION, "projectKey": req.projectKey,
        "phase": base.get("phase"), "coreSessionId": sid or None, "coreSessionIdMustComeFromCore": True,
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT, "projectPlan": base,
        "nodeCount": len(selected), "nodes": selected, "layoutRevision": canvas.get("layoutRevision"), "layoutHash": canvas.get("layoutHash"),
        "coreRequests": list(base.get("coreRequests") or []), "canvasBindingIsViewCompositionOnly": True,
        "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False,
        "coreExecutesWorkbenchComputation": False, "automaticScientificInterpretationAuthorized": False}
    if sid and req.includeLayout and canvas.get("layoutHash"):
        out["coreRequests"].append({"path": CORE_PATHS["objectBindings"], "method": "POST", "phase": "visual-research-canvas-layout-bind", "data": {
            "session_id": sid, "object_type": "workbench.visual-research-canvas-layout",
            "object_ref": f"sc://workbench/visual-research-canvas/{req.projectKey}/layout",
            "version_ref": f"sc://workbench/visual-research-canvas/{req.projectKey}/layout@{canvas['layoutRevision']}",
            "content_hash": canvas["layoutHash"], "role": "view-composition", "visibility": req.visibility,
            "metadata": {"workbenchVersion": VERSION, "projectKey": req.projectKey, "layoutRevision": canvas.get("layoutRevision"), "scientificSourceOfTruth": False}}, "dispatchPerformed": False})
    out["planHash"] = content_hash(out)
    return out


def manifest() -> Dict[str, Any]:
    out = {"ok": True, "schema": SCHEMA, "version": VERSION, "release": "Visual Research Canvas",
           "capabilities": {"projectVisualCanvas": True, "authoritativeObjectProjection": True, "persistentLayout": True, "dragPositionState": True, "researcherAuthoredLinks": True, "timelineLayer": True, "lineageOverlay": True, "linkedSelection": True, "coreCanvasPlanning": True},
           "authorities": {"project": "v8.2", "environment": "v8.1", "assets": "v8.3", "executions": "v8.4", "timelineAndLineage": "v8.5", "layout": "v8.6-view-state-only"},
           "boundaries": {"canvasIsScientificSourceOfTruth": False, "scientificPayloadsDuplicated": False, "scientificResultsRewritten": False, "automaticScientificExecutionAuthorized": False, "automaticScientificInterpretationAuthorized": False, "automaticCausalInferenceAuthorized": False, "automaticWinnerSelectionAuthorized": False, "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False}}
    out["manifestHash"] = content_hash(out)
    return out


@router.get("/research-canvas/manifest")
def manifest_route(): return manifest()


@router.get("/research-canvas/{project_key}/layout")
def layout_route(project_key: str):
    try:
        load_project(project_key); return _load_layout(project_key)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/research-canvas/{project_key}/layout/save")
def save_layout_route(project_key: str, req: CanvasLayoutSaveRequest):
    try: return save_layout(project_key, req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/research-canvas/{project_key}/lineage-overlay")
def lineage_overlay_route(project_key: str):
    try:
        graph = lineage_graph(project_key)
        return {"ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key, "nodeCount": graph.get("nodeCount"), "edgeCount": graph.get("edgeCount"), "nodes": graph.get("nodes") or [], "edges": graph.get("edges") or [], "automaticCausalInferencePerformed": False, "automaticScientificInterpretationPerformed": False}
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/research-canvas/{project_key}")
def canvas_route(project_key: str, include_timeline: bool = Query(default=True), timeline_limit: int = Query(default=80, ge=1, le=MAX_TIMELINE_NODES)):
    try: return build_canvas_projection(project_key, include_timeline=include_timeline, timeline_limit=timeline_limit)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/research-canvas/selection/resolve")
def selection_route(req: CanvasSelectionRequest):
    try: return resolve_selection(req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/research-canvas/plan")
def core_plan_route(req: CoreCanvasPlanRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    try: return core_canvas_plan(req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/v860/status")
def status_route():
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "release": "Visual Research Canvas", "visualCanvas": True, "persistentLayout": True, "lineageOverlay": True, "linkedSelection": True, "canvasIsScientificSourceOfTruth": False, "automaticScientificExecution": False, "automaticCoreDispatch": False}

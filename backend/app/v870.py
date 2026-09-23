"""Workbench v8.7.0 — Linked Scientific Views & Cross-Filtering.

Creates deterministic, project-scoped linked view projections over the v8.6 visual
research canvas. Filters and selections are declarative view state only: they do not
rewrite project, environment, asset, execution, timeline, lineage, or scientific result
records. Cross-filtering is neutral and does not infer scientific validity, causality,
preference, or a winning result.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v660 import CORE_PATHS, CORE_UNIFIED_RUNTIME_CONTRACT
from .v820 import ProjectCorePlanRequest, core_project_plan, load_project
from .v860 import MAX_CORE_NODES, MAX_TIMELINE_NODES, build_canvas_projection

VERSION = APP_VERSION
SCHEMA = "sc-workbench-linked-scientific-views/1.0"
QUERY_SCHEMA = "sc-workbench-linked-scientific-views-query/1.0"
SELECTION_SCHEMA = "sc-workbench-linked-scientific-views-selection/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-linked-scientific-views-core-plan/1.0"
MAX_FILTER_VALUES = 100
MAX_RETURNED_NODES = 1000
MAX_RETURNED_EDGES = 2000
MAX_TEXT = 500

router = APIRouter(tags=["workbench-v870-linked-scientific-views"])

ViewKey = Literal["canvas", "assets", "executions", "timeline", "lineage", "facets"]
NodeKind = Literal["project", "environment", "asset", "execution", "timeline"]


def _clean(values: List[str]) -> List[str]:
    return sorted({str(v).strip() for v in values if str(v).strip()})[:MAX_FILTER_VALUES]


def _text(value: Any) -> str:
    return str(value or "").strip().lower()


def _iso(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _facet(nodes: List[Dict[str, Any]], getter) -> List[Dict[str, Any]]:
    counts: Counter[str] = Counter()
    for node in nodes:
        values = getter(node)
        if not isinstance(values, list):
            values = [values]
        for value in values:
            s = str(value or "").strip()
            if s:
                counts[s] += 1
    return [{"value": key, "count": counts[key]} for key in sorted(counts)]


class CrossFilterSpec(BaseModel):
    kinds: List[NodeKind] = Field(default_factory=list, max_length=MAX_FILTER_VALUES)
    authorities: List[str] = Field(default_factory=list, max_length=MAX_FILTER_VALUES)
    assetTypes: List[str] = Field(default_factory=list, max_length=MAX_FILTER_VALUES)
    assetOrigins: List[str] = Field(default_factory=list, max_length=MAX_FILTER_VALUES)
    tags: List[str] = Field(default_factory=list, max_length=MAX_FILTER_VALUES)
    runtimeKinds: List[str] = Field(default_factory=list, max_length=MAX_FILTER_VALUES)
    executionStatuses: List[str] = Field(default_factory=list, max_length=MAX_FILTER_VALUES)
    eventTypes: List[str] = Field(default_factory=list, max_length=MAX_FILTER_VALUES)
    text: str = Field(default="", max_length=MAX_TEXT)
    timelineStart: str = Field(default="", max_length=80)
    timelineEnd: str = Field(default="", max_length=80)
    nodeIds: List[str] = Field(default_factory=list, max_length=MAX_RETURNED_NODES)
    includeNeighbors: bool = False
    includeHidden: bool = False

    @model_validator(mode="after")
    def validate_range(self):
        start, end = _iso(self.timelineStart), _iso(self.timelineEnd)
        if self.timelineStart and start is None:
            raise ValueError("timelineStart must be an ISO-8601 timestamp")
        if self.timelineEnd and end is None:
            raise ValueError("timelineEnd must be an ISO-8601 timestamp")
        if start and end and start > end:
            raise ValueError("timelineStart must be less than or equal to timelineEnd")
        return self


class LinkedViewsQueryRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    filters: CrossFilterSpec = Field(default_factory=CrossFilterSpec)
    selectedNodeIds: List[str] = Field(default_factory=list, max_length=MAX_CORE_NODES)
    sourceView: ViewKey = "canvas"
    timelineLimit: int = Field(default=120, ge=1, le=MAX_TIMELINE_NODES)


class LinkedSelectionRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    selectedNodeIds: List[str] = Field(default_factory=list, max_length=MAX_CORE_NODES)
    sourceView: ViewKey = "canvas"
    filters: CrossFilterSpec = Field(default_factory=CrossFilterSpec)
    timelineLimit: int = Field(default=120, ge=1, le=MAX_TIMELINE_NODES)


class CoreLinkedViewsPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    filters: CrossFilterSpec = Field(default_factory=CrossFilterSpec)
    selectedNodeIds: List[str] = Field(default_factory=list, max_length=MAX_CORE_NODES)
    sourceView: ViewKey = "canvas"
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def _matches(node: Dict[str, Any], spec: CrossFilterSpec) -> bool:
    meta = node.get("metadata") or {}
    if not spec.includeHidden and node.get("hidden"):
        return False
    if spec.kinds and node.get("kind") not in set(spec.kinds):
        return False
    if spec.authorities and node.get("sourceAuthority") not in set(_clean(spec.authorities)):
        return False
    if spec.nodeIds and node.get("nodeId") not in set(spec.nodeIds):
        return False
    if spec.assetTypes and node.get("kind") == "asset" and str(meta.get("assetType") or "") not in set(_clean(spec.assetTypes)):
        return False
    if spec.assetTypes and node.get("kind") != "asset":
        return False
    if spec.assetOrigins and node.get("kind") == "asset" and str(meta.get("origin") or "") not in set(_clean(spec.assetOrigins)):
        return False
    if spec.assetOrigins and node.get("kind") != "asset":
        return False
    if spec.tags:
        tags = {str(t) for t in (meta.get("tags") or [])}
        if not tags.intersection(set(_clean(spec.tags))):
            return False
    if spec.runtimeKinds and node.get("kind") == "execution" and str(meta.get("runtimeKind") or "") not in set(_clean(spec.runtimeKinds)):
        return False
    if spec.runtimeKinds and node.get("kind") != "execution":
        return False
    if spec.executionStatuses and node.get("kind") == "execution" and str(meta.get("status") or "") not in set(_clean(spec.executionStatuses)):
        return False
    if spec.executionStatuses and node.get("kind") != "execution":
        return False
    if spec.eventTypes and node.get("kind") == "timeline" and str(meta.get("eventType") or "") not in set(_clean(spec.eventTypes)):
        return False
    if spec.eventTypes and node.get("kind") != "timeline":
        return False
    if spec.timelineStart or spec.timelineEnd:
        if node.get("kind") != "timeline":
            return False
        at = _iso(meta.get("at"))
        if at is None:
            return False
        start, end = _iso(spec.timelineStart), _iso(spec.timelineEnd)
        if start and at < start:
            return False
        if end and at > end:
            return False
    q = _text(spec.text)
    if q:
        hay = " ".join([
            _text(node.get("title")), _text(node.get("sourceRef")), _text(node.get("sourceAuthority")),
            _text(meta.get("assetKey")), _text(meta.get("assetType")), _text(meta.get("origin")),
            _text(meta.get("jobId")), _text(meta.get("runtimeKind")), _text(meta.get("status")),
            _text(meta.get("eventId")), _text(meta.get("eventType")), " ".join(_text(t) for t in (meta.get("tags") or [])),
        ])
        if q not in hay:
            return False
    return True


def _rows(nodes: List[Dict[str, Any]], kind: str) -> List[Dict[str, Any]]:
    out = []
    for n in nodes:
        if n.get("kind") != kind:
            continue
        m = n.get("metadata") or {}
        base = {"nodeId": n.get("nodeId"), "title": n.get("title"), "sourceRef": n.get("sourceRef"), "sourceHash": n.get("sourceHash"), "sourceAuthority": n.get("sourceAuthority")}
        if kind == "asset":
            base.update({"assetKey": m.get("assetKey"), "assetType": m.get("assetType"), "assetRevision": m.get("assetRevision"), "origin": m.get("origin"), "tags": m.get("tags") or []})
        elif kind == "execution":
            base.update({"jobId": m.get("jobId"), "runtimeKind": m.get("runtimeKind"), "status": m.get("status"), "jobRevision": m.get("jobRevision"), "resultHash": m.get("resultHash")})
        elif kind == "timeline":
            base.update({"eventId": m.get("eventId"), "source": m.get("source"), "eventType": m.get("eventType"), "at": m.get("at"), "revision": m.get("revision"), "chronologyAuthoritative": m.get("chronologyAuthoritative")})
        out.append(base)
    return out


def linked_views_query(req: LinkedViewsQueryRequest) -> Dict[str, Any]:
    canvas = build_canvas_projection(req.projectKey, include_timeline=True, timeline_limit=req.timelineLimit)
    all_nodes = canvas.get("nodes") or []
    all_edges = canvas.get("edges") or []
    by_id = {n.get("nodeId"): n for n in all_nodes}
    selected = _clean(req.selectedNodeIds)
    unknown = [nid for nid in selected if nid not in by_id]
    if unknown:
        raise FileNotFoundError(f"linked-view node {unknown[0]} not found")

    matched_ids = {n.get("nodeId") for n in all_nodes if _matches(n, req.filters)}
    if req.filters.includeNeighbors and matched_ids:
        neighbors = set(matched_ids)
        for e in all_edges:
            a, b = e.get("from"), e.get("to")
            if a in matched_ids or b in matched_ids:
                neighbors.update([a, b])
        matched_ids = {nid for nid in neighbors if nid in by_id}
    filtered_nodes = [deepcopy(n) for n in all_nodes if n.get("nodeId") in matched_ids][:MAX_RETURNED_NODES]
    filtered_ids = {n.get("nodeId") for n in filtered_nodes}
    filtered_edges = [deepcopy(e) for e in all_edges if e.get("from") in filtered_ids and e.get("to") in filtered_ids][:MAX_RETURNED_EDGES]

    selected_visible = [nid for nid in selected if nid in filtered_ids]
    selected_hidden = [nid for nid in selected if nid not in filtered_ids]

    facets = {
        "kind": _facet(filtered_nodes, lambda n: n.get("kind")),
        "authority": _facet(filtered_nodes, lambda n: n.get("sourceAuthority")),
        "assetType": _facet(filtered_nodes, lambda n: (n.get("metadata") or {}).get("assetType") if n.get("kind") == "asset" else None),
        "assetOrigin": _facet(filtered_nodes, lambda n: (n.get("metadata") or {}).get("origin") if n.get("kind") == "asset" else None),
        "tag": _facet(filtered_nodes, lambda n: (n.get("metadata") or {}).get("tags") if n.get("kind") == "asset" else []),
        "runtimeKind": _facet(filtered_nodes, lambda n: (n.get("metadata") or {}).get("runtimeKind") if n.get("kind") == "execution" else None),
        "executionStatus": _facet(filtered_nodes, lambda n: (n.get("metadata") or {}).get("status") if n.get("kind") == "execution" else None),
        "eventType": _facet(filtered_nodes, lambda n: (n.get("metadata") or {}).get("eventType") if n.get("kind") == "timeline" else None),
    }

    degree: Dict[str, int] = defaultdict(int)
    for e in filtered_edges:
        degree[e.get("from")] += 1
        degree[e.get("to")] += 1
    lineage_nodes = [dict(n, linkedDegree=degree.get(n.get("nodeId"), 0)) for n in filtered_nodes]

    out: Dict[str, Any] = {
        "ok": True, "schema": QUERY_SCHEMA, "version": VERSION, "release": "Linked Scientific Views & Cross-Filtering",
        "projectKey": req.projectKey, "sourceView": req.sourceView,
        "filter": req.filters.model_dump(), "filterHash": content_hash(req.filters.model_dump()),
        "sourceNodeCount": len(all_nodes), "sourceEdgeCount": len(all_edges),
        "filteredNodeCount": len(filtered_nodes), "filteredEdgeCount": len(filtered_edges),
        "selectedNodeIds": selected, "selectedVisibleNodeIds": selected_visible, "selectedFilteredOutNodeIds": selected_hidden,
        "views": {
            "canvas": {"nodes": filtered_nodes, "edges": filtered_edges, "layoutRevision": canvas.get("layoutRevision"), "layoutHash": canvas.get("layoutHash"), "viewport": canvas.get("viewport"), "layers": canvas.get("layers")},
            "assets": {"rows": _rows(filtered_nodes, "asset")},
            "executions": {"rows": _rows(filtered_nodes, "execution")},
            "timeline": {"rows": sorted(_rows(filtered_nodes, "timeline"), key=lambda x: str(x.get("at") or ""))},
            "lineage": {"nodes": lineage_nodes, "edges": filtered_edges},
            "facets": facets,
        },
        "linkedSelection": {"propagatedAcrossViews": True, "selectionIsViewStateOnly": True},
        "boundaries": {
            "filtersMutateScientificObjects": False, "selectionMutatesScientificObjects": False,
            "automaticScientificInterpretationPerformed": False, "automaticCausalInferencePerformed": False,
            "automaticWinnerSelectionPerformed": False, "automaticCoreDispatchPerformed": False,
        },
    }
    out["viewStateHash"] = content_hash(out)
    return out


def resolve_linked_selection(req: LinkedSelectionRequest) -> Dict[str, Any]:
    result = linked_views_query(LinkedViewsQueryRequest(projectKey=req.projectKey, filters=req.filters, selectedNodeIds=req.selectedNodeIds, sourceView=req.sourceView, timelineLimit=req.timelineLimit))
    selected = set(result.get("selectedVisibleNodeIds") or [])
    views = result["views"]
    out = {
        "ok": True, "schema": SELECTION_SCHEMA, "version": VERSION, "projectKey": req.projectKey, "sourceView": req.sourceView,
        "selectedNodeIds": result.get("selectedNodeIds") or [], "selectedVisibleNodeIds": sorted(selected),
        "selectedFilteredOutNodeIds": result.get("selectedFilteredOutNodeIds") or [],
        "views": {
            "canvas": {"selectedNodeIds": sorted(selected)},
            "assets": {"selectedRowNodeIds": [r["nodeId"] for r in views["assets"]["rows"] if r["nodeId"] in selected]},
            "executions": {"selectedRowNodeIds": [r["nodeId"] for r in views["executions"]["rows"] if r["nodeId"] in selected]},
            "timeline": {"selectedRowNodeIds": [r["nodeId"] for r in views["timeline"]["rows"] if r["nodeId"] in selected]},
            "lineage": {"selectedNodeIds": sorted(selected)},
        },
        "selectionIsViewStateOnly": True, "automaticScientificInterpretationPerformed": False,
        "automaticWinnerSelected": False, "automaticCoreDispatchPerformed": False,
    }
    out["selectionHash"] = content_hash(out)
    return out


def core_linked_views_plan(req: CoreLinkedViewsPlanRequest) -> Dict[str, Any]:
    project = load_project(req.projectKey)
    ws = project["workspace"]
    sid = str(req.coreSessionId or ws.get("coreSessionId") or "").strip()[:255]
    query = linked_views_query(LinkedViewsQueryRequest(projectKey=req.projectKey, filters=req.filters, selectedNodeIds=req.selectedNodeIds, sourceView=req.sourceView, timelineLimit=MAX_TIMELINE_NODES))
    base = core_project_plan(ProjectCorePlanRequest(projectKey=req.projectKey, coreProjectEntityId=req.coreProjectEntityId or req.projectKey, coreSessionId=sid, visibility=req.visibility, createdBy=req.createdBy))
    out: Dict[str, Any] = {
        "ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION, "projectKey": req.projectKey,
        "phase": base.get("phase"), "coreSessionId": sid or None, "coreSessionIdMustComeFromCore": True,
        "coreUnifiedResearchContract": CORE_UNIFIED_RUNTIME_CONTRACT, "projectPlan": base,
        "viewStateHash": query.get("viewStateHash"), "filterHash": query.get("filterHash"),
        "selectedNodeIds": query.get("selectedNodeIds") or [], "filteredNodeCount": query.get("filteredNodeCount"),
        "coreRequests": list(base.get("coreRequests") or []), "linkedViewBindingIsViewStateOnly": True,
        "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False,
        "automaticScientificInterpretationAuthorized": False, "automaticWinnerSelectionAuthorized": False,
    }
    if sid:
        out["coreRequests"].append({
            "path": CORE_PATHS["objectBindings"], "method": "POST", "phase": "linked-scientific-views-bind",
            "data": {
                "session_id": sid, "object_type": "workbench.linked-scientific-view-state",
                "object_ref": f"sc://workbench/linked-scientific-views/{req.projectKey}/{query['viewStateHash'][:24]}",
                "version_ref": f"sc://workbench/linked-scientific-views/{req.projectKey}@{VERSION}",
                "content_hash": query["viewStateHash"], "role": "view-state", "visibility": req.visibility,
                "metadata": {"workbenchVersion": VERSION, "projectKey": req.projectKey, "sourceView": req.sourceView, "filterHash": query.get("filterHash"), "scientificSourceOfTruth": False},
            }, "dispatchPerformed": False,
        })
    out["planHash"] = content_hash(out)
    return out


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION, "release": "Linked Scientific Views & Cross-Filtering",
        "views": ["canvas", "assets", "executions", "timeline", "lineage", "facets"],
        "capabilities": {
            "linkedScientificViews": True, "declarativeCrossFiltering": True, "crossViewSelectionPropagation": True,
            "facetCounts": True, "timelineRangeFiltering": True, "textFiltering": True, "neighborExpansion": True,
            "authoritativeCanvasProjectionReuse": True, "coreViewStatePlanning": True,
        },
        "authorities": {"visualProjection": "v8.6", "projects": "v8.2", "environments": "v8.1", "assets": "v8.3", "executions": "v8.4", "timelineAndLineage": "v8.5"},
        "boundaries": {
            "linkedViewsAreScientificSourceOfTruth": False, "filtersMutateScientificObjects": False,
            "selectionMutatesScientificObjects": False, "automaticScientificInterpretationAuthorized": False,
            "automaticCausalInferenceAuthorized": False, "automaticWinnerSelectionAuthorized": False,
            "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


@router.get("/linked-scientific-views/manifest")
def manifest_route():
    return manifest()


@router.post("/linked-scientific-views/query")
def query_route(req: LinkedViewsQueryRequest):
    try:
        return linked_views_query(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/linked-scientific-views/selection/resolve")
def selection_route(req: LinkedSelectionRequest):
    try:
        return resolve_linked_selection(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/linked-scientific-views/plan")
def core_plan_route(req: CoreLinkedViewsPlanRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    try:
        return core_linked_views_plan(req)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/v870/status")
def status_route():
    return {
        "ok": True, "schema": SCHEMA, "version": VERSION, "release": "Linked Scientific Views & Cross-Filtering",
        "linkedScientificViews": True, "crossFiltering": True, "crossViewSelection": True,
        "linkedViewsAreScientificSourceOfTruth": False, "automaticScientificInterpretation": False,
        "automaticWinnerSelection": False, "automaticCoreDispatch": False,
    }

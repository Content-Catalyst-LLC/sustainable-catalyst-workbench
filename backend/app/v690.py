"""Workbench v6.9.0 — Core Visual Reasoning Runtime Adapter.

Adapts Workbench-owned numerical and analytical results into renderer-neutral,
Core-compatible visual research manifests and explicit persistence plans for the
Platform Core visual reasoning stack.  Workbench prepares semantic objects,
scene graph state, visualization grammar hints, unified-visual workspace
handoffs, and cross-product visual bindings. Platform Core remains the registry
and visual-semantics authority. Workbench does not render on behalf of Core and
never persists or dispatches to Core automatically.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route
from .v650 import PRODUCT_REF
from .v660 import CORE_UNIFIED_RUNTIME_CONTRACT
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT

VERSION = APP_VERSION
SCHEMA = "sc-workbench-core-visual-reasoning-runtime-adapter/1.0"
RESULT_SCHEMA = "sc-workbench-visual-research-result-manifest/1.0"
CORE_REQUEST_SCHEMA = "sc-workbench-core-visual-request/1.0"
BRIDGE_REF = "workbench:/integration/core/visual-reasoning"

CORE_VISUAL_OBJECT_MODEL = "platform-core:/v1/visual-reasoning"
CORE_SCENE_CONTRACT = "sc.visual-runtime.scene.v1"
CORE_COMPOSITION_CONTRACT = "sc.visual-runtime.composition.v1"
CORE_GRAMMAR_CONTRACT = "sc.visual-runtime.grammar.v1"
CORE_LINKED_VIEWS_CONTRACT = "sc.visual-runtime.linked-views.v1"
CORE_VISUAL_QUERY_CONTRACT = "sc.visual-runtime.visual-query.v1"
CORE_UNIFIED_VISUAL_CONTRACT = "sc.visual-runtime.unified-reasoning.v1"
CORE_CROSS_PRODUCT_VISUAL_CONTRACT = "sc.visual-runtime.cross-product-integration.v1"

CORE_PATHS = {
    "visualReadiness": "/v1/visual-reasoning/readiness",
    "visualObjects": "/v1/visual-reasoning/objects",
    "visualElements": "/v1/visual-reasoning/objects/{visual_entity_id}/elements",
    "visualRelations": "/v1/visual-reasoning/objects/{visual_entity_id}/relations",
    "visualLayers": "/v1/visual-reasoning/objects/{visual_entity_id}/layers",
    "visualAnnotations": "/v1/visual-reasoning/objects/{visual_entity_id}/annotations",
    "visualSnapshots": "/v1/visual-reasoning/objects/{visual_entity_id}/snapshots",
    "sceneReadiness": "/v1/visual-runtime/readiness",
    "scenes": "/v1/visual-runtime/scenes",
    "sceneLayers": "/v1/visual-runtime/scenes/{scene_id}/layers",
    "sceneNodes": "/v1/visual-runtime/scenes/{scene_id}/nodes",
    "sceneEdges": "/v1/visual-runtime/scenes/{scene_id}/edges",
    "sceneAnnotations": "/v1/visual-runtime/scenes/{scene_id}/annotations",
    "sceneViews": "/v1/visual-runtime/scenes/{scene_id}/views",
    "sceneBindings": "/v1/visual-runtime/scenes/{scene_id}/bindings",
    "sceneSnapshots": "/v1/visual-runtime/scenes/{scene_id}/snapshots",
    "compositionReadiness": "/v1/visual-runtime/composition/readiness",
    "compositions": "/v1/visual-runtime/composition/scenes/{scene_id}/compositions",
    "compositionAssignments": "/v1/visual-runtime/composition/compositions/{composition_id}/assignments",
    "grammarReadiness": "/v1/visual-runtime/grammar/readiness",
    "grammarSpecifications": "/v1/visual-runtime/grammar/specifications",
    "grammarDataBindings": "/v1/visual-runtime/grammar/specifications/{specification_id}/data-bindings",
    "grammarMarks": "/v1/visual-runtime/grammar/specifications/{specification_id}/marks",
    "grammarScales": "/v1/visual-runtime/grammar/specifications/{specification_id}/scales",
    "grammarEncodings": "/v1/visual-runtime/grammar/specifications/{specification_id}/encodings",
    "grammarGuides": "/v1/visual-runtime/grammar/specifications/{specification_id}/guides",
    "unifiedReadiness": "/v1/visual-runtime/unified/readiness",
    "unifiedWorkspaces": "/v1/visual-runtime/unified/compositions/{composition_id}/workspaces",
    "unifiedLayerBindings": "/v1/visual-runtime/unified/workspaces/{workspace_id}/layer-bindings",
    "unifiedStateBridges": "/v1/visual-runtime/unified/workspaces/{workspace_id}/state-bridges",
    "unifiedHandoffs": "/v1/visual-runtime/unified/workspaces/{workspace_id}/handoffs",
    "crossProductReadiness": "/v1/visual-runtime/integrations/readiness",
    "crossProductIntegrations": "/v1/visual-runtime/integrations/workspaces/{workspace_id}/products",
    "crossProductObjectBindings": "/v1/visual-runtime/integrations/integrations/{integration_id}/object-bindings",
    "crossProductContextBindings": "/v1/visual-runtime/integrations/integrations/{integration_id}/context-bindings",
    "crossProductCapabilities": "/v1/visual-runtime/integrations/integrations/{integration_id}/capabilities",
}

SUPPORTED_DATA_KINDS = {
    "series", "scatter", "distribution", "matrix", "sensitivity",
    "ensemble", "scenario", "model-run", "table", "network",
}
SUPPORTED_VISUAL_KINDS = {
    "generic", "system-map", "flow-map", "scenario-landscape", "model-map",
    "model-canvas", "evidence-map", "causal-map", "spatial-temporal-map",
}
SUPPORTED_PURPOSES = {"explore", "compare", "explain", "diagnose", "communicate"}
SUPPORTED_COORDINATE_SPACES = {"abstract", "geographic", "temporal", "cartesian", "none"}

router = APIRouter(tags=["workbench-v690-core-visual-reasoning-runtime-adapter"])


def _bad(exc: Exception) -> HTTPException:
    return exc if isinstance(exc, HTTPException) else HTTPException(status_code=422, detail=str(exc))


def _bounded(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _core_request(path: str, data: Dict[str, Any], phase: str, *, method: str = "POST") -> Dict[str, Any]:
    out = {
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "method": method,
        "path": path,
        "phase": phase,
        "data": data,
        "payload": {"data": data} if method == "POST" else None,
        "automaticDispatchAuthorized": False,
        "callerMustPersistToCore": method == "POST",
    }
    out["requestHash"] = content_hash(out)
    return out


def visual_reasoning_manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "productRef": PRODUCT_REF,
        "runtime": RUNTIME_KIND,
        "bridgeRef": BRIDGE_REF,
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "coreVisualObjectModel": CORE_VISUAL_OBJECT_MODEL,
        "coreSceneContract": CORE_SCENE_CONTRACT,
        "coreCompositionContract": CORE_COMPOSITION_CONTRACT,
        "coreGrammarContract": CORE_GRAMMAR_CONTRACT,
        "coreLinkedViewsContract": CORE_LINKED_VIEWS_CONTRACT,
        "coreVisualQueryContract": CORE_VISUAL_QUERY_CONTRACT,
        "coreUnifiedVisualContract": CORE_UNIFIED_VISUAL_CONTRACT,
        "coreCrossProductVisualContract": CORE_CROSS_PRODUCT_VISUAL_CONTRACT,
        "corePaths": dict(CORE_PATHS),
        "supportedDataKinds": sorted(SUPPORTED_DATA_KINDS),
        "supportedVisualKinds": sorted(SUPPORTED_VISUAL_KINDS),
        "capabilities": [
            "numerical-result-to-visual-research-manifest",
            "renderer-neutral-visual-object-planning",
            "scene-graph-node-and-layer-planning",
            "analytical-visualization-grammar-planning",
            "uncertainty-aware-visual-value-binding",
            "v680-scenario-uncertainty-result-visualization",
            "v670-computation-lineage-visual-binding",
            "unified-visual-reasoning-workspace-handoff",
            "cross-product-visual-runtime-binding",
            "deterministic-visual-manifest-hashing",
        ],
        "boundaries": {
            "workbenchAdaptsNumericalResults": True,
            "workbenchComputesDerivedVisualStatistics": True,
            "coreOwnsVisualSemantics": True,
            "coreOwnsSceneRegistry": True,
            "coreOwnsGrammarRegistry": True,
            "coreOwnsUnifiedVisualWorkspace": True,
            "rendererExecutionByWorkbenchForCore": False,
            "rendererExecutionByCore": False,
            "automaticLayoutByCore": False,
            "automaticVisualInference": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "arbitraryCoreCodeExecution": False,
            "coreDeterminesTruth": False,
            "workbenchDeterminesTruth": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


class VisualResultAdapterRequest(BaseModel):
    projectEntityId: str
    title: str
    dataKind: Literal["series", "scatter", "distribution", "matrix", "sensitivity", "ensemble", "scenario", "model-run", "table", "network"] = "series"
    data: Dict[str, Any] = Field(default_factory=dict)
    visualKind: Literal["generic", "system-map", "flow-map", "scenario-landscape", "model-map", "model-canvas", "evidence-map", "causal-map", "spatial-temporal-map"] = "generic"
    reasoningPurpose: Literal["explore", "compare", "explain", "diagnose", "communicate"] = "explore"
    coordinateSpace: Literal["abstract", "geographic", "temporal", "cartesian", "none"] = "cartesian"
    sourceRef: str = ""
    sourceKind: str = "workbench-result"
    workbenchExecutionRef: str = ""
    coreExecutionId: str = ""
    coreSessionId: str = ""
    unit: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("projectEntityId", "title")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = _bounded(value, 300)
        if not value:
            raise ValueError("projectEntityId and title are required")
        return value


class VisualObjectPlanRequest(BaseModel):
    manifest: Dict[str, Any]
    visibility: Literal["private", "workspace", "public"] = "workspace"


class ScenePlanRequest(BaseModel):
    manifest: Dict[str, Any]
    coreVisualEntityId: str
    visibility: Literal["private", "workspace", "public"] = "workspace"

    @field_validator("coreVisualEntityId")
    @classmethod
    def visual_id_required(cls, value: str) -> str:
        value = _bounded(value, 255)
        if not value:
            raise ValueError("coreVisualEntityId must be issued by Platform Core")
        return value


class GrammarPlanRequest(BaseModel):
    manifest: Dict[str, Any]
    coreSceneId: str
    coreViewId: str = ""
    visibility: Literal["private", "workspace", "public"] = "workspace"

    @field_validator("coreSceneId")
    @classmethod
    def scene_id_required(cls, value: str) -> str:
        value = _bounded(value, 255)
        if not value:
            raise ValueError("coreSceneId must be issued by Platform Core")
        return value


class UnifiedWorkspacePlanRequest(BaseModel):
    manifest: Dict[str, Any]
    coreCompositionId: str
    coreSceneIds: List[str] = Field(default_factory=list)
    coreViewIds: List[str] = Field(default_factory=list)
    coreGrammarSpecificationIds: List[str] = Field(default_factory=list)

    @field_validator("coreCompositionId")
    @classmethod
    def composition_id_required(cls, value: str) -> str:
        value = _bounded(value, 255)
        if not value:
            raise ValueError("coreCompositionId must be issued by Platform Core")
        return value


class CrossProductPlanRequest(BaseModel):
    manifest: Dict[str, Any]
    coreWorkspaceId: str
    coreVisualEntityIds: List[str] = Field(default_factory=list)
    coreIntegrationId: str = ""

    @field_validator("coreWorkspaceId")
    @classmethod
    def workspace_id_required(cls, value: str) -> str:
        value = _bounded(value, 255)
        if not value:
            raise ValueError("coreWorkspaceId must be issued by Platform Core")
        return value


def _numeric(values: Any) -> List[float]:
    if not isinstance(values, list):
        return []
    out: List[float] = []
    for value in values:
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            out.append(float(value))
    return out


def _quantile(values: List[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * min(1.0, max(0.0, q))
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return xs[lo]
    frac = pos - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def _series_points(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    xs = data.get("x") if isinstance(data.get("x"), list) else []
    ys = data.get("y") if isinstance(data.get("y"), list) else []
    if ys and not xs:
        xs = list(range(len(ys)))
    n = min(len(xs), len(ys))
    return [{"index": i, "x": xs[i], "y": ys[i]} for i in range(n)]


def adapt_visual_result(request: VisualResultAdapterRequest) -> Dict[str, Any]:
    data = dict(request.data)
    elements: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}
    mark_kind = "point"
    grammar_kind = "cartesian"
    coordinate_system = "cartesian"
    semantic_role = "result"

    if request.dataKind in {"series", "scatter"}:
        points = _series_points(data)
        if not points:
            raise ValueError("series/scatter data requires numeric-compatible x/y arrays or a y array")
        elements = [{"element_key": f"point-{p['index']}", "element_kind": "metric", "semantic_role": "result", "label": str(p["x"]), "value": {"x": p["x"], "y": p["y"], "unit": request.unit}} for p in points]
        ys = _numeric([p["y"] for p in points])
        if ys:
            summary = {"count": len(ys), "min": min(ys), "max": max(ys), "mean": statistics.fmean(ys)}
        mark_kind = "line" if request.dataKind == "series" else "point"
    elif request.dataKind == "distribution":
        values = _numeric(data.get("values"))
        if not values:
            raise ValueError("distribution data requires a non-empty numeric values array")
        summary = {"count": len(values), "min": min(values), "max": max(values), "mean": statistics.fmean(values), "p05": _quantile(values, .05), "p50": _quantile(values, .5), "p95": _quantile(values, .95)}
        elements = [{"element_key": f"sample-{i}", "element_kind": "metric", "semantic_role": "uncertainty", "label": str(i), "value": {"value": v, "unit": request.unit}} for i, v in enumerate(values[:5000])]
        mark_kind = "area"; semantic_role = "uncertainty"
    elif request.dataKind == "sensitivity":
        indices = data.get("indices") or data.get("factors") or {}
        if not isinstance(indices, dict) or not indices:
            raise ValueError("sensitivity data requires an indices mapping")
        vals = []
        for key, raw in sorted(indices.items()):
            if isinstance(raw, dict):
                value = raw.get("total", raw.get("mu_star", raw.get("value", 0)))
            else:
                value = raw
            if not isinstance(value, (int, float)):
                continue
            vals.append(float(value))
            elements.append({"element_key": f"factor-{key}", "element_kind": "parameter", "semantic_role": "uncertainty", "label": str(key), "value": {"sensitivity": float(value)}})
        if not elements:
            raise ValueError("sensitivity indices contain no numeric values")
        summary = {"factorCount": len(elements), "maxSensitivity": max(vals)}
        mark_kind = "bar"; semantic_role = "uncertainty"
    elif request.dataKind == "matrix":
        matrix = data.get("matrix")
        if not isinstance(matrix, list) or not matrix or not all(isinstance(row, list) for row in matrix):
            raise ValueError("matrix data requires a non-empty matrix array")
        width = max((len(row) for row in matrix), default=0)
        for r, row in enumerate(matrix):
            for c, value in enumerate(row):
                if isinstance(value, (int, float)):
                    elements.append({"element_key": f"cell-{r}-{c}", "element_kind": "metric", "semantic_role": "result", "label": f"{r},{c}", "value": {"row": r, "column": c, "value": float(value)}})
        summary = {"rows": len(matrix), "columns": width, "numericCells": len(elements)}
        mark_kind = "matrix-cell"; grammar_kind = "matrix"
    elif request.dataKind in {"ensemble", "scenario", "model-run"}:
        outputs = data.get("outputs", data)
        if not isinstance(outputs, dict) or not outputs:
            raise ValueError("ensemble/scenario/model-run data requires output fields")
        for key, raw in sorted(outputs.items()):
            values = _numeric(raw if isinstance(raw, list) else [raw])
            value_payload: Dict[str, Any] = {"raw": raw}
            if values:
                value_payload.update({"mean": statistics.fmean(values), "min": min(values), "max": max(values), "count": len(values)})
            elements.append({"element_key": f"output-{key}", "element_kind": "metric", "semantic_role": "output", "label": str(key), "value": value_payload})
        summary = {"outputCount": len(elements)}
        mark_kind = "bar"; semantic_role = "output"
    elif request.dataKind == "network":
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        if not isinstance(nodes, list): nodes = []
        if not isinstance(edges, list): edges = []
        elements = [{"element_key": _bounded(n.get("id") or n.get("key") or f"node-{i}", 180), "element_kind": "node", "semantic_role": _bounded(n.get("role"), 80) or "context", "label": _bounded(n.get("label") or n.get("id") or f"Node {i+1}", 300), "value": n.get("value")} for i, n in enumerate(nodes) if isinstance(n, dict)]
        summary = {"nodeCount": len(elements), "edgeCount": len(edges)}
        mark_kind = "node"; grammar_kind = "network"; coordinate_system = "abstract"
    else:
        rows = data.get("rows", [])
        if not isinstance(rows, list): rows = []
        elements = [{"element_key": f"row-{i}", "element_kind": "metric", "semantic_role": "result", "label": f"Row {i+1}", "value": row} for i, row in enumerate(rows[:5000])]
        summary = {"rowCount": len(elements)}
        mark_kind = "text"; coordinate_system = "abstract"

    provenance = {
        "source_product": PRODUCT_KEY,
        "workbench_version": VERSION,
        "source_ref": request.sourceRef or None,
        "source_kind": request.sourceKind,
        "workbench_execution_ref": request.workbenchExecutionRef or None,
        "core_execution_id": request.coreExecutionId or None,
        "core_session_id": request.coreSessionId or None,
        **request.provenance,
    }
    out = {
        "ok": True,
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "projectEntityId": request.projectEntityId,
        "title": request.title,
        "dataKind": request.dataKind,
        "visualKind": request.visualKind,
        "reasoningPurpose": request.reasoningPurpose,
        "coordinateSpace": request.coordinateSpace,
        "summary": summary,
        "elements": elements,
        "rawData": data,
        "sceneHints": {"sceneKind": "model-canvas" if request.visualKind == "model-canvas" else "semantic", "coordinateSpace": request.coordinateSpace, "semanticRole": semantic_role},
        "grammarHints": {"grammarKind": grammar_kind, "coordinateSystem": coordinate_system, "markKind": mark_kind},
        "provenance": provenance,
        "metadata": dict(request.metadata),
        "rendererNeutral": True,
        "calculated_by_workbench": True,
        "calculated_by_core": False,
        "rendered_by_workbench_for_core": False,
        "rendered_by_core": False,
    }
    out["manifestHash"] = content_hash(out)
    return out


def _require_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    if manifest.get("schema") != RESULT_SCHEMA:
        raise ValueError(f"manifest.schema must be {RESULT_SCHEMA}")
    if not _bounded(manifest.get("projectEntityId"), 255):
        raise ValueError("manifest.projectEntityId is required")
    return manifest


def build_visual_object_plan(request: VisualObjectPlanRequest) -> Dict[str, Any]:
    m = _require_manifest(dict(request.manifest))
    visual = {
        "name": _bounded(m.get("title"), 300),
        "description": f"Workbench {m.get('dataKind')} result adapted for Core visual reasoning.",
        "visibility": request.visibility,
        "status": "active",
        "visual_kind": m.get("visualKind", "generic"),
        "reasoning_purpose": m.get("reasoningPurpose", "explore"),
        "semantic_state": "draft",
        "coordinate_space": m.get("coordinateSpace", "abstract"),
        "project_entity_id": m["projectEntityId"],
        "lens": {"source_product": PRODUCT_KEY, "data_kind": m.get("dataKind"), "summary": m.get("summary", {})},
        "filters": {},
        "assumptions": [],
        "metadata": {"workbenchManifestHash": m.get("manifestHash"), **dict(m.get("metadata") or {})},
    }
    req = _core_request(CORE_PATHS["visualObjects"], visual, "create-visual-reasoning-object")
    out = {"ok": True, "schema": SCHEMA, "version": VERSION, "phase": "visual-object-registration", "coreRequests": [req], "requestCount": 1, "coreVisualEntityIdMustComeFromCore": True, "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False}
    out["planHash"] = content_hash(out)
    return out


def build_scene_plan(request: ScenePlanRequest) -> Dict[str, Any]:
    m = _require_manifest(dict(request.manifest)); visual_id = request.coreVisualEntityId
    prov = dict(m.get("provenance") or {})
    reqs: List[Dict[str, Any]] = []
    for i, elem in enumerate(m.get("elements") or []):
        data = {"element_key": _bounded(elem.get("element_key") or f"element-{i}", 180), "element_kind": elem.get("element_kind", "metric"), "semantic_role": elem.get("semantic_role", "result"), "label": _bounded(elem.get("label") or f"Element {i+1}", 300), "value": elem.get("value"), "position": {}, "geometry": {}, "style_hints": {}, "provenance": prov, "metadata": {"workbenchManifestHash": m.get("manifestHash")}}
        reqs.append(_core_request(CORE_PATHS["visualElements"].format(visual_entity_id=visual_id), data, "create-visual-element"))
    reqs.append(_core_request(CORE_PATHS["visualLayers"].format(visual_entity_id=visual_id), {"layer_key": "workbench-results", "name": "Workbench Results", "layer_kind": "uncertainty" if m.get("dataKind") in {"distribution", "sensitivity", "ensemble"} else "data", "order_index": 0, "visible_by_default": True, "metadata": {"workbenchManifestHash": m.get("manifestHash")}}, "create-visual-layer"))
    scene = {"project_entity_id": m["projectEntityId"], "source_visual_entity_id": visual_id, "scene_key": f"workbench-{str(m.get('manifestHash',''))[:16]}", "name": _bounded(m.get("title"), 300), "description": "Renderer-neutral Workbench result scene.", "scene_kind": "model-canvas" if m.get("visualKind") == "model-canvas" else "semantic", "coordinate_space": m.get("coordinateSpace", "abstract"), "status": "draft", "visibility": request.visibility, "scene_metadata": {"workbenchManifestHash": m.get("manifestHash"), "dataKind": m.get("dataKind")}, "provenance": prov}
    reqs.append(_core_request(CORE_PATHS["scenes"], scene, "create-scene"))
    out = {"ok": True, "schema": SCHEMA, "version": VERSION, "phase": "semantic-object-and-scene-registration", "coreVisualEntityId": visual_id, "coreRequests": reqs, "requestCount": len(reqs), "coreSceneIdMustComeFromCore": True, "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False}
    out["planHash"] = content_hash(out)
    return out


def build_grammar_plan(request: GrammarPlanRequest) -> Dict[str, Any]:
    m = _require_manifest(dict(request.manifest)); scene_id=request.coreSceneId
    prov=dict(m.get("provenance") or {}); reqs=[]
    reqs.append(_core_request(CORE_PATHS["sceneLayers"].format(scene_id=scene_id), {"layer_key":"workbench-results","name":"Workbench Results","layer_kind":"semantic","order_index":0,"visible_by_default":True,"locked_by_default":False,"style_hints":{},"metadata":{"workbenchManifestHash":m.get("manifestHash")}}, "create-scene-layer"))
    for i, elem in enumerate((m.get("elements") or [])[:5000]):
        node={"node_key":_bounded(elem.get("element_key") or f"node-{i}",180),"node_kind":"metric","semantic_role":elem.get("semantic_role","result"),"label":_bounded(elem.get("label") or f"Node {i+1}",300),"position":{},"geometry":{},"value":elem.get("value"),"uncertainty":m.get("summary",{}) if m.get("dataKind") in {"distribution","sensitivity","ensemble"} else {},"style_hints":{},"provenance":prov,"metadata":{"workbenchManifestHash":m.get("manifestHash")}}
        reqs.append(_core_request(CORE_PATHS["sceneNodes"].format(scene_id=scene_id), node, "create-scene-node"))
    view={"view_key":"workbench-primary","name":_bounded(m.get("title"),300),"view_kind":"canvas","viewport":{},"selection":{},"filter":{},"layer_state":{},"interaction_state":{},"renderer_hints":{"renderer_neutral":True,"data_kind":m.get("dataKind")},"metadata":{"workbenchManifestHash":m.get("manifestHash")}}
    reqs.append(_core_request(CORE_PATHS["sceneViews"].format(scene_id=scene_id),view,"create-scene-view"))
    composition={"composition_key":"workbench-primary","name":_bounded(m.get("title"),300),"composition_kind":"single","layout_spec":{"policy":"external-renderer"},"shared_state":{},"visibility":request.visibility,"metadata":{"workbenchManifestHash":m.get("manifestHash")}}
    reqs.append(_core_request(CORE_PATHS["compositions"].format(scene_id=scene_id),composition,"create-view-composition"))
    grammar={"scene_id":scene_id,"view_id":_bounded(request.coreViewId,255) or None,"grammar_key":"workbench-result-grammar","name":_bounded(m.get("title"),300),"grammar_kind":m.get("grammarHints",{}).get("grammarKind","cartesian"),"coordinate_system":m.get("grammarHints",{}).get("coordinateSystem","cartesian"),"data_policy":{"source_product":PRODUCT_KEY,"manifest_hash":m.get("manifestHash")},"interaction_policy":{},"visibility":request.visibility,"metadata":{"markKind":m.get("grammarHints",{}).get("markKind","point"),"renderer_neutral":True}}
    reqs.append(_core_request(CORE_PATHS["grammarSpecifications"],grammar,"create-grammar-specification"))
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"scene-and-grammar-registration","coreSceneId":scene_id,"coreRequests":reqs,"requestCount":len(reqs),"coreViewIdMustComeFromCore":not bool(request.coreViewId),"coreCompositionIdMustComeFromCore":True,"coreGrammarSpecificationIdMustComeFromCore":True,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False}
    out["planHash"]=content_hash(out);return out


def build_unified_workspace_plan(request: UnifiedWorkspacePlanRequest) -> Dict[str, Any]:
    m=_require_manifest(dict(request.manifest)); cid=request.coreCompositionId; prov=dict(m.get("provenance") or {})
    workspace={"workspace_key":"workbench-visual-reasoning","name":_bounded(m.get("title"),300),"purpose":"Explore Workbench computational results with Core visual reasoning.","status":"draft","visibility":"workspace","settings":{"renderer_neutral":True,"source_product":PRODUCT_KEY},"provenance":prov,"metadata":{"workbenchManifestHash":m.get("manifestHash")}}
    reqs=[_core_request(CORE_PATHS["unifiedWorkspaces"].format(composition_id=cid),workspace,"create-unified-visual-workspace")]
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"unified-visual-workspace-registration","coreCompositionId":cid,"coreRequests":reqs,"requestCount":len(reqs),"coreWorkspaceIdMustComeFromCore":True,"postWorkspaceBindingTemplate":{"scene_ids":request.coreSceneIds,"view_ids":request.coreViewIds,"grammar_specification_ids":request.coreGrammarSpecificationIds,"display_contract":{"renderer_neutral":True,"source_product":PRODUCT_KEY}},"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False}
    out["planHash"]=content_hash(out);return out


def build_cross_product_plan(request: CrossProductPlanRequest) -> Dict[str, Any]:
    m=_require_manifest(dict(request.manifest)); wid=request.coreWorkspaceId; prov=dict(m.get("provenance") or {})
    integration={"product_key":"workbench","integration_key":"workbench-v690","name":"Workbench Visual Reasoning Runtime","status":"declared","runtime_contract":{"version":VERSION,"bridgeRef":BRIDGE_REF,"resultSchema":RESULT_SCHEMA},"provenance":prov,"metadata":{"workbenchManifestHash":m.get("manifestHash")}}
    reqs=[_core_request(CORE_PATHS["crossProductIntegrations"].format(workspace_id=wid),integration,"create-cross-product-integration")]
    if request.coreIntegrationId:
        iid=_bounded(request.coreIntegrationId,255)
        reqs.append(_core_request(CORE_PATHS["crossProductObjectBindings"].format(integration_id=iid),{"binding_key":"workbench-results","canonical_object_refs":request.coreVisualEntityIds,"product_object_refs":[m.get("provenance",{}).get("source_ref") or f"workbench:visual-manifest:{m.get('manifestHash')}"],"semantic_roles":["result","uncertainty"] if m.get("dataKind") in {"distribution","sensitivity","ensemble"} else ["result"],"provenance":prov},"create-cross-product-object-binding"))
        reqs.append(_core_request(CORE_PATHS["crossProductCapabilities"].format(integration_id=iid),{"capability_key":"visualize","object_kinds":[m.get("dataKind")],"operation_contract":{"source_product":"workbench","renderer_neutral":True},"output_contract":{"schema":RESULT_SCHEMA},"provenance":prov},"create-cross-product-capability-binding"))
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"cross-product-visual-runtime-registration","coreWorkspaceId":wid,"coreIntegrationIdMustComeFromCore":not bool(request.coreIntegrationId),"coreRequests":reqs,"requestCount":len(reqs),"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False}
    out["planHash"]=content_hash(out);return out


@router.get("/integration/core/visual-reasoning/manifest")
def manifest(x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token); return visual_reasoning_manifest()


@router.post("/integration/core/visual-reasoning/result/adapt")
def result_adapt(request: VisualResultAdapterRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:return adapt_visual_result(request)
    except Exception as exc:raise _bad(exc)


@router.post("/integration/core/visual-reasoning/object/plan")
def object_plan(request: VisualObjectPlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_visual_object_plan(request)
    except Exception as exc:raise _bad(exc)


@router.post("/integration/core/visual-reasoning/scene/plan")
def scene_plan(request: ScenePlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_scene_plan(request)
    except Exception as exc:raise _bad(exc)


@router.post("/integration/core/visual-reasoning/grammar/plan")
def grammar_plan(request: GrammarPlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_grammar_plan(request)
    except Exception as exc:raise _bad(exc)


@router.post("/integration/core/visual-reasoning/unified-workspace/plan")
def unified_workspace_plan(request: UnifiedWorkspacePlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_unified_workspace_plan(request)
    except Exception as exc:raise _bad(exc)


@router.post("/integration/core/visual-reasoning/cross-product/plan")
def cross_product_plan(request: CrossProductPlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_cross_product_plan(request)
    except Exception as exc:raise _bad(exc)


@router.get("/v690/status")
def v690_status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Core Visual Reasoning Runtime Adapter",
        "coreVisualObjectModel": CORE_VISUAL_OBJECT_MODEL,
        "coreSceneContract": CORE_SCENE_CONTRACT,
        "coreGrammarContract": CORE_GRAMMAR_CONTRACT,
        "coreUnifiedVisualContract": CORE_UNIFIED_VISUAL_CONTRACT,
        "coreCrossProductVisualContract": CORE_CROSS_PRODUCT_VISUAL_CONTRACT,
        "numericalResultAdaptation": True,
        "rendererNeutral": True,
        "uncertaintyAware": True,
        "v680ScenarioUncertaintyIntegration": True,
        "v670ExecutionLineageIntegration": True,
        "coreIssuedVisualIdsRequired": True,
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
        "rendererExecutionByCore": False,
        "arbitraryCoreCodeExecution": False,
    }

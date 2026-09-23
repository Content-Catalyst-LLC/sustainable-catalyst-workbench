"""Workbench v7.11.0 — Visual Scientific Computing Workspace.

Renderer-neutral scientific views over bounded Workbench results. The workspace
links views and controls explicitly, can prepare recomputation mutations, and
can prepare Platform Core visual-reasoning registration plans. It never runs a
renderer on behalf of Core and never dispatches/persists to Core automatically.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v690 import (
    VisualResultAdapterRequest,
    VisualObjectPlanRequest,
    adapt_visual_result,
    build_visual_object_plan,
    CORE_SCENE_CONTRACT,
    CORE_GRAMMAR_CONTRACT,
    CORE_LINKED_VIEWS_CONTRACT,
    CORE_VISUAL_QUERY_CONTRACT,
    CORE_UNIFIED_VISUAL_CONTRACT,
)

VERSION = APP_VERSION
SCHEMA = "sc-workbench-visual-scientific-computing-workspace/1.0"
VIEW_SCHEMA = "sc-workbench-scientific-view/1.0"
STATE_SCHEMA = "sc-workbench-visual-linked-state/1.0"
CONTROL_PLAN_SCHEMA = "sc-workbench-visual-control-recompute-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-core-visual-workspace-plan/1.0"
MAX_VIEWS = 24
MAX_CONTROLS = 64
MAX_LINKS = 128
MAX_POINTS = 10000
LINKED_VIEWS_CONTRACT = "sc.visual-runtime.linked-views.v1"

ViewKind = Literal[
    "line", "scatter", "trajectory", "uncertainty-band", "distribution",
    "heatmap", "convergence", "pareto", "table", "scalar"
]
Purpose = Literal["explore", "compare", "diagnose", "explain", "communicate"]
router = APIRouter(tags=["workbench-v7110-visual-scientific-computing-workspace"])


def _get_path(value: Any, path: str) -> Any:
    cur = value
    for token in [p for p in str(path or "").split(".") if p]:
        if isinstance(cur, dict) and token in cur:
            cur = cur[token]
        elif isinstance(cur, list) and token.isdigit() and int(token) < len(cur):
            cur = cur[int(token)]
        else:
            raise ValueError(f"sourcePath not found: {path}")
    return cur


def _set_path(value: Dict[str, Any], path: str, item: Any) -> None:
    parts = [p for p in str(path or "").split(".") if p]
    if not parts:
        raise ValueError("targetPath is required")
    cur: Dict[str, Any] = value
    for token in parts[:-1]:
        nxt = cur.get(token)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[token] = nxt
        cur = nxt
    cur[parts[-1]] = item


def _numeric_list(value: Any, name: str) -> List[float]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be an array")
    if len(value) > MAX_POINTS:
        raise ValueError(f"{name} exceeds {MAX_POINTS} points")
    out: List[float] = []
    for raw in value:
        if not isinstance(raw, (int, float)):
            raise ValueError(f"{name} must contain numeric values")
        out.append(float(raw))
    return out


class ScientificViewSpec(BaseModel):
    viewId: str = Field(min_length=1, max_length=120)
    kind: ViewKind
    title: str = Field(min_length=1, max_length=300)
    data: Dict[str, Any] = Field(default_factory=dict)
    sourceRef: str = Field(default="", max_length=500)
    executionObjectRef: str = Field(default="", max_length=500)
    unit: str = Field(default="", max_length=80)
    purpose: Purpose = "explore"
    linkGroups: List[str] = Field(default_factory=list, max_length=20)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("linkGroups")
    @classmethod
    def unique_groups(cls, value: List[str]) -> List[str]:
        if len(set(value)) != len(value):
            raise ValueError("linkGroups must be unique")
        return value


class VisualControlSpec(BaseModel):
    controlId: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=300)
    targetPath: str = Field(min_length=1, max_length=500)
    value: Any = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = Field(default=None, gt=0)
    unit: str = Field(default="", max_length=80)
    targetRuntimePath: str = Field(default="", max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("control minimum must be <= maximum")
        if isinstance(self.value, (int, float)):
            if self.minimum is not None and self.value < self.minimum:
                raise ValueError("control value is below minimum")
            if self.maximum is not None and self.value > self.maximum:
                raise ValueError("control value is above maximum")
        return self


class VisualLinkSpec(BaseModel):
    linkId: str = Field(min_length=1, max_length=120)
    sourceViewId: str = Field(min_length=1, max_length=120)
    targetViewId: str = Field(min_length=1, max_length=120)
    relation: Literal["selection", "filter", "cursor", "time", "parameter"] = "selection"
    sourceField: str = Field(default="", max_length=240)
    targetField: str = Field(default="", max_length=240)


class VisualWorkspaceSpec(BaseModel):
    workspaceKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=300)
    projectEntityId: str = Field(min_length=1, max_length=255)
    views: List[ScientificViewSpec] = Field(min_length=1, max_length=MAX_VIEWS)
    controls: List[VisualControlSpec] = Field(default_factory=list, max_length=MAX_CONTROLS)
    links: List[VisualLinkSpec] = Field(default_factory=list, max_length=MAX_LINKS)
    sourceNotebookRunHash: str = Field(default="", max_length=200)
    sourceWorkflowGraphRunHash: str = Field(default="", max_length=200)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_refs(self):
        ids = [v.viewId for v in self.views]
        if len(set(ids)) != len(ids):
            raise ValueError("viewId values must be unique")
        controls = [c.controlId for c in self.controls]
        if len(set(controls)) != len(controls):
            raise ValueError("controlId values must be unique")
        link_ids = [l.linkId for l in self.links]
        if len(set(link_ids)) != len(link_ids):
            raise ValueError("linkId values must be unique")
        known = set(ids)
        for link in self.links:
            if link.sourceViewId not in known or link.targetViewId not in known:
                raise ValueError("visual links must reference declared views")
        return self


class WorkspaceBuildRequest(BaseModel):
    workspace: VisualWorkspaceSpec


class WorkspaceValidateRequest(BaseModel):
    visualWorkspace: Dict[str, Any]


class LinkedStateRequest(BaseModel):
    visualWorkspace: Dict[str, Any]
    sourceViewId: str
    selection: Dict[str, Any] = Field(default_factory=dict)
    filter: Dict[str, Any] = Field(default_factory=dict)
    cursor: Dict[str, Any] = Field(default_factory=dict)


class ControlPlanRequest(BaseModel):
    visualWorkspace: Dict[str, Any]
    controlId: str
    value: Any
    runtimeRequest: Dict[str, Any] = Field(default_factory=dict)


class NotebookProjectionRequest(BaseModel):
    notebookRun: Dict[str, Any]
    workspaceKey: str = "notebook-visual-workspace"
    title: str = "Notebook Visual Workspace"
    projectEntityId: str = "workbench-notebook"


class CoreVisualWorkspacePlanRequest(BaseModel):
    visualWorkspace: Dict[str, Any]
    coreSessionId: str = ""
    coreExecutionId: str = ""
    visibility: Literal["private", "workspace", "public"] = "workspace"


def _normalize_view(view: ScientificViewSpec) -> Dict[str, Any]:
    data = deepcopy(view.data)
    summary: Dict[str, Any] = {}
    if view.kind in {"line", "scatter", "trajectory", "pareto", "convergence"}:
        xs = _numeric_list(data.get("x", []), "x")
        ys = _numeric_list(data.get("y", []), "y")
        if not ys:
            raise ValueError(f"{view.kind} requires y values")
        if not xs:
            xs = [float(i) for i in range(len(ys))]
        if len(xs) != len(ys):
            raise ValueError("x and y arrays must have equal length")
        data["x"], data["y"] = xs, ys
        summary = {"pointCount": len(ys), "xMin": min(xs), "xMax": max(xs), "yMin": min(ys), "yMax": max(ys)}
    elif view.kind == "uncertainty-band":
        xs = _numeric_list(data.get("x", []), "x")
        center = _numeric_list(data.get("center", []), "center")
        lower = _numeric_list(data.get("lower", []), "lower")
        upper = _numeric_list(data.get("upper", []), "upper")
        if not center or len({len(xs), len(center), len(lower), len(upper)}) != 1:
            raise ValueError("uncertainty-band requires equal non-empty x/center/lower/upper arrays")
        if any(lo > hi for lo, hi in zip(lower, upper)):
            raise ValueError("uncertainty-band lower values must be <= upper values")
        data.update({"x": xs, "center": center, "lower": lower, "upper": upper})
        summary = {"pointCount": len(center), "minLower": min(lower), "maxUpper": max(upper)}
    elif view.kind == "distribution":
        values = _numeric_list(data.get("values", []), "values")
        if not values:
            raise ValueError("distribution requires values")
        data["values"] = values
        summary = {"sampleCount": len(values), "min": min(values), "max": max(values), "mean": sum(values)/len(values)}
    elif view.kind == "heatmap":
        matrix = data.get("matrix")
        if not isinstance(matrix, list) or not matrix or len(matrix) > 500:
            raise ValueError("heatmap requires a non-empty bounded matrix")
        widths = {len(row) for row in matrix if isinstance(row, list)}
        if len(widths) != 1 or not widths or max(widths) > 500:
            raise ValueError("heatmap matrix rows must have equal bounded width")
        for row in matrix:
            _numeric_list(row, "matrix row")
        summary = {"rows": len(matrix), "columns": next(iter(widths))}
    elif view.kind == "table":
        rows = data.get("rows")
        if not isinstance(rows, list) or len(rows) > 5000:
            raise ValueError("table requires a bounded rows array")
        summary = {"rowCount": len(rows)}
    elif view.kind == "scalar":
        if "value" not in data:
            raise ValueError("scalar requires value")
        summary = {"value": data.get("value")}
    out = {
        "schema": VIEW_SCHEMA,
        "version": VERSION,
        "viewId": view.viewId,
        "kind": view.kind,
        "title": view.title,
        "data": data,
        "summary": summary,
        "sourceRef": view.sourceRef or None,
        "executionObjectRef": view.executionObjectRef or None,
        "unit": view.unit or None,
        "purpose": view.purpose,
        "linkGroups": view.linkGroups,
        "metadata": view.metadata,
        "rendererNeutral": True,
    }
    out["viewHash"] = content_hash(out)
    return out


def build_workspace(spec: VisualWorkspaceSpec) -> Dict[str, Any]:
    views = [_normalize_view(v) for v in spec.views]
    out: Dict[str, Any] = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "workspaceKey": spec.workspaceKey,
        "workspaceRef": f"sc://workbench/visual-workspace/{content_hash({'workspaceKey': spec.workspaceKey, 'views': views})[:32]}",
        "title": spec.title,
        "projectEntityId": spec.projectEntityId,
        "views": views,
        "controls": [c.model_dump(mode="json") for c in spec.controls],
        "links": [l.model_dump(mode="json") for l in spec.links],
        "sourceNotebookRunHash": spec.sourceNotebookRunHash or None,
        "sourceWorkflowGraphRunHash": spec.sourceWorkflowGraphRunHash or None,
        "metadata": spec.metadata,
        "linkedViewsEnabled": bool(spec.links),
        "controlsExecuteAutomatically": False,
        "rendererExecutionByPlatformCore": False,
        "automaticCoreDispatchAuthorized": False,
        "scientificValidityCertified": False,
    }
    out["visualWorkspaceHash"] = content_hash(out)
    return out


def validate_workspace(workspace: Dict[str, Any]) -> Dict[str, Any]:
    given = workspace.get("visualWorkspaceHash")
    candidate = deepcopy(workspace)
    candidate.pop("visualWorkspaceHash", None)
    expected = content_hash(candidate)
    valid = bool(given) and given == expected and workspace.get("schema") == SCHEMA
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "valid": valid, "expectedHash": expected, "providedHash": given}


def apply_linked_state(req: LinkedStateRequest) -> Dict[str, Any]:
    check = validate_workspace(req.visualWorkspace)
    if not check["valid"]:
        raise ValueError("visualWorkspace integrity validation failed")
    views = {v.get("viewId") for v in req.visualWorkspace.get("views", [])}
    if req.sourceViewId not in views:
        raise ValueError("sourceViewId is not present in workspace")
    affected = []
    for link in req.visualWorkspace.get("links", []):
        if link.get("sourceViewId") == req.sourceViewId:
            affected.append({"targetViewId": link.get("targetViewId"), "relation": link.get("relation"), "sourceField": link.get("sourceField"), "targetField": link.get("targetField")})
    out = {"ok": True, "schema": STATE_SCHEMA, "version": VERSION, "workspaceHash": req.visualWorkspace.get("visualWorkspaceHash"), "sourceViewId": req.sourceViewId,
           "selection": req.selection, "filter": req.filter, "cursor": req.cursor, "affectedViews": affected, "linkedStateAppliedByRenderer": False, "recomputationPerformed": False}
    out["stateHash"] = content_hash(out)
    return out


def control_plan(req: ControlPlanRequest) -> Dict[str, Any]:
    check = validate_workspace(req.visualWorkspace)
    if not check["valid"]:
        raise ValueError("visualWorkspace integrity validation failed")
    controls = {c.get("controlId"): c for c in req.visualWorkspace.get("controls", [])}
    control = controls.get(req.controlId)
    if not control:
        raise ValueError("controlId is not present in workspace")
    if isinstance(req.value, (int, float)):
        if control.get("minimum") is not None and req.value < control["minimum"]: raise ValueError("control value is below minimum")
        if control.get("maximum") is not None and req.value > control["maximum"]: raise ValueError("control value is above maximum")
    mutated = deepcopy(req.runtimeRequest)
    _set_path(mutated, control["targetPath"], req.value)
    out = {"ok": True, "schema": CONTROL_PLAN_SCHEMA, "version": VERSION, "workspaceHash": req.visualWorkspace.get("visualWorkspaceHash"), "controlId": req.controlId,
           "value": req.value, "targetRuntimePath": control.get("targetRuntimePath") or None, "preparedRuntimeRequest": mutated, "executionPerformed": False, "automaticDispatchAuthorized": False}
    out["planHash"] = content_hash(out)
    return out


def notebook_projection(req: NotebookProjectionRequest) -> Dict[str, Any]:
    run = req.notebookRun
    if not run.get("notebookRunHash"):
        raise ValueError("notebookRun must contain notebookRunHash")
    views: List[ScientificViewSpec] = []
    for cell in run.get("cellRuns", []):
        if not cell.get("ok") or cell.get("cellType") == "markdown":
            continue
        result = cell.get("result")
        if not isinstance(result, dict):
            continue
        data: Dict[str, Any] = {}
        kind: ViewKind = "scalar"
        if isinstance(result.get("x"), list) and isinstance(result.get("y"), list):
            kind, data = "line", {"x": result["x"], "y": result["y"]}
        elif isinstance(result.get("trajectory"), list) and result.get("trajectory"):
            traj = result["trajectory"]
            xs = [p.get("time", i) for i,p in enumerate(traj) if isinstance(p, dict)]
            ys = [p.get("value", p.get("state", [None])[0] if isinstance(p.get("state"), list) and p.get("state") else None) for p in traj if isinstance(p, dict)]
            if ys and all(isinstance(v,(int,float)) for v in ys): kind, data = "trajectory", {"x": xs, "y": ys}
            else: continue
        elif isinstance(result.get("values"), list) and result.get("values"):
            kind, data = "distribution", {"values": result["values"]}
        elif isinstance(result.get("matrix"), list) and result.get("matrix"):
            kind, data = "heatmap", {"matrix": result["matrix"]}
        elif isinstance(result.get("rows"), list):
            kind, data = "table", {"rows": result["rows"]}
        else:
            numeric = next(((k,v) for k,v in result.items() if isinstance(v,(int,float))), None)
            if not numeric: continue
            kind, data = "scalar", {"value": numeric[1], "metric": numeric[0]}
        views.append(ScientificViewSpec(viewId=f"cell-{cell.get('cellId')}", kind=kind, title=cell.get("cellId") or "Notebook cell", data=data, sourceRef=run.get("notebookRef", ""), executionObjectRef=(cell.get("executionObject") or {}).get("objectRef", "")))
        if len(views) >= MAX_VIEWS: break
    if not views:
        raise ValueError("notebookRun contains no automatically projectable scientific results")
    spec = VisualWorkspaceSpec(workspaceKey=req.workspaceKey,title=req.title,projectEntityId=req.projectEntityId,views=views,sourceNotebookRunHash=run["notebookRunHash"])
    return build_workspace(spec)


def _core_data_for_view(view: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    kind = view.get("kind"); data = dict(view.get("data") or {})
    if kind in {"line","trajectory","convergence"}: return "series", {"x":data.get("x",[]),"y":data.get("y",[])}
    if kind in {"scatter","pareto"}: return "scatter", {"x":data.get("x",[]),"y":data.get("y",[])}
    if kind == "distribution": return "distribution", {"values":data.get("values",[])}
    if kind == "uncertainty-band": return "ensemble", {"outputs":{"center":data.get("center",[]),"lower":data.get("lower",[]),"upper":data.get("upper",[])}}
    if kind == "heatmap": return "matrix", {"matrix":data.get("matrix",[])}
    if kind == "table": return "table", {"rows":data.get("rows",[])}
    return "model-run", {"outputs":{"value":data.get("value")}}


def core_visual_plan(req: CoreVisualWorkspacePlanRequest) -> Dict[str, Any]:
    check = validate_workspace(req.visualWorkspace)
    if not check["valid"]:
        raise ValueError("visualWorkspace integrity validation failed")
    plans=[]
    for view in req.visualWorkspace.get("views", []):
        data_kind, core_data = _core_data_for_view(view)
        manifest = adapt_visual_result(VisualResultAdapterRequest(
            projectEntityId=req.visualWorkspace.get("projectEntityId"), title=view.get("title") or view.get("viewId"), dataKind=data_kind, data=core_data,
            reasoningPurpose=view.get("purpose","explore"), coordinateSpace="cartesian" if view.get("kind") not in {"table","scalar"} else "abstract",
            sourceRef=view.get("sourceRef") or req.visualWorkspace.get("workspaceRef"), sourceKind="workbench-visual-scientific-view", workbenchExecutionRef=view.get("executionObjectRef") or "",
            coreExecutionId=req.coreExecutionId, coreSessionId=req.coreSessionId, unit=view.get("unit") or "", metadata={"viewId":view.get("viewId"),"viewKind":view.get("kind"),"visualWorkspaceHash":req.visualWorkspace.get("visualWorkspaceHash")}
        ))
        object_plan = build_visual_object_plan(VisualObjectPlanRequest(manifest=manifest, visibility=req.visibility))
        plans.append({"viewId":view.get("viewId"),"visualManifest":manifest,"visualObjectRegistrationPlan":object_plan})
    out={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"visualWorkspaceHash":req.visualWorkspace.get("visualWorkspaceHash"),"viewPlans":plans,
         "coreSceneContract":CORE_SCENE_CONTRACT,"coreGrammarContract":CORE_GRAMMAR_CONTRACT,"coreLinkedViewsContract":CORE_LINKED_VIEWS_CONTRACT,"coreVisualQueryContract":CORE_VISUAL_QUERY_CONTRACT,"coreUnifiedVisualContract":CORE_UNIFIED_VISUAL_CONTRACT,
         "coreVisualEntityIdsMustComeFromCore":True,"coreSceneIdsMustComeFromCore":True,"coreGrammarIdsMustComeFromCore":True,"workbenchExecutesScientificComputation":True,"coreExecutesScientificComputation":False,
         "rendererExecutionByCore":False,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"scientificValidityCertified":False,"truthDetermined":False}
    out["planHash"]=content_hash(out); return out


def manifest() -> Dict[str, Any]:
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"viewKinds":["line","scatter","trajectory","uncertainty-band","distribution","heatmap","convergence","pareto","table","scalar"],
         "capabilities":{"rendererNeutralScientificViews":True,"linkedViews":True,"explicitCrossFiltering":True,"parameterControlPlanning":True,"notebookProjection":True,"coreVisualReasoningPlans":True,"uncertaintyViews":True,"designSpaceViews":True,"trajectoryViews":True,"convergenceViews":True},
         "coreContracts":{"scene":CORE_SCENE_CONTRACT,"grammar":CORE_GRAMMAR_CONTRACT,"linkedViews":CORE_LINKED_VIEWS_CONTRACT,"visualQuery":CORE_VISUAL_QUERY_CONTRACT,"unifiedVisual":CORE_UNIFIED_VISUAL_CONTRACT},
         "boundaries":{"controlsExecuteAutomatically":False,"hiddenDataflowAllowed":False,"rendererExecutionByCore":False,"automaticCoreDispatchAuthorized":False,"scientificValidityCertified":False}}
    out["manifestHash"]=content_hash(out); return out


@router.get("/visual-workspace/manifest")
def get_manifest(): return manifest()

@router.post("/visual-workspace/build")
def build_endpoint(req: WorkspaceBuildRequest):
    try: return build_workspace(req.workspace)
    except Exception as exc: raise HTTPException(status_code=422,detail=str(exc))

@router.post("/visual-workspace/validate")
def validate_endpoint(req: WorkspaceValidateRequest): return validate_workspace(req.visualWorkspace)

@router.post("/visual-workspace/linked-state/apply")
def linked_endpoint(req: LinkedStateRequest):
    try: return apply_linked_state(req)
    except Exception as exc: raise HTTPException(status_code=422,detail=str(exc))

@router.post("/visual-workspace/control/plan")
def control_endpoint(req: ControlPlanRequest):
    try: return control_plan(req)
    except Exception as exc: raise HTTPException(status_code=422,detail=str(exc))

@router.post("/visual-workspace/notebook/project")
def notebook_endpoint(req: NotebookProjectionRequest):
    try: return notebook_projection(req)
    except Exception as exc: raise HTTPException(status_code=422,detail=str(exc))

@router.post("/integration/core/visual-workspace/plan")
def core_plan_endpoint(req: CoreVisualWorkspacePlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token"), x_sc_gateway_service: str | None = Header(default=None, alias="X-SC-Gateway-Service"), x_sc_core_version: str | None = Header(default=None, alias="X-SC-Core-Version")):
    _authorize_core_route(x_sc_service_token)
    try: return core_visual_plan(req)
    except Exception as exc: raise HTTPException(status_code=422,detail=str(exc))

@router.get("/v7110/status")
def status():
    return {"ok":True,"version":VERSION,"release":"Visual Scientific Computing Workspace","schema":SCHEMA,"linkedViews":True,"parameterControls":True,"notebookProjection":True,"coreVisualReasoning":True,"controlsExecuteAutomatically":False,"rendererExecutionByCore":False,"automaticCoreDispatchAuthorized":False,"scientificValidityCertified":False}

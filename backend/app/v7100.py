"""Workbench v7.10.0 — Interactive Computational Notebook Runtime.

A content-addressed notebook layer over bounded Workbench runtimes. Executable
cells have explicit dependencies and bindings; there is no hidden interpreter
namespace, arbitrary code execution, or automatic Platform Core dispatch.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v790 import GraphBinding, WorkflowGraphNode, WorkflowGraphSpec, _execute_node, _get_path, _set_path, validate_graph

VERSION = APP_VERSION
SCHEMA = "sc-workbench-interactive-computational-notebook/1.0"
RUN_SCHEMA = "sc-workbench-interactive-computational-notebook-run/1.0"
VALIDATION_SCHEMA = "sc-workbench-interactive-computational-notebook-validation/1.0"
REPLAY_SCHEMA = "sc-workbench-interactive-computational-notebook-replay-plan/1.0"
GRAPH_PLAN_SCHEMA = "sc-workbench-notebook-workflow-graph-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-notebook-core-workflow-plan/1.0"
CORE_WORKFLOW_CONTRACT = "sc.research.workflow-orchestration.v1"
MAX_CELLS = 200
MAX_BINDINGS = 500

CellType = Literal[
    "markdown",
    "unified-operation",
    "solver",
    "simulation",
    "engineering",
    "design-space",
    "validation",
]

router = APIRouter(tags=["workbench-v7100-interactive-computational-notebook"])


class NotebookCell(BaseModel):
    cellId: str = Field(min_length=1, max_length=120)
    cellType: CellType
    action: str = Field(default="", max_length=120)
    source: str = Field(default="", max_length=20000)
    request: Dict[str, Any] = Field(default_factory=dict)
    dependsOn: List[str] = Field(default_factory=list, max_length=50)
    bindings: List[GraphBinding] = Field(default_factory=list, max_length=MAX_BINDINGS)
    label: str = Field(default="", max_length=400)
    tags: List[str] = Field(default_factory=list, max_length=50)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("dependsOn")
    @classmethod
    def unique_dependencies(cls, value: List[str]) -> List[str]:
        if len(value) != len(set(value)):
            raise ValueError("dependsOn values must be unique")
        return value

    @model_validator(mode="after")
    def markdown_is_non_executable(self):
        if self.cellType == "markdown" and (self.request or self.bindings):
            raise ValueError("markdown cells may not declare executable requests or result bindings")
        return self


class NotebookSpec(BaseModel):
    notebookKey: str = Field(default="computational-notebook", min_length=1, max_length=180)
    title: str = Field(default="", max_length=400)
    cells: List[NotebookCell] = Field(min_length=1, max_length=MAX_CELLS)
    stopOnFailure: bool = True
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    datasetRefs: List[str] = Field(default_factory=list, max_length=100)
    methodRefs: List[str] = Field(default_factory=list, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_cells(self):
        ids = [c.cellId for c in self.cells]
        if len(ids) != len(set(ids)):
            raise ValueError("notebook cellId values must be unique")
        known = set(ids)
        for cell in self.cells:
            if cell.cellId in cell.dependsOn:
                raise ValueError(f"cell {cell.cellId} may not depend on itself")
            missing = sorted(set(cell.dependsOn) - known)
            if missing:
                raise ValueError(f"cell {cell.cellId} depends on unknown cells: {', '.join(missing)}")
            for binding in cell.bindings:
                if binding.sourceNodeId not in known:
                    raise ValueError(f"binding source cell does not exist: {binding.sourceNodeId}")
                if binding.sourceNodeId not in cell.dependsOn:
                    raise ValueError(f"cell {cell.cellId} binding source {binding.sourceNodeId} must be declared in dependsOn")
        return self


class NotebookRunRequest(BaseModel):
    notebook: NotebookSpec
    requestKey: str = Field(default="", max_length=180)


class NotebookRunValidationRequest(BaseModel):
    notebookRun: Dict[str, Any]


class ReplayPlanRequest(BaseModel):
    notebookRun: Dict[str, Any]


class CoreNotebookPlanRequest(BaseModel):
    notebookRun: Dict[str, Any]
    coreWorkflowId: str = Field(default="", max_length=128)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _graph_spec(notebook: NotebookSpec) -> WorkflowGraphSpec:
    nodes=[]
    for c in notebook.cells:
        if c.cellType == "markdown":
            continue
        nodes.append(WorkflowGraphNode(
            nodeId=c.cellId, nodeType=c.cellType, action=c.action,
            request=c.request, dependsOn=[d for d in c.dependsOn if next(x for x in notebook.cells if x.cellId==d).cellType != "markdown"],
            bindings=c.bindings, label=c.label, metadata={**c.metadata, "notebookCellId": c.cellId},
        ))
    if not nodes:
        # graph model requires one executable node; notebook validation handles markdown-only separately
        raise ValueError("notebook has no executable cells")
    return WorkflowGraphSpec(
        graphKey=f"notebook:{notebook.notebookKey}", title=notebook.title, nodes=nodes,
        stopOnFailure=notebook.stopOnFailure, projectRef=notebook.projectRef,
        coreSessionId=notebook.coreSessionId, datasetRefs=notebook.datasetRefs,
        methodRefs=notebook.methodRefs, tags=notebook.tags, metadata={**notebook.metadata, "notebookKey": notebook.notebookKey},
    )


def _dependency_order(notebook: NotebookSpec) -> List[str]:
    ids=[c.cellId for c in notebook.cells]
    indegree={c.cellId:len(set(c.dependsOn)) for c in notebook.cells}
    children={c.cellId:[] for c in notebook.cells}
    for c in notebook.cells:
        for dep in c.dependsOn: children[dep].append(c.cellId)
    pos={cid:i for i,cid in enumerate(ids)}
    queue=[cid for cid in ids if indegree[cid]==0]
    order=[]
    while queue:
        queue.sort(key=pos.get); cid=queue.pop(0); order.append(cid)
        for child in children[cid]:
            indegree[child]-=1
            if indegree[child]==0: queue.append(child)
    if len(order)!=len(ids):
        raise ValueError("notebook dependency cycle detected")
    return order


def validate_notebook(notebook: NotebookSpec) -> Dict[str, Any]:
    reasons=[]
    try: order=_dependency_order(notebook)
    except ValueError as exc: order=[]; reasons=[str(exc)]
    record={
        "ok": not reasons, "schema": VALIDATION_SCHEMA, "version": VERSION,
        "notebookKey": notebook.notebookKey, "notebookHash": content_hash(notebook.model_dump()),
        "cellCount": len(notebook.cells), "executableCellCount": sum(c.cellType!='markdown' for c in notebook.cells),
        "dependencyOrder": order, "bindingCount": sum(len(c.bindings) for c in notebook.cells), "reasons": reasons,
        "hiddenInterpreterStateAllowed": False, "explicitBindingsOnly": True, "arbitraryCodeExecutionAuthorized": False,
    }
    record["validationHash"]=content_hash(record)
    return record


def run_notebook(req: NotebookRunRequest) -> Dict[str, Any]:
    nb=req.notebook; validation=validate_notebook(nb)
    if not validation["ok"]: raise HTTPException(status_code=422, detail=validation["reasons"])
    by_id={c.cellId:c for c in nb.cells}; outputs={}; runs=[]; failed=None
    graph_context=WorkflowGraphSpec(graphKey=f"notebook:{nb.notebookKey}", title=nb.title,
        nodes=[WorkflowGraphNode(nodeId="placeholder",nodeType="unified-operation",request={"operation":"math.simplify","payload":{"expression":"1"}})],
        projectRef=nb.projectRef, coreSessionId=nb.coreSessionId, datasetRefs=nb.datasetRefs, methodRefs=nb.methodRefs, tags=nb.tags,
        metadata={**nb.metadata,"notebookKey":nb.notebookKey})
    for cid in validation["dependencyOrder"]:
        cell=by_id[cid]
        blocked=[d for d in cell.dependsOn if not outputs.get(d,{}).get("ok",False)]
        if blocked:
            run={"ok":False,"cellId":cid,"cellType":cell.cellType,"status":"blocked","blockedBy":blocked}; outputs[cid]=run; runs.append(run); failed=failed or cid
            if nb.stopOnFailure: break
            continue
        if cell.cellType=="markdown":
            run={"ok":True,"cellId":cid,"cellType":"markdown","status":"descriptive","sourceHash":content_hash(cell.source),"result":{"rendered":False,"sourceHash":content_hash(cell.source)}}
            outputs[cid]=run; runs.append(run); continue
        prepared=deepcopy(cell.request); applied=[]
        try:
            for b in cell.bindings:
                source=outputs.get(b.sourceNodeId)
                if not source: raise ValueError(f"source cell has no run result: {b.sourceNodeId}")
                try: value=_get_path(source["result"],b.sourcePath)
                except ValueError:
                    if b.required: raise
                    continue
                _set_path(prepared,b.targetPath,value)
                applied.append({"sourceCellId":b.sourceNodeId,"sourcePath":b.sourcePath,"targetPath":b.targetPath,"valueHash":content_hash(value)})
            node=WorkflowGraphNode(nodeId=cid,nodeType=cell.cellType,action=cell.action,request=prepared,dependsOn=[],bindings=[],label=cell.label,metadata={**cell.metadata,"notebookCellId":cid})
            executed=_execute_node(node,prepared,graph_context); result=executed["result"]
            ok=bool(result.get("ok",True)) if isinstance(result,dict) else True
            run={"ok":ok,"cellId":cid,"cellType":cell.cellType,"action":cell.action,"status":"completed" if ok else "failed",
                 "dependsOn":cell.dependsOn,"appliedBindings":applied,"preparedRequestHash":content_hash(prepared),"result":result,
                 "resultHash":content_hash(result),"executionObject":executed.get("executionObject")}
        except (ValueError,HTTPException) as exc:
            run={"ok":False,"cellId":cid,"cellType":cell.cellType,"status":"failed","dependsOn":cell.dependsOn,"appliedBindings":applied,"error":exc.detail if isinstance(exc,HTTPException) else str(exc)}
        outputs[cid]=run; runs.append(run)
        if not run["ok"]:
            failed=failed or cid
            if nb.stopOnFailure: break
    record={"ok":failed is None,"schema":RUN_SCHEMA,"version":VERSION,"notebookKey":nb.notebookKey,
            "notebookRef":f"sc://workbench/notebook/{validation['notebookHash'][:32]}","notebookHash":validation["notebookHash"],
            "projectRef":nb.projectRef,"coreSessionId":nb.coreSessionId,"declaredCellCount":len(nb.cells),"executedCellCount":len(runs),
            "completedExecutableCellCount":sum(r.get("status")=="completed" for r in runs),"failedCellId":failed,"cellRuns":runs,
            "hiddenInterpreterStateUsed":False,"automaticResultSubstitutionPerformed":False,"automaticCoreDispatchPerformed":False,"automaticCorePersistencePerformed":False}
    record["notebookRunHash"]=content_hash({k:v for k,v in record.items() if k!="notebookRunHash"})
    return record


def validate_run(run: Dict[str,Any]) -> Dict[str,Any]:
    declared=run.get("notebookRunHash","")
    calculated=content_hash({k:v for k,v in run.items() if k!="notebookRunHash"})
    return {"ok":True,"schema":"sc-workbench-notebook-run-integrity/1.0","version":VERSION,"valid":bool(declared) and declared==calculated,
            "declaredHash":declared,"calculatedHash":calculated,"hiddenInterpreterStateCertified":False}


def replay_plan(run: Dict[str,Any]) -> Dict[str,Any]:
    cells=[]
    for r in run.get("cellRuns",[]):
        if r.get("cellType")=="markdown": continue
        cells.append({"cellId":r.get("cellId"),"cellType":r.get("cellType"),"preparedRequestHash":r.get("preparedRequestHash"),"resultHash":r.get("resultHash"),
                      "executionObjectHash":(r.get("executionObject") or {}).get("objectHash")})
    out={"ok":True,"schema":REPLAY_SCHEMA,"version":VERSION,"notebookKey":run.get("notebookKey"),"notebookHash":run.get("notebookHash"),
         "sourceNotebookRunHash":run.get("notebookRunHash"),"cells":cells,"replayPerformed":False,"environmentMustBeReestablished":True,
         "hiddenStateReplayAuthorized":False,"automaticCoreDispatchAuthorized":False}
    out["planHash"]=content_hash(out); return out


def workflow_graph_plan(nb: NotebookSpec) -> Dict[str,Any]:
    graph=_graph_spec(nb); gv=validate_graph(graph)
    if not gv["ok"]: raise HTTPException(status_code=422,detail=gv["reasons"])
    out={"ok":True,"schema":GRAPH_PLAN_SCHEMA,"version":VERSION,"notebookKey":nb.notebookKey,"notebookHash":content_hash(nb.model_dump()),
         "graph":graph.model_dump(),"graphHash":gv["graphHash"],"dependencyOrder":gv["dependencyOrder"],"executionPerformed":False,
         "markdownCellsExcludedFromExecutionGraph":True,"automaticCoreDispatchAuthorized":False}
    out["planHash"]=content_hash(out); return out


def core_plan(req: CoreNotebookPlanRequest) -> Dict[str,Any]:
    run=req.notebookRun
    if run.get("schema")!=RUN_SCHEMA: raise HTTPException(status_code=422,detail="notebookRun schema mismatch")
    create={"workflow_key":run.get("notebookKey") or "workbench-notebook","workflow_type":"analysis","status":"completed" if run.get("ok") else "failed",
            "title":run.get("notebookKey") or "Workbench computational notebook","visibility":req.visibility,"project_ref":run.get("projectRef") or None,
            "session_id":run.get("coreSessionId") or None,"metadata":{"workbenchVersion":VERSION,"notebookHash":run.get("notebookHash"),"notebookRunHash":run.get("notebookRunHash")},"created_by":req.createdBy}
    stages=[];bindings=[];events=[]
    if req.coreWorkflowId:
        ordinal=0
        for cr in run.get("cellRuns",[]):
            if cr.get("cellType")=="markdown": continue
            ordinal+=1; cid=cr.get("cellId"); obj=cr.get("executionObject") or {}; status="completed" if cr.get("ok") else "failed"; ref=obj.get("objectRef") or f"{run.get('notebookRef')}/cell/{cid}"
            stages.append({"method":"POST","path":f"/v1/research/workflows/{req.coreWorkflowId}/stages","data":{"stage_key":cid,"stage_type":"analysis","ordinal":ordinal,"status":status,"responsible_product":"workbench","object_ref":ref,"created_by":req.createdBy}})
            bindings.append({"method":"POST","path":f"/v1/research/workflows/{req.coreWorkflowId}/context-bindings","data":{"binding_key":f"notebook-cell-{ordinal}","stage_key":cid,"product_key":"workbench","object_type":"execution" if obj else "notebook-cell-result","object_ref":ref,"relation":"computational_notebook_cell","context":{"resultHash":cr.get("resultHash"),"executionObjectHash":obj.get("objectHash")},"created_by":req.createdBy}})
            if status=="completed": events.append({"method":"POST","path":f"/v1/research/workflows/{req.coreWorkflowId}/events","data":{"event_key":f"notebook-cell-completed-{ordinal}","event_type":"stage_completed","stage_key":cid,"actor_ref":"product:workbench","details":{"resultHash":cr.get("resultHash"),"declaredByWorkbench":True},"created_by":req.createdBy}})
    out={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"coreWorkflowContract":CORE_WORKFLOW_CONTRACT,"coreWorkflowIdProvided":bool(req.coreWorkflowId),"coreWorkflowIdMustComeFromCore":not bool(req.coreWorkflowId),
         "workflowRegistration":{"method":"POST","path":"/v1/research/workflows","data":create},"stageRegistrations":stages,"contextBindings":bindings,"eventRegistrations":events,
         "coreExecutesNotebookCells":False,"coreInfersNotebookResults":False,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"scientificValidityCertified":False,"truthDetermined":False}
    out["planHash"]=content_hash(out); return out


def manifest():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"cellTypes":["markdown","unified-operation","solver","simulation","engineering","design-space","validation"],
            "capabilities":{"typedNotebookCells":True,"explicitCellDependencies":True,"explicitResultBindings":True,"contentAddressedNotebookRuns":True,"replayPlanning":True,"workflowGraphProjection":True,"coreWorkflowPlanning":True},
            "boundaries":{"hiddenInterpreterStateAllowed":False,"arbitraryCodeExecutionAuthorized":False,"automaticCoreDispatchAuthorized":False,"scientificValidityCertified":False}}


@router.get("/notebooks/manifest")
def manifest_route(): return manifest()

@router.post("/notebooks/validate")
def validate_route(notebook: NotebookSpec): return validate_notebook(notebook)

@router.post("/notebooks/run")
def run_route(req: NotebookRunRequest): return run_notebook(req)

@router.post("/notebooks/run/validate")
def run_validate_route(req: NotebookRunValidationRequest): return validate_run(req.notebookRun)

@router.post("/notebooks/replay/plan")
def replay_route(req: ReplayPlanRequest): return replay_plan(req.notebookRun)

@router.post("/notebooks/workflow-graph/plan")
def graph_plan_route(notebook: NotebookSpec): return workflow_graph_plan(notebook)

@router.post("/integration/core/notebook-workflow/plan")
def core_plan_route(req: CoreNotebookPlanRequest, x_sc_service_token: str|None=Header(default=None,alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token); return core_plan(req)

@router.get("/v7100/status")
def status_route():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":"Interactive Computational Notebook Runtime","typedCells":True,"explicitDependencies":True,"hiddenInterpreterState":False,"replayPlanning":True,"workflowGraphProjection":True,"automaticCoreDispatch":False}

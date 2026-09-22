"""Workbench v7.9.0 — Scientific Workflow Graph.

Content-addressed, dependency-aware scientific workflow DAGs over bounded
Workbench runtimes. Graphs use explicit typed nodes and declared bindings;
there is no hidden output substitution, arbitrary code execution, or automatic
Platform Core dispatch/persistence.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from .release import APP_VERSION, PRODUCT_KEY
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v700 import UnifiedExecutionRequest, _execute_request
from .v710 import _execution_object_from_result
from .v740 import SolverRequest, solve as solve_numerical
from .v750 import SimulationRequest, run_simulation
from .v760 import EngineeringAnalysisRequest, analyze as engineering_analyze
from .v770 import (
    ExplorationRequest,
    OptimizationRequest,
    PointEvaluationRequest,
    evaluate_point,
    explore,
    optimize,
    pareto_frontier,
)
from .v780 import (
    BenchmarkEvaluationRequest,
    ConvergenceEvaluationRequest,
    DatasetComparisonRequest,
    VVReportRequest,
    benchmark_evaluate,
    build_report,
    convergence_evaluate,
    dataset_compare,
)

VERSION = APP_VERSION
SCHEMA = "sc-workbench-scientific-workflow-graph/1.0"
PLAN_SCHEMA = "sc-workbench-scientific-workflow-graph-plan/1.0"
RUN_SCHEMA = "sc-workbench-scientific-workflow-graph-run/1.0"
VALIDATION_SCHEMA = "sc-workbench-scientific-workflow-graph-validation/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-scientific-workflow-graph-core-plan/1.0"
GRAPH_REF = "workbench:/runtime/scientific-workflow-graph"
CORE_WORKFLOW_CONTRACT = "sc.research.workflow-orchestration.v1"
MAX_NODES = 100
MAX_BINDINGS = 300
MAX_PATH_LENGTH = 600

NodeType = Literal[
    "unified-operation",
    "solver",
    "simulation",
    "engineering",
    "design-space",
    "validation",
]

router = APIRouter(tags=["workbench-v790-scientific-workflow-graph"])


class GraphBinding(BaseModel):
    sourceNodeId: str = Field(min_length=1, max_length=120)
    sourcePath: str = Field(min_length=1, max_length=MAX_PATH_LENGTH)
    targetPath: str = Field(min_length=1, max_length=MAX_PATH_LENGTH)
    required: bool = True


class WorkflowGraphNode(BaseModel):
    nodeId: str = Field(min_length=1, max_length=120)
    nodeType: NodeType
    action: str = Field(default="", max_length=120)
    request: Dict[str, Any] = Field(default_factory=dict)
    dependsOn: List[str] = Field(default_factory=list, max_length=50)
    bindings: List[GraphBinding] = Field(default_factory=list, max_length=MAX_BINDINGS)
    label: str = Field(default="", max_length=400)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("dependsOn")
    @classmethod
    def unique_dependencies(cls, value: List[str]) -> List[str]:
        if len(value) != len(set(value)):
            raise ValueError("dependsOn values must be unique")
        return value


class WorkflowGraphSpec(BaseModel):
    graphKey: str = Field(default="scientific-workflow", min_length=1, max_length=180)
    title: str = Field(default="", max_length=400)
    nodes: List[WorkflowGraphNode] = Field(min_length=1, max_length=MAX_NODES)
    stopOnFailure: bool = True
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    datasetRefs: List[str] = Field(default_factory=list, max_length=100)
    methodRefs: List[str] = Field(default_factory=list, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_graph_shape(self):
        ids = [n.nodeId for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("workflow nodeId values must be unique")
        known = set(ids)
        for node in self.nodes:
            if node.nodeId in node.dependsOn:
                raise ValueError(f"node {node.nodeId} may not depend on itself")
            unknown = sorted(set(node.dependsOn) - known)
            if unknown:
                raise ValueError(f"node {node.nodeId} depends on unknown nodes: {', '.join(unknown)}")
            for binding in node.bindings:
                if binding.sourceNodeId not in known:
                    raise ValueError(f"binding source node does not exist: {binding.sourceNodeId}")
                if binding.sourceNodeId not in node.dependsOn:
                    raise ValueError(
                        f"node {node.nodeId} binding source {binding.sourceNodeId} must be declared in dependsOn"
                    )
        return self


class GraphRunRequest(BaseModel):
    graph: WorkflowGraphSpec
    requestKey: str = Field(default="", max_length=180)


class GraphResultValidationRequest(BaseModel):
    graphRun: Dict[str, Any]


class CoreWorkflowPlanRequest(BaseModel):
    graphRun: Dict[str, Any]
    coreWorkflowId: str = Field(default="", max_length=128)
    workflowType: Literal["analysis", "experiment", "simulation", "engineering", "mixed"] = "analysis"
    visibility: Literal["private", "internal", "public"] = "internal"
    protocolRef: str = Field(default="", max_length=1000)
    programRef: str = Field(default="", max_length=1000)
    createdBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if not part:
            raise ValueError("path contains an empty component")
        if isinstance(current, dict):
            if part not in current:
                raise ValueError(f"path component not found: {part}")
            current = current[part]
        elif isinstance(current, list):
            try:
                index = int(part)
            except ValueError as exc:
                raise ValueError(f"list path component must be an integer: {part}") from exc
            if index < 0 or index >= len(current):
                raise ValueError(f"list index out of range: {index}")
            current = current[index]
        else:
            raise ValueError(f"cannot descend through path component: {part}")
    return current


def _set_path(target: Dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    if any(not p for p in parts):
        raise ValueError("targetPath contains an empty component")
    current: Any = target
    for part in parts[:-1]:
        if isinstance(current, dict):
            if part not in current:
                current[part] = {}
            if not isinstance(current[part], dict):
                raise ValueError(f"target path collides with non-object component: {part}")
            current = current[part]
        else:
            raise ValueError(f"cannot descend through target path component: {part}")
    if not isinstance(current, dict):
        raise ValueError("target path parent must be an object")
    current[parts[-1]] = deepcopy(value)


def _topological_order(graph: WorkflowGraphSpec) -> List[WorkflowGraphNode]:
    by_id = {n.nodeId: n for n in graph.nodes}
    indegree = {n.nodeId: len(set(n.dependsOn)) for n in graph.nodes}
    children: Dict[str, List[str]] = {n.nodeId: [] for n in graph.nodes}
    for node in graph.nodes:
        for dep in node.dependsOn:
            children[dep].append(node.nodeId)
    queue = sorted([node_id for node_id, degree in indegree.items() if degree == 0])
    ordered: List[WorkflowGraphNode] = []
    while queue:
        node_id = queue.pop(0)
        ordered.append(by_id[node_id])
        for child in sorted(children[node_id]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
                queue.sort()
    if len(ordered) != len(graph.nodes):
        cyclic = sorted(node_id for node_id, degree in indegree.items() if degree > 0)
        raise ValueError("workflow graph dependency cycle detected: " + ", ".join(cyclic))
    return ordered


def _graph_hash(graph: WorkflowGraphSpec) -> str:
    return content_hash(graph.model_dump())


def validate_graph(graph: WorkflowGraphSpec) -> Dict[str, Any]:
    try:
        ordered = _topological_order(graph)
        reasons: List[str] = []
    except ValueError as exc:
        ordered = []
        reasons = [str(exc)]
    record = {
        "ok": not reasons,
        "schema": VALIDATION_SCHEMA,
        "version": VERSION,
        "graphKey": graph.graphKey,
        "graphHash": _graph_hash(graph),
        "nodeCount": len(graph.nodes),
        "dependencyOrder": [n.nodeId for n in ordered],
        "bindingCount": sum(len(n.bindings) for n in graph.nodes),
        "reasons": reasons,
        "acyclic": not reasons,
        "explicitBindingOnly": True,
        "hiddenOutputSubstitutionPerformed": False,
        "arbitraryCodeExecutionAuthorized": False,
    }
    record["validationHash"] = content_hash(record)
    return record


def plan_graph(graph: WorkflowGraphSpec) -> Dict[str, Any]:
    validation = validate_graph(graph)
    if not validation["ok"]:
        raise HTTPException(status_code=422, detail=validation["reasons"])
    nodes = []
    by_id = {n.nodeId: n for n in graph.nodes}
    for node_id in validation["dependencyOrder"]:
        node = by_id[node_id]
        nodes.append({
            "nodeId": node.nodeId,
            "nodeType": node.nodeType,
            "action": node.action,
            "dependsOn": node.dependsOn,
            "bindings": [b.model_dump() for b in node.bindings],
            "requestHash": content_hash(node.request),
        })
    record = {
        "ok": True,
        "schema": PLAN_SCHEMA,
        "version": VERSION,
        "graphKey": graph.graphKey,
        "graphRef": f"sc://workbench/workflow-graph/{validation['graphHash'][:32]}",
        "graphHash": validation["graphHash"],
        "dependencyOrder": validation["dependencyOrder"],
        "nodes": nodes,
        "reusableGraph": True,
        "executionPerformed": False,
        "automaticCoreDispatchPerformed": False,
        "automaticCorePersistencePerformed": False,
    }
    record["planHash"] = content_hash(record)
    return record


def _with_common_context(node: WorkflowGraphNode, request: Dict[str, Any], graph: WorkflowGraphSpec) -> Dict[str, Any]:
    data = deepcopy(request)
    for field, value in (
        ("projectRef", graph.projectRef),
        ("coreSessionId", graph.coreSessionId),
    ):
        if value and field not in data:
            data[field] = value
    if "requestKey" not in data:
        data["requestKey"] = f"{graph.graphKey}:{node.nodeId}"
    if node.label and "label" not in data:
        data["label"] = node.label
    if "metadata" in data and isinstance(data["metadata"], dict):
        data["metadata"] = {**data["metadata"], "workflowGraphKey": graph.graphKey, "workflowNodeId": node.nodeId, **node.metadata}
    elif node.nodeType in {"unified-operation", "solver", "simulation", "engineering"}:
        data["metadata"] = {"workflowGraphKey": graph.graphKey, "workflowNodeId": node.nodeId, **node.metadata}
    return data


def _execute_node(node: WorkflowGraphNode, prepared: Dict[str, Any], graph: WorkflowGraphSpec) -> Dict[str, Any]:
    try:
        if node.nodeType == "unified-operation":
            result = _execute_request(UnifiedExecutionRequest.model_validate(_with_common_context(node, prepared, graph)))
            execution_object = _execution_object_from_result(
                result,
                declared_request={
                    "payload": prepared.get("payload", {}),
                    "inputRefs": prepared.get("inputRefs", []),
                    "requestKey": prepared.get("requestKey", f"{graph.graphKey}:{node.nodeId}"),
                    "metadata": node.metadata,
                },
                object_key=f"{graph.graphKey}:{node.nodeId}",
                label=node.label or node.nodeId,
                project_ref=graph.projectRef,
                core_session_id=graph.coreSessionId,
                dataset_refs=graph.datasetRefs,
                method_refs=graph.methodRefs,
                parent_refs=[],
                tags=graph.tags,
                metadata={"workflowGraphKey": graph.graphKey, "workflowNodeId": node.nodeId},
            )
            return {"result": result, "executionObject": execution_object}
        if node.nodeType == "solver":
            result = solve_numerical(SolverRequest.model_validate(_with_common_context(node, prepared, graph)))
            return {"result": result, "executionObject": result.get("executionObject")}
        if node.nodeType == "simulation":
            result = run_simulation(SimulationRequest.model_validate(_with_common_context(node, prepared, graph)))
            return {"result": result, "executionObject": result.get("executionObject")}
        if node.nodeType == "engineering":
            result = engineering_analyze(EngineeringAnalysisRequest.model_validate(_with_common_context(node, prepared, graph)))
            return {"result": result, "executionObject": result.get("executionObject")}
        if node.nodeType == "design-space":
            action = node.action or "optimize"
            if action == "optimize":
                result = optimize(OptimizationRequest.model_validate(prepared))
            elif action == "explore":
                result = explore(ExplorationRequest.model_validate(prepared))
            elif action == "evaluate":
                result = evaluate_point(PointEvaluationRequest.model_validate(prepared))
            elif action == "pareto":
                result = pareto_frontier(prepared.get("exploration", prepared))
            else:
                raise ValueError("design-space action must be optimize, explore, evaluate, or pareto")
            return {"result": result, "executionObject": result.get("executionObject") if isinstance(result, dict) else None}
        if node.nodeType == "validation":
            action = node.action or "report"
            if action == "benchmark":
                result = benchmark_evaluate(BenchmarkEvaluationRequest.model_validate(prepared))
            elif action == "dataset-compare":
                result = dataset_compare(DatasetComparisonRequest.model_validate(prepared))
            elif action == "convergence":
                result = convergence_evaluate(ConvergenceEvaluationRequest.model_validate(prepared))
            elif action == "report":
                result = build_report(VVReportRequest.model_validate(prepared))
            else:
                raise ValueError("validation action must be benchmark, dataset-compare, convergence, or report")
            return {"result": result, "executionObject": None}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"node {node.nodeId}: {exc}") from exc
    raise HTTPException(status_code=422, detail=f"unsupported node type: {node.nodeType}")


def run_graph(request: GraphRunRequest) -> Dict[str, Any]:
    graph = request.graph
    validation = validate_graph(graph)
    if not validation["ok"]:
        raise HTTPException(status_code=422, detail=validation["reasons"])
    by_id = {n.nodeId: n for n in graph.nodes}
    outputs: Dict[str, Dict[str, Any]] = {}
    node_runs: List[Dict[str, Any]] = []
    failed_node: Optional[str] = None

    for node_id in validation["dependencyOrder"]:
        node = by_id[node_id]
        blocked_by = [dep for dep in node.dependsOn if not outputs.get(dep, {}).get("ok", False)]
        if blocked_by:
            run = {
                "ok": False,
                "nodeId": node.nodeId,
                "nodeType": node.nodeType,
                "status": "blocked",
                "blockedBy": blocked_by,
                "dependsOn": node.dependsOn,
            }
            outputs[node.nodeId] = run
            node_runs.append(run)
            failed_node = failed_node or node.nodeId
            if graph.stopOnFailure:
                break
            continue

        prepared = deepcopy(node.request)
        applied_bindings = []
        try:
            for binding in node.bindings:
                source_run = outputs.get(binding.sourceNodeId)
                if not source_run:
                    raise ValueError(f"source node has no run result: {binding.sourceNodeId}")
                try:
                    value = _get_path(source_run["result"], binding.sourcePath)
                except ValueError:
                    if binding.required:
                        raise
                    continue
                _set_path(prepared, binding.targetPath, value)
                applied_bindings.append({
                    "sourceNodeId": binding.sourceNodeId,
                    "sourcePath": binding.sourcePath,
                    "targetPath": binding.targetPath,
                    "valueHash": content_hash(value),
                })
            executed = _execute_node(node, prepared, graph)
            result = executed["result"]
            ok = bool(result.get("ok", True)) if isinstance(result, dict) else True
            run = {
                "ok": ok,
                "nodeId": node.nodeId,
                "nodeType": node.nodeType,
                "action": node.action,
                "status": "completed" if ok else "failed",
                "dependsOn": node.dependsOn,
                "appliedBindings": applied_bindings,
                "preparedRequestHash": content_hash(prepared),
                "result": result,
                "resultHash": content_hash(result),
                "executionObject": executed.get("executionObject"),
            }
        except (ValueError, HTTPException) as exc:
            detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
            run = {
                "ok": False,
                "nodeId": node.nodeId,
                "nodeType": node.nodeType,
                "action": node.action,
                "status": "failed",
                "dependsOn": node.dependsOn,
                "appliedBindings": applied_bindings,
                "error": detail,
            }
        outputs[node.nodeId] = run
        node_runs.append(run)
        if not run["ok"]:
            failed_node = failed_node or node.nodeId
            if graph.stopOnFailure:
                break

    completed = sum(1 for run in node_runs if run.get("status") == "completed")
    record = {
        "ok": failed_node is None,
        "schema": RUN_SCHEMA,
        "version": VERSION,
        "graphKey": graph.graphKey,
        "graphRef": f"sc://workbench/workflow-graph/{validation['graphHash'][:32]}",
        "graphHash": validation["graphHash"],
        "projectRef": graph.projectRef,
        "coreSessionId": graph.coreSessionId,
        "declaredNodeCount": len(graph.nodes),
        "executedNodeCount": len(node_runs),
        "completedNodeCount": completed,
        "dependencyOrder": validation["dependencyOrder"],
        "failedNodeId": failed_node,
        "nodeRuns": node_runs,
        "nodeResultRefs": {
            run["nodeId"]: (run.get("executionObject") or {}).get("objectRef")
            for run in node_runs if (run.get("executionObject") or {}).get("objectRef")
        },
        "automaticOutputSubstitutionPerformed": False,
        "explicitDeclaredBindingsApplied": True,
        "automaticCoreDispatchPerformed": False,
        "automaticCorePersistencePerformed": False,
        "scientificValidityCertified": False,
        "truthDetermined": False,
    }
    record["graphRunHash"] = content_hash({
        "graphHash": record["graphHash"],
        "nodeResultHashes": [run.get("resultHash") for run in node_runs if run.get("resultHash")],
        "failedNodeId": failed_node,
    })
    return record


def validate_graph_run(graph_run: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    if graph_run.get("schema") != RUN_SCHEMA:
        reasons.append("schema-mismatch")
    if graph_run.get("version") != VERSION:
        reasons.append("version-mismatch")
    expected = content_hash({
        "graphHash": graph_run.get("graphHash"),
        "nodeResultHashes": [run.get("resultHash") for run in graph_run.get("nodeRuns", []) if isinstance(run, dict) and run.get("resultHash")],
        "failedNodeId": graph_run.get("failedNodeId"),
    })
    if graph_run.get("graphRunHash") != expected:
        reasons.append("graph-run-hash-mismatch")
    for run in graph_run.get("nodeRuns", []):
        if not isinstance(run, dict):
            reasons.append("node-run-not-object")
            continue
        if run.get("resultHash") and content_hash(run.get("result")) != run.get("resultHash"):
            reasons.append(f"node-result-hash-mismatch:{run.get('nodeId','unknown')}")
    record = {
        "ok": True,
        "schema": "sc-workbench-scientific-workflow-graph-run-validation/1.0",
        "version": VERSION,
        "valid": not reasons,
        "reasons": reasons,
        "graphRunHash": graph_run.get("graphRunHash"),
    }
    record["validationHash"] = content_hash(record)
    return record


def build_core_workflow_plan(request: CoreWorkflowPlanRequest) -> Dict[str, Any]:
    run = request.graphRun
    if run.get("schema") != RUN_SCHEMA or run.get("version") != VERSION:
        raise HTTPException(status_code=422, detail=f"graphRun must use {RUN_SCHEMA} version {VERSION}")
    if not validate_graph_run(run)["valid"]:
        raise HTTPException(status_code=422, detail="graphRun failed integrity validation")

    create_data = {
        "workflow_key": str(run.get("graphKey") or "workbench-scientific-workflow"),
        "title": str(run.get("graphKey") or "Workbench scientific workflow graph"),
        "workflow_type": request.workflowType,
        "status": "completed" if run.get("ok") else "paused",
        "visibility": request.visibility,
        "project_ref": run.get("projectRef") or None,
        "protocol_ref": request.protocolRef or None,
        "program_ref": request.programRef or None,
        "metadata": {
            "sourceProduct": PRODUCT_KEY,
            "sourceVersion": VERSION,
            "workflowGraphSchema": SCHEMA,
            "graphHash": run.get("graphHash"),
            "graphRunHash": run.get("graphRunHash"),
        },
        "provenance": {
            "graphRef": run.get("graphRef"),
            "nodeResultRefs": run.get("nodeResultRefs", {}),
        },
    }
    stages: List[Dict[str, Any]] = []
    bindings: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    if request.coreWorkflowId:
        for ordinal, node_run in enumerate(run.get("nodeRuns", []), start=1):
            node_id = str(node_run.get("nodeId") or f"node-{ordinal}")
            status = "completed" if node_run.get("status") == "completed" else "blocked"
            obj = node_run.get("executionObject") if isinstance(node_run.get("executionObject"), dict) else {}
            object_ref = obj.get("objectRef") or f"{run.get('graphRef')}/node/{node_id}"
            stages.append({
                "method": "POST",
                "path": f"/v1/research/workflows/{request.coreWorkflowId}/stages",
                "data": {
                    "stage_key": node_id,
                    "stage_type": "analysis",
                    "ordinal": ordinal,
                    "status": status,
                    "responsible_product": "workbench",
                    "object_ref": object_ref,
                    "entry_criteria": {"dependsOn": node_run.get("dependsOn", [])},
                    "exit_criteria": {"resultHash": node_run.get("resultHash"), "declaredByWorkbench": True},
                    "created_by": request.createdBy,
                },
            })
            bindings.append({
                "method": "POST",
                "path": f"/v1/research/workflows/{request.coreWorkflowId}/context-bindings",
                "data": {
                    "binding_key": f"workbench-node-{ordinal}",
                    "stage_key": node_id,
                    "product_key": "workbench",
                    "object_type": "execution" if obj else "workflow-node-result",
                    "object_ref": object_ref,
                    "relation": "scientific_workflow_node",
                    "context": {
                        "nodeType": node_run.get("nodeType"),
                        "resultHash": node_run.get("resultHash"),
                        "executionObjectHash": obj.get("objectHash"),
                    },
                    "created_by": request.createdBy,
                },
            })
            if status == "completed":
                events.append({
                    "method": "POST",
                    "path": f"/v1/research/workflows/{request.coreWorkflowId}/events",
                    "data": {
                        "event_key": f"workbench-node-completed-{ordinal}",
                        "event_type": "stage_completed",
                        "stage_key": node_id,
                        "actor_ref": "product:workbench",
                        "details": {"resultHash": node_run.get("resultHash"), "declaredByWorkbench": True},
                        "created_by": request.createdBy,
                    },
                })
    plan = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "coreWorkflowContract": CORE_WORKFLOW_CONTRACT,
        "coreWorkflowIdProvided": bool(request.coreWorkflowId),
        "coreWorkflowIdMustComeFromCore": not bool(request.coreWorkflowId),
        "workflowRegistration": {"method": "POST", "path": "/v1/research/workflows", "data": create_data},
        "stageRegistrations": stages,
        "contextBindings": bindings,
        "eventRegistrations": events,
        "nodeCount": len(run.get("nodeRuns", [])),
        "coreExecutesSpecialistWork": False,
        "coreInfersStageCompletion": False,
        "workbenchDeclaresItsOwnExecutionCompletion": True,
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "scientificValidityCertified": False,
        "truthDetermined": False,
    }
    plan["planHash"] = content_hash(plan)
    return plan


def manifest() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Scientific Workflow Graph",
        "runtimeRef": GRAPH_REF,
        "coreWorkflowContract": CORE_WORKFLOW_CONTRACT,
        "nodeTypes": ["unified-operation", "solver", "simulation", "engineering", "design-space", "validation"],
        "capabilities": {
            "typedScientificWorkflowNodes": True,
            "dependencyDirectedAcyclicGraphs": True,
            "deterministicTopologicalOrdering": True,
            "explicitResultBindings": True,
            "contentAddressedGraphPlans": True,
            "reusableWorkflowGraphs": True,
            "executionObjectLineage": True,
            "validationCheckpointNodes": True,
            "platformCoreWorkflowPlanning": True,
        },
        "boundaries": {
            "hiddenOutputSubstitution": False,
            "arbitraryCodeExecution": False,
            "automaticCoreDispatch": False,
            "automaticCorePersistence": False,
            "scientificValidityCertification": False,
            "truthDetermination": False,
        },
    }


@router.get("/workflow-graph/manifest")
def get_manifest():
    return manifest()


@router.post("/workflow-graph/validate")
def post_validate(graph: WorkflowGraphSpec):
    return validate_graph(graph)


@router.post("/workflow-graph/plan")
def post_plan(graph: WorkflowGraphSpec):
    return plan_graph(graph)


@router.post("/workflow-graph/run")
def post_run(request: GraphRunRequest):
    return run_graph(request)


@router.post("/workflow-graph/run/validate")
def post_run_validate(request: GraphResultValidationRequest):
    return validate_graph_run(request.graphRun)


@router.post("/integration/core/workflow-graph/plan")
def post_core_plan(
    request: CoreWorkflowPlanRequest,
    x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token"),
):
    _authorize_core_route(x_sc_service_token)
    return build_core_workflow_plan(request)


@router.get("/v790/status")
def status():
    m = manifest()
    return {
        "ok": True,
        "schema": "sc-workbench-v790-status/1.0",
        "version": VERSION,
        "release": "Scientific Workflow Graph",
        "typedNodes": True,
        "acyclicDependencyGraphs": True,
        "explicitBindings": True,
        "contentAddressedGraphPlans": True,
        "executionObjectLineage": True,
        "platformCoreWorkflowPlanning": True,
        "automaticCoreDispatch": False,
        "hiddenOutputSubstitution": False,
        "scientificValidityCertification": False,
        "manifest": m,
    }

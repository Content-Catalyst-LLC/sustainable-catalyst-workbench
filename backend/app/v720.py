"""Workbench v7.2.0 — Scientific Runtime Orchestrator.

v7.2 adds a deterministic, bounded runtime-routing layer above the v7.0 unified
scientific & engineering execution runtime and the v7.1 execution-object model.
It selects an allow-listed Workbench runtime adapter for a declared operation,
executes only adapters marked local/in-process, preserves the resulting v7.1
execution object, and can prepare descriptive Platform Core research-workflow
records using the exact ``sc.research.workflow-orchestration.v1`` contract.

The orchestrator never executes arbitrary Python, R, Julia, shell commands,
dynamic imports, user-provided callables, or hidden code. R, Julia and generic
ML runtimes are represented only as explicit handoff-plan adapters until a
bounded adapter is separately installed and certified. Platform Core remains a
coordination/provenance plane and is never asked to execute specialist work.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v700 import (
    OPERATIONS,
    RUNTIME_REF as EXECUTION_RUNTIME_REF,
    UnifiedExecutionRequest,
    WorkflowRequest,
    WorkflowStep,
    _execute_request,
    execute_workflow,
)
from .v710 import _execution_object_from_result, _workflow_object_from_result

VERSION = APP_VERSION
SCHEMA = "sc-workbench-scientific-runtime-orchestrator/1.0"
ROUTE_SCHEMA = "sc-workbench-runtime-route/1.0"
EXECUTION_SCHEMA = "sc-workbench-orchestrated-execution/1.0"
WORKFLOW_SCHEMA = "sc-workbench-orchestrated-workflow/1.0"
EXTERNAL_PLAN_SCHEMA = "sc-workbench-external-runtime-handoff-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-runtime-orchestrator-core-workflow-plan/1.0"
CORE_WORKFLOW_CONTRACT = "sc.research.workflow-orchestration.v1"
ORCHESTRATOR_REF = "workbench:/runtime/scientific-orchestrator"
router = APIRouter(tags=["workbench-v720-scientific-runtime-orchestrator"])


@dataclass(frozen=True)
class RuntimeAdapter:
    key: str
    label: str
    runtime_family: str
    mode: Literal["in_process", "handoff_plan"]
    categories: Tuple[str, ...]
    deterministic_routing: bool = True
    available: bool = True
    priority: int = 100
    description: str = ""


def _adapter(key: str, label: str, family: str, categories: Tuple[str, ...], *, mode: str = "in_process", available: bool = True, priority: int = 100, description: str = "") -> RuntimeAdapter:
    return RuntimeAdapter(key, label, family, mode, categories, True, available, priority, description)


RUNTIME_ADAPTERS: Dict[str, RuntimeAdapter] = {
    "workbench.symbolic": _adapter("workbench.symbolic", "Workbench Symbolic Mathematics", "python-native", ("mathematics",), description="Restricted SymPy-backed symbolic/CAS execution."),
    "workbench.numerical": _adapter("workbench.numerical", "Workbench Numerical Scientific Computing", "python-native", ("numerical-scientific",), description="Bounded numerical methods, solvers, linear algebra and optimization."),
    "workbench.simulation": _adapter("workbench.simulation", "Workbench Simulation & Systems", "python-native", ("simulation-systems",), description="Deterministic simulation, digital-twin and systems-model execution."),
    "workbench.controls": _adapter("workbench.controls", "Workbench Controls & Signals", "python-native", ("controls-mechatronics", "signals-controls"), description="Controls, robotics, signals and systems analysis."),
    "workbench.measurement": _adapter("workbench.measurement", "Workbench Measurement & Instrumentation", "python-native", ("measurement-instrumentation",), description="Instrumentation, acquisition, calibration and measurement analysis."),
    "workbench.electronics": _adapter("workbench.electronics", "Workbench Electronics & Digital Hardware", "python-native", ("electronics-embedded", "digital-logic-fpga"), description="Electronics, embedded systems, digital logic and FPGA analysis/scaffolding."),
    "workbench.uncertainty": _adapter("workbench.uncertainty", "Workbench Uncertainty & Sensitivity", "python-native", ("uncertainty-sensitivity",), description="Sampling, Sobol/Morris, ensembles and exceedance analysis."),
    "workbench.predictive": _adapter("workbench.predictive", "Workbench Predictive Runtime", "python-native", ("predictive",), description="Forecasting, backtesting and calibration."),
    "workbench.forensics": _adapter("workbench.forensics", "Workbench Forensic Quantitative Runtime", "python-native", ("forensic-quantitative",), description="Quantitative reconstruction without truth or responsibility determination."),
    "workbench.energy": _adapter("workbench.energy", "Workbench Energy Runtime", "python-native", ("energy-systems",), description="Explicit-input energy-system execution."),
    "external.r": _adapter("external.r", "External R Runtime", "r", tuple(), mode="handoff_plan", available=False, priority=900, description="Plan-only adapter. No R command execution is authorized by v7.2."),
    "external.julia": _adapter("external.julia", "External Julia Runtime", "julia", tuple(), mode="handoff_plan", available=False, priority=900, description="Plan-only adapter. No Julia command execution is authorized by v7.2."),
    "external.ml": _adapter("external.ml", "External ML Runtime", "ml", tuple(), mode="handoff_plan", available=False, priority=900, description="Plan-only adapter for a future bounded ML runtime."),
}


class RouteRequest(BaseModel):
    operation: str = Field(min_length=1, max_length=180)
    preferredRuntime: str = Field(default="", max_length=180)
    requireDeterministic: bool = True
    allowHandoffPlan: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("operation")
    @classmethod
    def known_operation(cls, value: str) -> str:
        if value not in OPERATIONS:
            raise ValueError("operation is not registered in the v7.0 unified execution runtime")
        return value


class OrchestratedExecutionRequest(UnifiedExecutionRequest):
    preferredRuntime: str = Field(default="", max_length=180)
    requireDeterministic: bool = True
    allowHandoffPlan: bool = False
    datasetRefs: List[str] = Field(default_factory=list, max_length=200)
    environmentRefs: List[str] = Field(default_factory=list, max_length=100)
    methodRefs: List[str] = Field(default_factory=list, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=100)


class OrchestratorWorkflowStep(WorkflowStep):
    preferredRuntime: str = Field(default="", max_length=180)
    requireDeterministic: bool = True


class OrchestratorWorkflowRequest(BaseModel):
    workflowKey: str = Field(default="workbench-orchestrated-workflow", min_length=1, max_length=180)
    title: str = Field(default="", max_length=400)
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    steps: List[OrchestratorWorkflowStep] = Field(min_length=1, max_length=80)
    stopOnFailure: bool = True
    datasetRefs: List[str] = Field(default_factory=list, max_length=200)
    environmentRefs: List[str] = Field(default_factory=list, max_length=100)
    methodRefs: List[str] = Field(default_factory=list, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_step_ids(self):
        ids = [s.stepId for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("workflow stepId values must be unique")
        return self


class ExternalRuntimePlanRequest(BaseModel):
    runtime: Literal["external.r", "external.julia", "external.ml"]
    taskKey: str = Field(min_length=1, max_length=180)
    projectRef: str = Field(default="", max_length=1000)
    inputRefs: List[str] = Field(default_factory=list, max_length=200)
    environmentRefs: List[str] = Field(default_factory=list, max_length=100)
    requestedOperation: str = Field(default="", max_length=180)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CoreWorkflowPlanRequest(BaseModel):
    orchestrationResult: Dict[str, Any]
    coreWorkflowId: str = Field(default="", max_length=128)
    workflowType: Literal[
        "research_lifecycle", "scientific_study", "investigation", "systematic_review",
        "engineering_analysis", "forensic_investigation", "publication_pipeline", "replication", "custom"
    ] = "engineering_analysis"
    visibility: Literal["private", "internal", "public"] = "internal"
    protocolRef: str = Field(default="", max_length=1000)
    programRef: str = Field(default="", max_length=1000)
    createdBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _adapter_record(adapter: RuntimeAdapter) -> Dict[str, Any]:
    operation_count = sum(1 for spec in OPERATIONS.values() if spec.category in adapter.categories)
    return {
        "key": adapter.key,
        "label": adapter.label,
        "runtimeFamily": adapter.runtime_family,
        "mode": adapter.mode,
        "available": adapter.available,
        "deterministicRouting": adapter.deterministic_routing,
        "priority": adapter.priority,
        "categories": list(adapter.categories),
        "operationCount": operation_count,
        "runtimeRef": f"{ORCHESTRATOR_REF}/adapter/{adapter.key}",
        "description": adapter.description,
        "arbitraryCodeExecutionAuthorized": False,
        "subprocessExecutionAuthorized": False,
    }


def orchestrator_manifest() -> Dict[str, Any]:
    local = [a for a in RUNTIME_ADAPTERS.values() if a.mode == "in_process"]
    planned = [a for a in RUNTIME_ADAPTERS.values() if a.mode == "handoff_plan"]
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "orchestratorRef": ORCHESTRATOR_REF,
        "executionRuntimeRef": EXECUTION_RUNTIME_REF,
        "operationCount": len(OPERATIONS),
        "adapterCount": len(RUNTIME_ADAPTERS),
        "localAdapterCount": len(local),
        "handoffPlanAdapterCount": len(planned),
        "coreWorkflowContract": CORE_WORKFLOW_CONTRACT,
        "capabilities": {
            "deterministicRouting": True,
            "singleExecutionOrchestration": True,
            "workflowOrchestration": True,
            "executionObjectProjection": True,
            "externalRuntimeHandoffPlanning": True,
            "coreResearchWorkflowPlanning": True,
        },
        "boundaries": {
            "allowlistedOperationsOnly": True,
            "arbitraryPythonExecutionAuthorized": False,
            "arbitraryRExecutionAuthorized": False,
            "arbitraryJuliaExecutionAuthorized": False,
            "shellExecutionAuthorized": False,
            "dynamicImportAuthorized": False,
            "externalRuntimeAutoDispatchAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "scientificValidityCertified": False,
            "reproducibilityCertified": False,
            "truthDetermined": False,
        },
    }


def runtime_catalog() -> Dict[str, Any]:
    adapters = [_adapter_record(RUNTIME_ADAPTERS[key]) for key in sorted(RUNTIME_ADAPTERS)]
    return {
        "ok": True,
        "schema": "sc-workbench-scientific-runtime-adapter-catalog/1.0",
        "version": VERSION,
        "orchestratorRef": ORCHESTRATOR_REF,
        "adapters": adapters,
        "adapterCount": len(adapters),
    }


def _route(request: RouteRequest) -> Dict[str, Any]:
    spec = OPERATIONS[request.operation]
    chosen: Optional[RuntimeAdapter] = None
    reason = "category-default"
    if request.preferredRuntime:
        chosen = RUNTIME_ADAPTERS.get(request.preferredRuntime)
        if chosen is None:
            raise HTTPException(status_code=422, detail="preferredRuntime is not registered")
        if chosen.mode == "in_process" and spec.category not in chosen.categories:
            raise HTTPException(status_code=422, detail=f"preferredRuntime {chosen.key} does not support operation category {spec.category}")
        if chosen.mode == "handoff_plan" and not request.allowHandoffPlan:
            raise HTTPException(status_code=409, detail=f"preferredRuntime {chosen.key} is plan-only and cannot execute in v7.2")
        reason = "explicit-preference"
    else:
        candidates = [a for a in RUNTIME_ADAPTERS.values() if a.mode == "in_process" and spec.category in a.categories]
        candidates.sort(key=lambda a: (a.priority, a.key))
        if not candidates:
            raise HTTPException(status_code=422, detail=f"no bounded runtime adapter supports category {spec.category}")
        chosen = candidates[0]
    if request.requireDeterministic and not chosen.deterministic_routing:
        raise HTTPException(status_code=422, detail="selected runtime does not satisfy deterministic routing requirement")
    executable = chosen.mode == "in_process" and chosen.available
    route = {
        "ok": True,
        "schema": ROUTE_SCHEMA,
        "version": VERSION,
        "operation": request.operation,
        "category": spec.category,
        "sourceRelease": spec.source_release,
        "adapter": _adapter_record(chosen),
        "selectionReason": reason,
        "executable": executable,
        "handoffRequired": not executable,
        "executionAuthority": "workbench" if executable else "external-adapter-not-installed",
        "fallbackPerformed": False,
        "metadata": request.metadata,
    }
    route["routeHash"] = content_hash(route)
    return route


def _declared_request(request: OrchestratedExecutionRequest) -> Dict[str, Any]:
    return {
        "payload": request.payload,
        "inputRefs": request.inputRefs,
        "requestKey": request.requestKey,
        "metadata": {
            **request.metadata,
            "preferredRuntime": request.preferredRuntime,
            "orchestrator": SCHEMA,
        },
    }


def orchestrated_execute(request: OrchestratedExecutionRequest) -> Dict[str, Any]:
    route = _route(RouteRequest(
        operation=request.operation,
        preferredRuntime=request.preferredRuntime,
        requireDeterministic=request.requireDeterministic,
        allowHandoffPlan=request.allowHandoffPlan,
        metadata={"projectRef": request.projectRef, "requestKey": request.requestKey},
    ))
    if not route["executable"]:
        raise HTTPException(status_code=409, detail="selected adapter is plan-only; build an external handoff plan instead of executing")
    result = _execute_request(UnifiedExecutionRequest(
        operation=request.operation,
        payload=request.payload,
        projectRef=request.projectRef,
        coreSessionId=request.coreSessionId,
        requestKey=request.requestKey,
        label=request.label,
        inputRefs=request.inputRefs,
        metadata={**request.metadata, "orchestratorRouteHash": route["routeHash"], "runtimeAdapter": route["adapter"]["key"]},
    ))
    obj = _execution_object_from_result(
        result,
        declared_request=_declared_request(request),
        object_key=request.requestKey,
        label=request.label,
        project_ref=request.projectRef,
        core_session_id=request.coreSessionId,
        dataset_refs=request.datasetRefs,
        environment_refs=request.environmentRefs,
        method_refs=[route["adapter"]["runtimeRef"], *request.methodRefs],
        parent_refs=[],
        tags=request.tags,
        metadata={**request.metadata, "orchestratorRoute": route},
    )
    out = {
        "ok": bool(result.get("ok", True)),
        "schema": EXECUTION_SCHEMA,
        "version": VERSION,
        "orchestratorRef": ORCHESTRATOR_REF,
        "route": route,
        "executionResult": result,
        "executionObject": obj,
        "automaticFallbackPerformed": False,
        "automaticExternalDispatchPerformed": False,
        "automaticCoreDispatchPerformed": False,
        "automaticCorePersistencePerformed": False,
    }
    out["orchestrationHash"] = content_hash({
        "routeHash": route["routeHash"],
        "executionRef": result.get("executionRef"),
        "resultHash": result.get("resultHash"),
        "objectHash": obj.get("objectHash"),
    })
    return out


def orchestrated_workflow(request: OrchestratorWorkflowRequest) -> Dict[str, Any]:
    routes: Dict[str, Dict[str, Any]] = {}
    for step in request.steps:
        route = _route(RouteRequest(
            operation=step.operation,
            preferredRuntime=step.preferredRuntime,
            requireDeterministic=step.requireDeterministic,
            allowHandoffPlan=True,
            metadata={"workflowKey": request.workflowKey, "stepId": step.stepId},
        ))
        if not route["executable"]:
            raise HTTPException(status_code=409, detail=f"workflow step {step.stepId} selected plan-only adapter {route['adapter']['key']}")
        routes[step.stepId] = route
    base = WorkflowRequest(
        workflowKey=request.workflowKey,
        projectRef=request.projectRef,
        coreSessionId=request.coreSessionId,
        steps=[WorkflowStep(
            stepId=s.stepId,
            operation=s.operation,
            payload=s.payload,
            dependsOn=s.dependsOn,
            inputRefs=s.inputRefs,
            label=s.label,
            metadata={**s.metadata, "runtimeAdapter": routes[s.stepId]["adapter"]["key"], "orchestratorRouteHash": routes[s.stepId]["routeHash"]},
        ) for s in request.steps],
        stopOnFailure=request.stopOnFailure,
    )
    workflow = execute_workflow(base)
    declared = {
        "workflowKey": request.workflowKey,
        "projectRef": request.projectRef,
        "coreSessionId": request.coreSessionId,
        "steps": [s.model_dump() for s in request.steps],
    }
    obj = _workflow_object_from_result(
        workflow,
        declared_request=declared,
        object_key=request.workflowKey,
        label=request.title or request.workflowKey,
        project_ref=request.projectRef,
        core_session_id=request.coreSessionId,
        dataset_refs=request.datasetRefs,
        environment_refs=request.environmentRefs,
        method_refs=[ORCHESTRATOR_REF, *request.methodRefs],
        parent_refs=[],
        tags=request.tags,
        metadata={**request.metadata, "orchestratorRoutes": routes},
    )
    out = {
        "ok": workflow.get("ok", False),
        "schema": WORKFLOW_SCHEMA,
        "version": VERSION,
        "orchestratorRef": ORCHESTRATOR_REF,
        "workflowKey": request.workflowKey,
        "projectRef": request.projectRef,
        "coreSessionId": request.coreSessionId,
        "routes": routes,
        "workflowResult": workflow,
        "executionObject": obj,
        "externalRuntimeDispatchPerformed": False,
        "automaticCoreDispatchPerformed": False,
        "automaticCorePersistencePerformed": False,
    }
    out["orchestrationHash"] = content_hash({
        "workflowHash": workflow.get("workflowHash"),
        "objectHash": obj.get("objectHash"),
        "routeHashes": {k: v.get("routeHash") for k, v in routes.items()},
    })
    return out


def external_runtime_plan(request: ExternalRuntimePlanRequest) -> Dict[str, Any]:
    adapter = RUNTIME_ADAPTERS[request.runtime]
    plan = {
        "ok": True,
        "schema": EXTERNAL_PLAN_SCHEMA,
        "version": VERSION,
        "orchestratorRef": ORCHESTRATOR_REF,
        "taskKey": request.taskKey,
        "projectRef": request.projectRef,
        "requestedOperation": request.requestedOperation or None,
        "adapter": _adapter_record(adapter),
        "inputRefs": sorted(set(request.inputRefs)),
        "environmentRefs": sorted(set(request.environmentRefs)),
        "metadata": request.metadata,
        "executionPerformed": False,
        "adapterInstalled": False,
        "handoffRequired": True,
        "manualOrFutureBoundedAdapterRequired": True,
        "arbitraryCodeExecutionAuthorized": False,
        "automaticExternalDispatchAuthorized": False,
        "automaticCoreDispatchAuthorized": False,
    }
    plan["planHash"] = content_hash(plan)
    return plan


def _extract_execution_objects(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    schema = result.get("schema")
    if schema == EXECUTION_SCHEMA:
        obj = result.get("executionObject")
        return [obj] if isinstance(obj, dict) else []
    if schema == WORKFLOW_SCHEMA:
        obj = result.get("executionObject")
        children = obj.get("children", []) if isinstance(obj, dict) else []
        return [x for x in children if isinstance(x, dict)]
    raise HTTPException(status_code=422, detail=f"orchestrationResult must use {EXECUTION_SCHEMA} or {WORKFLOW_SCHEMA}")


def build_core_workflow_plan(request: CoreWorkflowPlanRequest) -> Dict[str, Any]:
    result = request.orchestrationResult
    objects = _extract_execution_objects(result)
    if not objects:
        raise HTTPException(status_code=422, detail="orchestrationResult contains no execution objects")
    project_ref = str(result.get("projectRef") or objects[0].get("projectRef") or "")
    if result.get("schema") == WORKFLOW_SCHEMA:
        workflow_key = str(result.get("workflowKey") or "workbench-runtime-orchestration")
        title = str((result.get("executionObject") or {}).get("label") or workflow_key)
    else:
        op = str((result.get("executionResult") or {}).get("operation") or "execution")
        workflow_key = f"workbench-runtime:{(result.get('executionObject') or {}).get('objectId','execution')}"
        title = f"Workbench runtime execution: {op}"
    create_data = {
        "workflow_key": workflow_key,
        "title": title,
        "workflow_type": request.workflowType,
        "status": "completed" if result.get("ok") else "paused",
        "visibility": request.visibility,
        "project_ref": project_ref or None,
        "protocol_ref": request.protocolRef or None,
        "program_ref": request.programRef or None,
        "metadata": {
            "sourceProduct": PRODUCT_KEY,
            "sourceVersion": VERSION,
            "orchestratorSchema": SCHEMA,
            "orchestrationHash": result.get("orchestrationHash"),
        },
        "provenance": {
            "executionObjectRefs": [x.get("objectRef") for x in objects],
            "executionObjectHashes": [x.get("objectHash") for x in objects],
        },
    }
    create_request = {"method": "POST", "path": "/v1/research/workflows", "data": create_data}
    stage_requests: List[Dict[str, Any]] = []
    binding_requests: List[Dict[str, Any]] = []
    event_requests: List[Dict[str, Any]] = []
    if request.coreWorkflowId:
        for idx, obj in enumerate(objects, start=1):
            operation = str((obj.get("method") or {}).get("operation") or f"execution-{idx}")
            stage_key = f"workbench-execution-{idx}"
            stage_requests.append({
                "method": "POST",
                "path": f"/v1/research/workflows/{request.coreWorkflowId}/stages",
                "data": {
                    "stage_key": stage_key,
                    "stage_type": "analysis",
                    "ordinal": idx,
                    "status": "completed" if obj.get("status") == "completed" else "blocked",
                    "responsible_product": "workbench",
                    "object_ref": obj.get("objectRef"),
                    "entry_criteria": {"declaredOperation": operation},
                    "exit_criteria": {"executionObjectHash": obj.get("objectHash"), "resultContentImmutable": True},
                    "created_by": request.createdBy,
                },
            })
            binding_requests.append({
                "method": "POST",
                "path": f"/v1/research/workflows/{request.coreWorkflowId}/context-bindings",
                "data": {
                    "binding_key": f"execution-object-{idx}",
                    "stage_key": stage_key,
                    "product_key": "workbench",
                    "object_type": "execution",
                    "object_ref": obj.get("objectRef"),
                    "relation": "specialist_execution",
                    "context": {"objectHash": obj.get("objectHash"), "operation": operation},
                    "created_by": request.createdBy,
                },
            })
            event_requests.append({
                "method": "POST",
                "path": f"/v1/research/workflows/{request.coreWorkflowId}/events",
                "data": {
                    "event_key": f"workbench-completed-{idx}",
                    "event_type": "stage_completed",
                    "stage_key": stage_key,
                    "actor_ref": "product:workbench",
                    "details": {"executionObjectRef": obj.get("objectRef"), "objectHash": obj.get("objectHash"), "declaredByWorkbench": True},
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
        "workflowRegistration": create_request,
        "stageRegistrations": stage_requests,
        "contextBindings": binding_requests,
        "eventRegistrations": event_requests,
        "executionObjectCount": len(objects),
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


@router.get("/execution/orchestrator/manifest")
def manifest() -> Dict[str, Any]:
    return orchestrator_manifest()


@router.get("/execution/orchestrator/runtimes")
def runtimes() -> Dict[str, Any]:
    return runtime_catalog()


@router.post("/execution/orchestrator/route")
def route(request: RouteRequest) -> Dict[str, Any]:
    return _route(request)


@router.post("/execution/orchestrator/execute")
def execute(request: OrchestratedExecutionRequest) -> Dict[str, Any]:
    return orchestrated_execute(request)


@router.post("/execution/orchestrator/workflow/run")
def workflow(request: OrchestratorWorkflowRequest) -> Dict[str, Any]:
    return orchestrated_workflow(request)


@router.post("/execution/orchestrator/external/plan")
def external_plan(request: ExternalRuntimePlanRequest) -> Dict[str, Any]:
    return external_runtime_plan(request)


@router.post("/integration/core/runtime-orchestrator/workflow/plan")
def core_workflow_plan(
    request: CoreWorkflowPlanRequest,
    x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return build_core_workflow_plan(request)


@router.get("/v720/status")
def status() -> Dict[str, Any]:
    manifest = orchestrator_manifest()
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Scientific Runtime Orchestrator",
        "orchestratorRef": ORCHESTRATOR_REF,
        "operationCount": manifest["operationCount"],
        "adapterCount": manifest["adapterCount"],
        "localAdapterCount": manifest["localAdapterCount"],
        "handoffPlanAdapterCount": manifest["handoffPlanAdapterCount"],
        "deterministicRouting": True,
        "workflowOrchestration": True,
        "executionObjectProjection": True,
        "externalRuntimeHandoffPlanning": True,
        "coreResearchWorkflowPlanning": True,
        "arbitraryCodeExecution": False,
        "automaticExternalRuntimeDispatch": False,
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
        "scientificValidityCertification": False,
        "truthDetermination": False,
    }

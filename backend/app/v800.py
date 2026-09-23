"""Workbench v8.0.0 — Unified Computational Research Environment.

Major consolidation layer over the completed v7 scientific/engineering stack.
Creates one content-addressed research environment that references data workspaces,
notebooks, workflow graphs, execution objects, visual workspaces, V&V reports and
reproducible packages. The environment coordinates explicit surface plans and Core
project/session bindings without duplicating specialist compute or authorizing hidden
execution, persistence, replay, or scientific-truth claims.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import _authorize_core_route, CORE_RUNTIME_CONTRACT
from .v650 import PRODUCT_REF, ADAPTER_REF
from .v660 import CORE_UNIFIED_RUNTIME_CONTRACT, CORE_PATHS
from .v6120 import CORE_REPRODUCIBLE_RESEARCH_CONTRACT

VERSION = APP_VERSION
CORE_UNIFIED_RUNTIME_CONTRACT_EXPECTED = "sc.research.unified-research-scientific-investigation-runtime.v1"
if CORE_UNIFIED_RUNTIME_CONTRACT != CORE_UNIFIED_RUNTIME_CONTRACT_EXPECTED:
    raise RuntimeError("Platform Core unified research runtime contract mismatch")
SCHEMA = "sc-workbench-unified-computational-research-environment/1.0"
ENVIRONMENT_SCHEMA = "sc-workbench-computational-research-environment/1.0"
SURFACE_PLAN_SCHEMA = "sc-workbench-research-environment-surface-plan/1.0"
SESSION_PLAN_SCHEMA = "sc-workbench-research-environment-session-plan/1.0"
SNAPSHOT_PLAN_SCHEMA = "sc-workbench-research-environment-snapshot-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-core-research-environment-plan/1.0"
MAX_COMPONENTS = 192
MAX_EXECUTION_OBJECTS = 128
MAX_REFS = 256

router = APIRouter(tags=["workbench-v800-unified-computational-research-environment"])

EnvironmentComponentType = Literal[
    "data-workspace", "notebook-run", "workflow-graph-run", "visual-workspace",
    "validation-report", "reproducible-package", "execution-object", "solver-run",
    "simulation-run", "engineering-run", "design-space-run", "predictive-run",
    "forensic-run", "artifact", "source", "other",
]
SurfaceType = Literal[
    "overview", "data", "notebook", "workflow", "visual", "validation",
    "solver", "simulation", "engineering", "design-space", "packages",
]

SURFACE_ENDPOINTS: Dict[str, Dict[str, str]] = {
    "overview": {"manifest": "/research-environment/manifest"},
    "data": {"manifest": "/data-workspace/manifest", "build": "/data-workspace/build"},
    "notebook": {"manifest": "/notebooks/manifest", "run": "/notebooks/run"},
    "workflow": {"manifest": "/workflow-graph/manifest", "run": "/workflow-graph/run"},
    "visual": {"manifest": "/visual-workspace/manifest", "build": "/visual-workspace/build"},
    "validation": {"manifest": "/validation/manifest", "build": "/validation/report/build"},
    "solver": {"manifest": "/solvers/manifest", "run": "/solvers/solve"},
    "simulation": {"manifest": "/simulations/manifest", "run": "/simulations/run"},
    "engineering": {"manifest": "/engineering/manifest", "run": "/engineering/analyze"},
    "design-space": {"manifest": "/design-space/manifest", "run": "/design-space/optimize"},
    "packages": {"manifest": "/repro-package/manifest", "build": "/repro-package/build"},
}

INTEGRATED_RUNTIME_CONTRACTS = {
    "unifiedRuntime": "sc-workbench-unified-scientific-engineering-execution/1.0",
    "executionObject": "sc-workbench-execution-object/1.0",
    "runtimeOrchestrator": "sc-workbench-scientific-runtime-orchestrator/1.0",
    "dataWorkspace": "sc-workbench-data-variable-parameter-workspace/1.0",
    "numericalSolver": "sc-workbench-numerical-methods-solver-runtime/1.0",
    "simulation": "sc-workbench-simulation-dynamical-systems-runtime/1.0",
    "engineering": "sc-workbench-engineering-systems-runtime/1.0",
    "designSpace": "sc-workbench-optimization-design-space-runtime/1.0",
    "validation": "sc-workbench-model-validation-verification-framework/1.0",
    "workflowGraph": "sc-workbench-scientific-workflow-graph/1.0",
    "notebook": "sc-workbench-interactive-computational-notebook/1.0",
    "visualWorkspace": "sc-workbench-visual-scientific-computing-workspace/1.0",
    "reproduciblePackage": "sc-workbench-reproducible-experiment-engineering-package/1.0",
}


def _safe(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _ref_list(values: List[str]) -> List[str]:
    return sorted({_safe(x, 1000) for x in values if _safe(x, 1000)})[:MAX_REFS]


class EnvironmentComponentSpec(BaseModel):
    componentKey: str = Field(min_length=1, max_length=160)
    componentType: EnvironmentComponentType
    componentRef: str = Field(default="", max_length=1000)
    contentHash: str = Field(default="", max_length=256)
    payload: Optional[Any] = None
    required: bool = True
    role: str = Field(default="context", max_length=120)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def identity(self):
        if self.payload is None and not self.componentRef:
            raise ValueError("componentRef or payload is required")
        if self.required and self.payload is None and not self.contentHash:
            raise ValueError("required reference-only components must declare contentHash")
        return self


class ResearchEnvironmentSpec(BaseModel):
    environmentKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=300)
    projectEntityId: str = Field(min_length=1, max_length=255)
    coreProjectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=255)
    activeSurface: SurfaceType = "overview"
    components: List[EnvironmentComponentSpec] = Field(default_factory=list, max_length=MAX_COMPONENTS)
    executionObjects: List[Dict[str, Any]] = Field(default_factory=list, max_length=MAX_EXECUTION_OBJECTS)
    lineageRefs: List[str] = Field(default_factory=list, max_length=MAX_REFS)
    assumptions: List[str] = Field(default_factory=list, max_length=256)
    limitations: List[str] = Field(default_factory=list, max_length=256)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_components(self):
        keys = [x.componentKey for x in self.components]
        if len(keys) != len(set(keys)):
            raise ValueError("componentKey values must be unique")
        return self


class EnvironmentBuildRequest(BaseModel):
    environment: ResearchEnvironmentSpec


class EnvironmentValidateRequest(BaseModel):
    researchEnvironment: Dict[str, Any]


class SurfacePlanRequest(BaseModel):
    researchEnvironment: Dict[str, Any]
    surface: SurfaceType
    action: Literal["open", "resume", "prepare-run", "inspect"] = "open"
    targetRef: str = Field(default="", max_length=1000)
    requestPayload: Dict[str, Any] = Field(default_factory=dict)


class SessionPlanRequest(BaseModel):
    researchEnvironment: Dict[str, Any]
    action: Literal["open", "resume", "switch-surface", "close"] = "open"
    surface: SurfaceType = "overview"


class SnapshotPlanRequest(BaseModel):
    researchEnvironment: Dict[str, Any]
    packageKey: str = Field(default="", max_length=160)
    title: str = Field(default="", max_length=300)


class CoreEnvironmentPlanRequest(BaseModel):
    researchEnvironment: Dict[str, Any]
    coreProjectEntityId: str = Field(min_length=1, max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def _normalize_component(item: EnvironmentComponentSpec) -> Dict[str, Any]:
    payload_hash = content_hash(item.payload) if item.payload is not None else ""
    if item.contentHash and payload_hash and item.contentHash != payload_hash:
        raise ValueError(f"component {item.componentKey} contentHash does not match payload")
    ch = item.contentHash or payload_hash
    return {
        "componentKey": item.componentKey,
        "componentType": item.componentType,
        "componentRef": item.componentRef or (f"sc://workbench/environment-component/{item.componentKey}/{ch}" if ch else None),
        "contentHash": ch or None,
        "payload": deepcopy(item.payload),
        "required": item.required,
        "role": item.role,
        "metadata": deepcopy(item.metadata),
    }


def manifest() -> Dict[str, Any]:
    record = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Unified Computational Research Environment",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "integratedRuntimeContracts": dict(INTEGRATED_RUNTIME_CONTRACTS),
        "surfaces": deepcopy(SURFACE_ENDPOINTS),
        "coreContracts": {
            "runtimeContract": CORE_RUNTIME_CONTRACT,
            "unifiedResearchSession": CORE_UNIFIED_RUNTIME_CONTRACT,
            "reproduciblePackage": CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        },
        "boundaries": {
            "specialistComputationRemainsInSpecialistRuntimes": True,
            "hiddenInterpreterStateAuthorized": False,
            "automaticExecutionAuthorized": False,
            "automaticReplayAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "scientificValidityCertified": False,
            "engineeringSafetyCertified": False,
            "researchTruthDeterminationAuthorized": False,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


def build_environment(spec: ResearchEnvironmentSpec) -> Dict[str, Any]:
    components = [_normalize_component(x) for x in spec.components]
    execution_objects = []
    for obj in spec.executionObjects:
        if not isinstance(obj, dict):
            raise ValueError("executionObjects entries must be objects")
        obj_hash = obj.get("objectHash") or content_hash(obj)
        execution_objects.append({"executionObjectRef": obj.get("objectRef") or f"sc://workbench/execution-object/{obj_hash}", "objectHash": obj_hash, "payload": deepcopy(obj)})
    base = {
        "ok": True,
        "schema": ENVIRONMENT_SCHEMA,
        "version": VERSION,
        "environmentKey": spec.environmentKey,
        "environmentRef": "",
        "title": spec.title,
        "projectEntityId": spec.projectEntityId,
        "coreProjectRef": spec.coreProjectRef or None,
        "coreSessionId": spec.coreSessionId or None,
        "activeSurface": spec.activeSurface,
        "surfaces": deepcopy(SURFACE_ENDPOINTS),
        "components": components,
        "executionObjects": execution_objects,
        "lineageRefs": _ref_list(spec.lineageRefs),
        "assumptions": list(spec.assumptions),
        "limitations": list(spec.limitations),
        "metadata": deepcopy(spec.metadata),
        "provenance": {"workbenchVersion": VERSION, **deepcopy(spec.provenance)},
        "state": {
            "componentCount": len(components),
            "executionObjectCount": len(execution_objects),
            "contentAddressed": True,
            "specialistRuntimeCount": len(INTEGRATED_RUNTIME_CONTRACTS),
        },
        "boundaries": manifest()["boundaries"],
    }
    identity_basis = deepcopy(base)
    identity_basis.pop("environmentRef", None)
    env_hash = content_hash(identity_basis)
    base["environmentHash"] = env_hash
    base["environmentRef"] = f"sc://workbench/research-environment/{spec.environmentKey}/{env_hash}"
    return base


def validate_environment(env: Dict[str, Any]) -> Dict[str, Any]:
    candidate = deepcopy(env)
    given = candidate.pop("environmentHash", "")
    candidate.pop("environmentRef", None)
    expected = content_hash(candidate)
    components_valid = True
    for item in env.get("components", []):
        if item.get("payload") is not None and item.get("contentHash") != content_hash(item.get("payload")):
            components_valid = False
            break
        if item.get("required") and item.get("payload") is None and not item.get("contentHash"):
            components_valid = False
            break
    valid = bool(given) and given == expected and env.get("schema") == ENVIRONMENT_SCHEMA and components_valid
    return {"ok": True, "schema": ENVIRONMENT_SCHEMA, "version": VERSION, "valid": valid, "expectedHash": expected, "providedHash": given, "componentsValid": components_valid}


def _require_environment(env: Dict[str, Any]) -> None:
    if not validate_environment(env)["valid"]:
        raise ValueError("researchEnvironment integrity validation failed")


def surface_plan(req: SurfacePlanRequest) -> Dict[str, Any]:
    _require_environment(req.researchEnvironment)
    endpoint = SURFACE_ENDPOINTS[req.surface]
    target_path = endpoint.get("run") or endpoint.get("build") or endpoint.get("manifest")
    plan = {
        "ok": True,
        "schema": SURFACE_PLAN_SCHEMA,
        "version": VERSION,
        "environmentRef": req.researchEnvironment.get("environmentRef"),
        "environmentHash": req.researchEnvironment.get("environmentHash"),
        "surface": req.surface,
        "action": req.action,
        "targetRef": req.targetRef or None,
        "targetPath": target_path,
        "surfaceEndpoints": deepcopy(endpoint),
        "preparedRequest": deepcopy(req.requestPayload),
        "executionPerformed": False,
        "stateMutationPerformed": False,
        "automaticDispatchAuthorized": False,
    }
    plan["planHash"] = content_hash(plan)
    return plan


def session_plan(req: SessionPlanRequest) -> Dict[str, Any]:
    _require_environment(req.researchEnvironment)
    plan = {
        "ok": True,
        "schema": SESSION_PLAN_SCHEMA,
        "version": VERSION,
        "environmentRef": req.researchEnvironment.get("environmentRef"),
        "environmentHash": req.researchEnvironment.get("environmentHash"),
        "projectEntityId": req.researchEnvironment.get("projectEntityId"),
        "coreSessionId": req.researchEnvironment.get("coreSessionId"),
        "action": req.action,
        "requestedSurface": req.surface,
        "surfaceEndpoints": deepcopy(SURFACE_ENDPOINTS[req.surface]),
        "sessionState": "closed" if req.action == "close" else "prepared",
        "environmentPersistencePerformed": False,
        "executionPerformed": False,
        "automaticCoreDispatchAuthorized": False,
    }
    plan["sessionPlanHash"] = content_hash(plan)
    return plan


def snapshot_plan(req: SnapshotPlanRequest) -> Dict[str, Any]:
    _require_environment(req.researchEnvironment)
    env = req.researchEnvironment
    components = []
    for item in env.get("components", []):
        components.append({
            "componentKey": item.get("componentKey"),
            "componentType": item.get("componentType", "other"),
            "componentRef": item.get("componentRef") or env.get("environmentRef"),
            "contentHash": item.get("contentHash") or content_hash(item.get("payload")),
            "required": bool(item.get("required", True)),
            "payload": deepcopy(item.get("payload")),
            "metadata": {"environmentRole": item.get("role")},
        })
    components.append({
        "componentKey": "research-environment",
        "componentType": "other",
        "componentRef": env.get("environmentRef"),
        "contentHash": env.get("environmentHash"),
        "required": True,
        "payload": deepcopy(env),
        "metadata": {"schema": ENVIRONMENT_SCHEMA},
    })
    request = {
        "package": {
            "packageKey": req.packageKey or f"{env.get('environmentKey')}-snapshot",
            "title": req.title or f"{env.get('title')} — Reproducible Snapshot",
            "projectEntityId": env.get("projectEntityId"),
            "packageKind": "mixed",
            "components": components,
            "lineageRefs": list(env.get("lineageRefs", [])),
            "assumptions": list(env.get("assumptions", [])),
            "limitations": list(env.get("limitations", [])),
            "metadata": {"sourceEnvironmentRef": env.get("environmentRef"), "sourceEnvironmentHash": env.get("environmentHash")},
            "provenance": {"workbenchVersion": VERSION},
        }
    }
    plan = {
        "ok": True,
        "schema": SNAPSHOT_PLAN_SCHEMA,
        "version": VERSION,
        "environmentRef": env.get("environmentRef"),
        "targetPath": "/repro-package/build",
        "preparedReproPackageRequest": request,
        "packageBuildPerformed": False,
        "filesystemWritePerformed": False,
        "automaticReplayAuthorized": False,
    }
    plan["snapshotPlanHash"] = content_hash(plan)
    return plan


def _core_request(path: str, data: Dict[str, Any], phase: str) -> Dict[str, Any]:
    record = {
        "schema": "sc-workbench-core-unified-computational-research-environment-request/1.0",
        "version": VERSION,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "method": "POST",
        "path": path,
        "phase": phase,
        "data": data,
        "automaticDispatchAuthorized": False,
        "callerMustPersistToCore": True,
    }
    record["requestHash"] = content_hash(record)
    return record


def core_environment_plan(req: CoreEnvironmentPlanRequest) -> Dict[str, Any]:
    _require_environment(req.researchEnvironment)
    env = req.researchEnvironment
    sid = _safe(req.coreSessionId or env.get("coreSessionId"), 255)
    requests: List[Dict[str, Any]] = []
    if not sid:
        data = {
            "session_key": f"workbench-{env.get('environmentKey')}",
            "title": env.get("title"),
            "project_ref": env.get("coreProjectRef") or req.coreProjectEntityId,
            "status": "active",
            "project_state_ref": env.get("environmentRef"),
            "runtime_contract_ref": CORE_RUNTIME_CONTRACT,
            "visibility": req.visibility,
            "metadata": {"sourceProductRef": PRODUCT_REF, "workbenchVersion": VERSION, "environmentHash": env.get("environmentHash"), "environmentSchema": ENVIRONMENT_SCHEMA},
            "provenance": {"adapterRef": ADAPTER_REF, "environmentRef": env.get("environmentRef")},
            "created_by": req.createdBy,
        }
        requests.append(_core_request(CORE_PATHS["sessions"], data, "session-create"))
        phase = "prepare-session"
        next_step = "Persist the session request in Platform Core, then call this planner again with the Core-issued session id."
    else:
        common = {"workbenchVersion": VERSION, "environmentHash": env.get("environmentHash"), "environmentRef": env.get("environmentRef")}
        product = {"session_id": sid, "product_ref": PRODUCT_REF, "product_version": VERSION, "runtime_binding_ref": ADAPTER_REF, "context_ref": env.get("environmentRef"), "declared_capabilities": ["unified-computational-research-environment"], "visibility": req.visibility, "metadata": common}
        requests.append(_core_request(CORE_PATHS["productBindings"], product, "environment-bind"))
        object_data = {"session_id": sid, "object_type": "workbench.computational-research-environment", "object_ref": env.get("environmentRef"), "version_ref": f"{env.get('environmentRef')}@{env.get('environmentHash','')[:16]}", "content_hash": env.get("environmentHash"), "role": "unified-research-environment", "visibility": req.visibility, "metadata": common}
        requests.append(_core_request(CORE_PATHS["objectBindings"], object_data, "environment-bind"))
        for comp in env.get("components", []):
            cref = comp.get("componentRef")
            if not cref:
                continue
            ctype = comp.get("componentType")
            if ctype == "visual-workspace":
                data = {"session_id": sid, "visual_ref": cref, "visual_type": "visual-scientific-workspace", "source_refs": [env.get("environmentRef")], "visibility": req.visibility, "metadata": common}
                requests.append(_core_request(CORE_PATHS["visualBindings"], data, "environment-bind"))
            elif ctype == "validation-report":
                data = {"session_id": sid, "validation_ref": cref, "validation_type": "model-validation-verification", "target_refs": [env.get("environmentRef")], "evidence_refs": [], "status": "recorded", "visibility": req.visibility, "metadata": common}
                requests.append(_core_request(CORE_PATHS["validationBindings"], data, "environment-bind"))
            elif ctype == "reproducible-package":
                data = {"session_id": sid, "package_ref": cref, "package_type": "reproducible-experiment-engineering", "version_ref": None, "content_hash": comp.get("contentHash"), "member_refs": [env.get("environmentRef")], "visibility": req.visibility, "metadata": common}
                requests.append(_core_request(CORE_PATHS["packageBindings"], data, "environment-bind"))
        phase = "bind-environment"
        next_step = "Caller may persist the prepared bindings in Platform Core under the existing unified research session contract."
    result = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "phase": phase,
        "environmentRef": env.get("environmentRef"),
        "environmentHash": env.get("environmentHash"),
        "coreProjectEntityId": req.coreProjectEntityId,
        "coreSessionId": sid or None,
        "coreSessionIdMustComeFromCore": True,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "coreRequests": requests,
        "nextStep": next_step,
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "coreExecutesWorkbenchComputation": False,
    }
    result["planHash"] = content_hash(result)
    return result


@router.get("/research-environment/manifest")
def manifest_endpoint():
    return manifest()


@router.post("/research-environment/build")
def build_endpoint(req: EnvironmentBuildRequest):
    try:
        return build_environment(req.environment)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/research-environment/validate")
def validate_endpoint(req: EnvironmentValidateRequest):
    return validate_environment(req.researchEnvironment)


@router.post("/research-environment/surface/plan")
def surface_endpoint(req: SurfacePlanRequest):
    try:
        return surface_plan(req)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/research-environment/session/plan")
def session_endpoint(req: SessionPlanRequest):
    try:
        return session_plan(req)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/research-environment/snapshot/plan")
def snapshot_endpoint(req: SnapshotPlanRequest):
    try:
        return snapshot_plan(req)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/integration/core/research-environment/plan")
def core_plan_endpoint(req: CoreEnvironmentPlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token"), x_sc_gateway_service: str | None = Header(default=None, alias="X-SC-Gateway-Service"), x_sc_core_version: str | None = Header(default=None, alias="X-SC-Core-Version")):
    _authorize_core_route(x_sc_service_token)
    try:
        return core_environment_plan(req)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/v800/status")
def status():
    return {
        "ok": True,
        "version": VERSION,
        "release": "Unified Computational Research Environment",
        "schema": SCHEMA,
        "v7SeriesIntegrated": True,
        "contentAddressedEnvironmentState": True,
        "explicitResearchSurfacePlanning": True,
        "reproducibleSnapshotPlanning": True,
        "coreUnifiedResearchSessionContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "coreRuntimeContract": CORE_RUNTIME_CONTRACT,
        "coreReproduciblePackageContract": CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        "automaticExecutionAuthorized": False,
        "automaticReplayAuthorized": False,
        "automaticCoreDispatchAuthorized": False,
        "scientificValidityCertified": False,
        "engineeringSafetyCertified": False,
        "v8Milestone": "unified-computational-research-environment",
    }

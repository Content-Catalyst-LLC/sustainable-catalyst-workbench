"""Workbench v6.6.0 — Unified Research Project & Session Bridge.

Bridges canonical Workbench computational projects into Platform Core 3.0's
unified research/scientific/investigation runtime without moving specialist
computation or project authority into Core.

The bridge is deliberately two-phase. Workbench first prepares a Core session
creation request. Platform Core persists that session and returns the canonical
Core session id. Workbench can then prepare exact product, object, execution,
visual, package, validation, and handoff binding requests against that id.

No v6.6 endpoint performs outbound HTTP dispatch or writes Platform Core state.
Every Core mutation is represented as a caller-persisted request envelope so
network policy, authentication, retries, audit logging, and authorization stay
outside the deterministic adapter.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v600 import ProjectBuildRequest, ProjectInput, build_project
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route
from .v650 import ADAPTER_REF, PRODUCT_REF, SUPPORTED_CAPABILITIES, map_project, ProjectMapRequest

VERSION = APP_VERSION
SCHEMA = "sc-workbench-core-unified-research-session-bridge/1.0"
CORE_UNIFIED_RUNTIME_CONTRACT = "sc.research.unified-research-scientific-investigation-runtime.v1"
CORE_REQUEST_SCHEMA = "sc-workbench-core-unified-runtime-request/1.0"
SESSION_DRAFT_SCHEMA = "sc-workbench-core-session-draft/1.0"
PROJECT_SESSION_BINDING_SCHEMA = "sc-workbench-core-project-session-binding-plan/1.0"
BINDING_SCHEMA = "sc-workbench-core-unified-runtime-binding/1.0"
BUNDLE_CONTEXT_SCHEMA = "sc-workbench-core-session-context/1.0"
BRIDGE_REF = "workbench:/integration/core/unified-runtime"

CORE_PATHS = {
    "readiness": "/v1/research/unified-runtime/readiness",
    "sessions": "/v1/research/unified-runtime/sessions",
    "objectBindings": "/v1/research/unified-runtime/object-bindings",
    "productBindings": "/v1/research/unified-runtime/product-bindings",
    "executionBindings": "/v1/research/unified-runtime/execution-bindings",
    "visualBindings": "/v1/research/unified-runtime/visual-bindings",
    "validationBindings": "/v1/research/unified-runtime/validation-bindings",
    "packageBindings": "/v1/research/unified-runtime/package-bindings",
    "handoffBindings": "/v1/research/unified-runtime/handoff-bindings",
}

router = APIRouter(tags=["workbench-v660-unified-research-project-session-bridge"])


def _bounded(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _refs(items: List[str]) -> List[str]:
    return sorted({_bounded(item, 1000) for item in items if _bounded(item, 1000)})


def _request(path: str, data: Dict[str, Any], phase: str, method: str = "POST") -> Dict[str, Any]:
    record = {
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "method": method,
        "path": path,
        "phase": phase,
        "data": data,
        "automaticDispatchAuthorized": False,
        "callerMustPersistToCore": True,
    }
    record["requestHash"] = content_hash(record)
    return record


def bridge_manifest() -> Dict[str, Any]:
    record = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "productRef": PRODUCT_REF,
        "runtime": RUNTIME_KIND,
        "bridgeRef": BRIDGE_REF,
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "corePaths": dict(CORE_PATHS),
        "bridgeLifecycle": [
            "prepare-session", "persist-session-in-core", "receive-core-session-id",
            "prepare-project-product-object-bindings", "prepare-specialist-runtime-bindings-as-results-are-created",
        ],
        "supportedBindingTypes": ["product", "object", "execution", "visual", "validation", "package", "handoff"],
        "boundaries": {
            "workbenchProjectRemainsAuthoritative": True,
            "coreSessionRegistryIsReferenceFirst": True,
            "coreSessionIdMustComeFromCore": True,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "coreExecutesWorkbenchComputation": False,
            "workbenchDeterminesResearchTruth": False,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


class SessionCreateRequest(BaseModel):
    project: ProjectInput
    sessionKey: str = ""
    title: str = ""
    coreProjectRef: str = ""
    workflowRef: str = ""
    projectStateRef: str = ""
    certificationSuiteRef: str = ""
    status: str = "active"
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = "workbench"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ProjectSessionBindRequest(BaseModel):
    coreSessionId: str
    project: ProjectInput
    coreProjectRef: str = ""
    contextRef: str = ""
    visibility: Literal["private", "internal", "public"] = "internal"
    includeVariableSet: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("coreSessionId")
    @classmethod
    def session_required(cls, value: str) -> str:
        value = _bounded(value, 128)
        if not value:
            raise ValueError("coreSessionId is required and must be returned by Platform Core")
        return value


class ExecutionBindingRequest(BaseModel):
    coreSessionId: str
    executionRef: str
    runtime: str = "workbench"
    environmentRef: str = ""
    methodRef: str = ""
    inputRefs: List[str] = Field(default_factory=list)
    outputRefs: List[str] = Field(default_factory=list)
    visibility: Literal["private", "internal", "public"] = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VisualBindingRequest(BaseModel):
    coreSessionId: str
    visualRef: str
    visualType: str = "visual-research-object"
    sceneRef: str = ""
    viewRef: str = ""
    sourceRefs: List[str] = Field(default_factory=list)
    visibility: Literal["private", "internal", "public"] = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationBindingRequest(BaseModel):
    coreSessionId: str
    validationRef: str
    validationType: str
    targetRefs: List[str] = Field(default_factory=list)
    evidenceRefs: List[str] = Field(default_factory=list)
    status: str = "recorded"
    visibility: Literal["private", "internal", "public"] = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PackageBindingRequest(BaseModel):
    coreSessionId: str
    packageRef: str
    packageType: str = "computational"
    versionRef: str = ""
    contentHash: str = ""
    memberRefs: List[str] = Field(default_factory=list)
    visibility: Literal["private", "internal", "public"] = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HandoffBindingRequest(BaseModel):
    coreSessionId: str
    handoffRef: str
    sourceProductRef: str = PRODUCT_REF
    targetProductRef: str
    contextRef: str = ""
    status: str = "recorded"
    visibility: Literal["private", "internal", "public"] = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CoreBundleConsumeRequest(BaseModel):
    bundle: Dict[str, Any]


def _require_session(value: str) -> str:
    sid = _bounded(value, 128)
    if not sid:
        raise ValueError("coreSessionId is required and must originate from Platform Core")
    return sid


def build_session_create(request: SessionCreateRequest) -> Dict[str, Any]:
    mapped = map_project(ProjectMapRequest(project=request.project, coreProjectRef=request.coreProjectRef))
    project_id = mapped["workbenchProjectId"]
    session_key = _bounded(request.sessionKey, 180) or f"workbench-{project_id}-runtime"
    title = _bounded(request.title, 400) or request.project.title or f"Workbench project {project_id}"
    project_state_ref = _bounded(request.projectStateRef, 1000) or f"sc://workbench/project-state/{project_id}/{mapped['workbenchProjectHash']}"
    data = {
        "session_key": session_key,
        "title": title,
        "project_ref": mapped["projectRef"],
        "status": _bounded(request.status, 80) or "active",
        "workflow_ref": _bounded(request.workflowRef, 1000) or None,
        "project_state_ref": project_state_ref,
        "runtime_contract_ref": CORE_RUNTIME_CONTRACT,
        "certification_suite_ref": _bounded(request.certificationSuiteRef, 1000) or None,
        "visibility": request.visibility,
        "metadata": {"sourceProductRef": PRODUCT_REF, "workbenchVersion": VERSION, "workbenchProjectId": project_id, "workbenchProjectHash": mapped["workbenchProjectHash"], "bridgeRef": BRIDGE_REF, **request.metadata},
        "provenance": {"adapterRef": ADAPTER_REF, "bridgeSchema": SCHEMA, "projectMapHash": mapped["mappingHash"], **request.provenance},
        "created_by": _bounded(request.createdBy, 255) or "workbench",
    }
    return {
        "ok": bool(mapped["ok"]), "schema": SESSION_DRAFT_SCHEMA, "version": VERSION, "phase": "prepare-session",
        "projectMap": mapped, "sessionDraft": data, "coreRequest": _request(CORE_PATHS["sessions"], data, "session-create"),
        "nextStep": "Persist coreRequest in Platform Core, then use the returned session id as coreSessionId for project binding.",
        "automaticCorePersistenceAuthorized": False,
    }


def build_project_session_bindings(request: ProjectSessionBindRequest) -> Dict[str, Any]:
    sid = _require_session(request.coreSessionId)
    mapped = map_project(ProjectMapRequest(project=request.project, coreProjectRef=request.coreProjectRef))
    built = build_project(ProjectBuildRequest(project=request.project))["project"]
    context_ref = _bounded(request.contextRef, 1000) or mapped["projectObjectRef"]
    common_meta = {"workbenchVersion": VERSION, "workbenchProjectId": mapped["workbenchProjectId"], "workbenchProjectHash": mapped["workbenchProjectHash"], "bridgeSchema": SCHEMA, **request.metadata}
    product = {"session_id": sid, "product_ref": PRODUCT_REF, "product_version": VERSION, "runtime_binding_ref": ADAPTER_REF, "context_ref": context_ref, "declared_capabilities": list(SUPPORTED_CAPABILITIES), "visibility": request.visibility, "metadata": common_meta}
    object_bindings: List[Dict[str, Any]] = [{"session_id": sid, "object_type": "workbench.computational-project", "object_ref": mapped["projectObjectRef"], "version_ref": f"sc://workbench/project-version/{mapped['workbenchProjectId']}/{mapped['workbenchProjectHash']}", "content_hash": mapped["workbenchProjectHash"], "role": "computational-project", "visibility": request.visibility, "metadata": common_meta}]
    for obj in mapped["objects"]:
        object_bindings.append({"session_id": sid, "object_type": obj["objectType"], "object_ref": obj["objectRef"], "version_ref": f"{obj['objectRef']}@{obj['contentHash'][:16]}", "content_hash": obj["contentHash"], "role": "computational-object", "visibility": request.visibility, "metadata": {**common_meta, "workbenchObjectId": obj["objectId"], "kind": obj["kind"], "studio": obj["studio"], "sourceSchema": obj["sourceSchema"], "sourceVersion": obj["sourceVersion"]}})
    if request.includeVariableSet:
        variable_hash = content_hash({"projectId": built["projectId"], "variables": built["variables"]})
        object_bindings.append({"session_id": sid, "object_type": "workbench.shared-variable-set", "object_ref": mapped["variableSetRef"], "version_ref": f"{mapped['variableSetRef']}@{variable_hash[:16]}", "content_hash": variable_hash, "role": "shared-variable-context", "visibility": request.visibility, "metadata": {**common_meta, "variableCount": built["variableCount"]}})
    core_requests = [_request(CORE_PATHS["productBindings"], product, "session-bind")]
    core_requests.extend(_request(CORE_PATHS["objectBindings"], item, "session-bind") for item in object_bindings)
    result = {"ok": bool(mapped["ok"]), "schema": PROJECT_SESSION_BINDING_SCHEMA, "version": VERSION, "phase": "bind-project-to-session", "coreSessionId": sid, "projectRef": mapped["projectRef"], "workbenchProjectId": mapped["workbenchProjectId"], "productBinding": product, "objectBindings": object_bindings, "coreRequests": core_requests, "bindingCount": len(core_requests), "automaticCorePersistenceAuthorized": False, "workbenchProjectRemainsAuthoritative": True}
    result["bindingPlanHash"] = content_hash(result)
    return result


def _binding_result(kind: str, data: Dict[str, Any], path: str) -> Dict[str, Any]:
    result = {"ok": True, "schema": BINDING_SCHEMA, "version": VERSION, "bindingType": kind, "binding": data, "coreRequest": _request(path, data, "specialist-binding"), "automaticCorePersistenceAuthorized": False}
    result["bindingHash"] = content_hash(result)
    return result


def build_execution_binding(request: ExecutionBindingRequest) -> Dict[str, Any]:
    sid = _require_session(request.coreSessionId); ref = _bounded(request.executionRef, 1000)
    if not ref: raise ValueError("executionRef is required")
    data = {"session_id": sid, "execution_ref": ref, "runtime": _bounded(request.runtime, 120) or "workbench", "environment_ref": _bounded(request.environmentRef, 1000) or None, "method_ref": _bounded(request.methodRef, 1000) or None, "input_refs": _refs(request.inputRefs), "output_refs": _refs(request.outputRefs), "visibility": request.visibility, "metadata": {"workbenchVersion": VERSION, "bridgeSchema": SCHEMA, **request.metadata}}
    return _binding_result("execution", data, CORE_PATHS["executionBindings"])


def build_visual_binding(request: VisualBindingRequest) -> Dict[str, Any]:
    sid = _require_session(request.coreSessionId); ref = _bounded(request.visualRef, 1000)
    if not ref: raise ValueError("visualRef is required")
    data = {"session_id": sid, "visual_ref": ref, "visual_type": _bounded(request.visualType, 120) or "visual-research-object", "scene_ref": _bounded(request.sceneRef, 1000) or None, "view_ref": _bounded(request.viewRef, 1000) or None, "source_refs": _refs(request.sourceRefs), "visibility": request.visibility, "metadata": {"workbenchVersion": VERSION, "bridgeSchema": SCHEMA, **request.metadata}}
    return _binding_result("visual", data, CORE_PATHS["visualBindings"])


def build_validation_binding(request: ValidationBindingRequest) -> Dict[str, Any]:
    sid = _require_session(request.coreSessionId); ref = _bounded(request.validationRef, 1000); kind = _bounded(request.validationType, 120)
    if not ref or not kind: raise ValueError("validationRef and validationType are required")
    data = {"session_id": sid, "validation_ref": ref, "validation_type": kind, "target_refs": _refs(request.targetRefs), "evidence_refs": _refs(request.evidenceRefs), "status": _bounded(request.status, 80) or "recorded", "visibility": request.visibility, "metadata": {"workbenchVersion": VERSION, "bridgeSchema": SCHEMA, **request.metadata}}
    return _binding_result("validation", data, CORE_PATHS["validationBindings"])


def build_package_binding(request: PackageBindingRequest) -> Dict[str, Any]:
    sid = _require_session(request.coreSessionId); ref = _bounded(request.packageRef, 1000)
    if not ref: raise ValueError("packageRef is required")
    data = {"session_id": sid, "package_ref": ref, "package_type": _bounded(request.packageType, 120) or "computational", "version_ref": _bounded(request.versionRef, 1000) or None, "content_hash": _bounded(request.contentHash, 128) or None, "member_refs": _refs(request.memberRefs), "visibility": request.visibility, "metadata": {"workbenchVersion": VERSION, "bridgeSchema": SCHEMA, **request.metadata}}
    return _binding_result("package", data, CORE_PATHS["packageBindings"])


def build_handoff_binding(request: HandoffBindingRequest) -> Dict[str, Any]:
    sid = _require_session(request.coreSessionId); href = _bounded(request.handoffRef, 1000); target = _bounded(request.targetProductRef, 500)
    if not href or not target: raise ValueError("handoffRef and targetProductRef are required")
    data = {"session_id": sid, "handoff_ref": href, "source_product_ref": _bounded(request.sourceProductRef, 500) or PRODUCT_REF, "target_product_ref": target, "context_ref": _bounded(request.contextRef, 1000) or None, "status": _bounded(request.status, 80) or "recorded", "visibility": request.visibility, "metadata": {"workbenchVersion": VERSION, "bridgeSchema": SCHEMA, **request.metadata}}
    return _binding_result("handoff", data, CORE_PATHS["handoffBindings"])


def consume_core_bundle(request: CoreBundleConsumeRequest) -> Dict[str, Any]:
    bundle = request.bundle or {}; session = bundle.get("session") if isinstance(bundle.get("session"), dict) else {}
    sid = _bounded(session.get("id"), 128); project_ref = _bounded(session.get("project_ref"), 1000); runtime_contract_ref = _bounded(session.get("runtime_contract_ref"), 1000)
    product_bindings = bundle.get("product_bindings") if isinstance(bundle.get("product_bindings"), list) else []
    wb_binding = next((x for x in product_bindings if isinstance(x, dict) and x.get("product_ref") == PRODUCT_REF), None)
    object_bindings = [x for x in (bundle.get("object_bindings") or []) if isinstance(x, dict)]
    workbench_objects = [x for x in object_bindings if str(x.get("object_type", "")).startswith("workbench.")]
    accepted = bool(sid and project_ref and runtime_contract_ref == CORE_RUNTIME_CONTRACT)
    context = {"schema": BUNDLE_CONTEXT_SCHEMA, "version": VERSION, "coreSessionId": sid, "coreProjectRef": project_ref, "runtimeContractRef": runtime_contract_ref, "workbenchProductBindingPresent": wb_binding is not None, "workbenchObjectBindings": workbench_objects, "executionBindingRefs": [x.get("execution_ref") for x in (bundle.get("execution_bindings") or []) if isinstance(x, dict) and x.get("execution_ref")], "visualBindingRefs": [x.get("visual_ref") for x in (bundle.get("visual_bindings") or []) if isinstance(x, dict) and x.get("visual_ref")], "packageBindingRefs": [x.get("package_ref") for x in (bundle.get("package_bindings") or []) if isinstance(x, dict) and x.get("package_ref")], "handoffBindingRefs": [x.get("handoff_ref") for x in (bundle.get("handoff_bindings") or []) if isinstance(x, dict) and x.get("handoff_ref")], "accepted": accepted, "readOnlyContext": True, "automaticWorkbenchMutationAuthorized": False, "specialistObjectsRemainAuthoritative": bool(bundle.get("underlying_objects_remain_authoritative", True))}
    context["contextHash"] = content_hash(context)
    return {"ok": accepted, "schema": BUNDLE_CONTEXT_SCHEMA, "version": VERSION, "context": context}


def _auth(token: Optional[str]) -> None: _authorize_core_route(token)

@router.get("/integration/core/unified-runtime/manifest")
def unified_runtime_manifest(x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _auth(x_sc_service_token); return bridge_manifest()

@router.post("/integration/core/unified-runtime/sessions/build")
def unified_runtime_session_build(request: SessionCreateRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _auth(x_sc_service_token)
    try: return build_session_create(request)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/integration/core/unified-runtime/projects/bind")
def unified_runtime_project_bind(request: ProjectSessionBindRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _auth(x_sc_service_token)
    try: return build_project_session_bindings(request)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/integration/core/unified-runtime/executions/bind")
def unified_runtime_execution_bind(request: ExecutionBindingRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _auth(x_sc_service_token)
    try: return build_execution_binding(request)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/integration/core/unified-runtime/visuals/bind")
def unified_runtime_visual_bind(request: VisualBindingRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _auth(x_sc_service_token)
    try: return build_visual_binding(request)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/integration/core/unified-runtime/validations/bind")
def unified_runtime_validation_bind(request: ValidationBindingRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _auth(x_sc_service_token)
    try: return build_validation_binding(request)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/integration/core/unified-runtime/packages/bind")
def unified_runtime_package_bind(request: PackageBindingRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _auth(x_sc_service_token)
    try: return build_package_binding(request)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/integration/core/unified-runtime/handoffs/bind")
def unified_runtime_handoff_bind(request: HandoffBindingRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _auth(x_sc_service_token)
    try: return build_handoff_binding(request)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post("/integration/core/unified-runtime/bundles/consume")
def unified_runtime_bundle_consume(request: CoreBundleConsumeRequest, x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token")):
    _auth(x_sc_service_token); return consume_core_bundle(request)

@router.get("/v660/status")
def v660_status() -> Dict[str, Any]:
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "release": "Unified Research Project & Session Bridge", "runtimeContractRef": CORE_RUNTIME_CONTRACT, "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT, "twoPhaseSessionBinding": True, "coreSessionIdMustComeFromCore": True, "automaticCoreDispatch": False, "automaticCorePersistence": False, "workbenchProjectRemainsAuthoritative": True}

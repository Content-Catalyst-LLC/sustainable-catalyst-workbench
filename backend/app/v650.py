"""Workbench v6.5.0 — Unified Runtime Contract Adapter.

Implements a deterministic adapter for Platform Core's
``sc.research.unified-runtime-contract.v1`` without granting Platform Core
arbitrary execution authority. The adapter validates declared contract bundles,
exposes a Workbench product-binding manifest, maps canonical Workbench projects
to Core references, consumes Core exchange envelopes into explicit import plans,
and builds Core-compatible exchange/invocation/result records for caller-led
persistence in Platform Core.

The adapter is intentionally non-persistent and non-dispatching in v6.5.0:
Workbench does not mutate Core state, infer Core schemas, authorize products,
certify scientific results, or execute code solely because a Core envelope was
received.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v600 import ProjectBuildRequest, ProjectInput, build_project
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route

VERSION = APP_VERSION
SCHEMA = "sc-workbench-core-runtime-adapter/1.0"
PRODUCT_BINDING_SCHEMA = "sc-workbench-core-product-binding-request/1.0"
PROJECT_MAP_SCHEMA = "sc-workbench-core-project-map/1.0"
EXCHANGE_ADAPTER_SCHEMA = "sc-workbench-core-exchange-adapter/1.0"
CORE_REQUEST_SCHEMA = "sc-workbench-core-runtime-request/1.0"
PRODUCT_REF = "product:workbench"
ADAPTER_REF = "workbench:/integration/core/runtime-contract"

CORE_OPERATIONS = {
    "create", "read", "update", "link", "version", "snapshot", "trace",
    "handoff", "package", "validate_external", "list",
}
SUPPORTED_OPERATIONS = {
    "create", "read", "link", "version", "snapshot", "trace", "handoff",
    "package", "validate_external", "list",
}
SUPPORTED_CAPABILITIES = [
    "object:create",
    "object:read",
    "object:link",
    "object:version",
    "object:snapshot",
    "provenance:trace",
    "context:handoff",
    "package:export",
    "validation:record",
]
SUPPORTED_OBJECT_TYPES = [
    "workbench.computational-project",
    "workbench.computational-object",
    "workbench.shared-variable-set",
    "workbench.linked-object-graph",
    "workbench.computational-provenance",
    "workbench.computational-export",
    "workbench.computational-handoff",
    "workbench.execution-result",
]
TARGET_ALIASES = {PRODUCT_REF, PRODUCT_KEY, "service:workbench", "sc:product:workbench"}

router = APIRouter(tags=["workbench-v650-unified-runtime-contract-adapter"])


def _bounded_string(value: Any, limit: int = 512) -> str:
    return str(value or "").strip()[:limit]


def _core_request(path: str, data: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
    record = {
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "contract": CORE_RUNTIME_CONTRACT,
        "method": method,
        "path": path,
        "data": data,
        "automaticDispatchAuthorized": False,
        "callerMustPersistToCore": True,
    }
    record["requestHash"] = content_hash(record)
    return record


def _validate_operation(operation: str, *, outbound: bool = False) -> str:
    op = _bounded_string(operation, 64)
    if op not in CORE_OPERATIONS:
        raise ValueError(f"Unsupported Core runtime operation: {op or '<empty>'}")
    if outbound and op not in SUPPORTED_OPERATIONS:
        raise ValueError(f"Workbench v6.5.0 does not declare support for Core operation: {op}")
    return op


def _normalize_refs(items: List[str]) -> List[str]:
    return sorted({_bounded_string(item, 512) for item in items if _bounded_string(item, 512)})


def adapter_manifest() -> Dict[str, Any]:
    record = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "productRef": PRODUCT_REF,
        "runtime": RUNTIME_KIND,
        "contract": CORE_RUNTIME_CONTRACT,
        "adapterRef": ADAPTER_REF,
        "supportedOperations": sorted(SUPPORTED_OPERATIONS),
        "supportedCapabilities": list(SUPPORTED_CAPABILITIES),
        "supportedObjectTypes": list(SUPPORTED_OBJECT_TYPES),
        "corePaths": {
            "readiness": "/v1/research/runtime-contract/readiness",
            "productBindings": "/v1/research/runtime-contract/product-bindings",
            "exchanges": "/v1/research/runtime-contract/exchanges",
            "invocations": "/v1/research/runtime-contract/invocations",
            "results": "/v1/research/runtime-contract/results",
        },
        "boundaries": {
            "contractSemanticsDeclaredNotInferred": True,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "arbitraryCoreInstructionExecutionAuthorized": False,
            "scientificResultCertificationByAdapter": False,
            "specialistComputationRemainsWorkbenchOwned": True,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


class ContractValidateRequest(BaseModel):
    bundle: Dict[str, Any]


class ProductBindingRequest(BaseModel):
    contractId: str
    bindingKey: str = "workbench-v6-5-0"
    visibility: Literal["private", "internal", "public"] = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ProjectMapRequest(BaseModel):
    project: ProjectInput
    coreProjectRef: str = ""


class ExchangeConsumeRequest(BaseModel):
    exchange: Dict[str, Any]


class ExchangeBuildRequest(BaseModel):
    contractId: str
    projectRef: str
    targetProductRef: str
    operation: str = "handoff"
    objectRefs: List[str] = Field(default_factory=list)
    contextRef: str = ""
    workflowRef: str = ""
    provenanceRefs: List[str] = Field(default_factory=list)
    exchangeKey: str = ""
    status: str = "declared"
    visibility: Literal["private", "internal", "public"] = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("targetProductRef")
    @classmethod
    def target_required(cls, value: str) -> str:
        value = _bounded_string(value, 256)
        if not value:
            raise ValueError("targetProductRef is required")
        return value


class InvocationBuildRequest(BaseModel):
    contractId: str
    projectRef: str
    operation: str
    inputRefs: List[str] = Field(default_factory=list)
    invocationKey: str = ""
    exchangeId: str = ""
    runtimeRef: str = ""
    status: str = "recorded"
    visibility: Literal["private", "internal", "public"] = "internal"
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ResultBuildRequest(BaseModel):
    invocationId: str
    projectRef: str
    resultType: str
    objectRef: str
    resultKey: str = ""
    objectVersionRef: str = ""
    contentHash: str = ""
    resultPayload: Any = None
    status: str = "declared"
    visibility: Literal["private", "internal", "public"] = "internal"
    provenance: Dict[str, Any] = Field(default_factory=dict)


def validate_contract_bundle(request: ContractValidateRequest) -> Dict[str, Any]:
    bundle = request.bundle or {}
    declared_schema = bundle.get("contract_schema") or bundle.get("contract")
    contract = bundle.get("contract") if isinstance(bundle.get("contract"), dict) else {}
    if isinstance(declared_schema, dict):
        declared_schema = bundle.get("contract_schema", "")
    required = _normalize_refs(list(contract.get("required_capabilities") or []))
    operations = bundle.get("operations") or []
    declared_ops = []
    unknown_ops = []
    for raw in operations:
        if not isinstance(raw, dict):
            continue
        op = _bounded_string(raw.get("operation"), 64)
        if not op:
            continue
        declared_ops.append(op)
        if op not in CORE_OPERATIONS:
            unknown_ops.append(op)
    missing = sorted(set(required) - set(SUPPORTED_CAPABILITIES))
    unsupported_declared = sorted(set(declared_ops) - SUPPORTED_OPERATIONS)
    schema_ok = declared_schema == CORE_RUNTIME_CONTRACT
    version = _bounded_string(contract.get("contract_version") or contract.get("schema_version"), 32)
    report = {
        "ok": bool(schema_ok and not unknown_ops),
        "schema": SCHEMA,
        "version": VERSION,
        "contract": CORE_RUNTIME_CONTRACT,
        "declaredContractSchema": declared_schema or "",
        "declaredContractVersion": version,
        "schemaCompatible": schema_ok,
        "requiredCapabilities": required,
        "supportedCapabilities": list(SUPPORTED_CAPABILITIES),
        "missingRequiredCapabilities": missing,
        "declaredOperations": sorted(set(declared_ops)),
        "unknownDeclaredOperations": sorted(set(unknown_ops)),
        "declaredOperationsNotImplementedByWorkbench": unsupported_declared,
        "declaredCompatibility": bool(schema_ok and not missing and not unknown_ops),
        "compatibilityIsDeclaredCapabilityComparisonNotScientificCertification": True,
        "contractSemanticsDeclaredNotInferred": True,
    }
    report["validationHash"] = content_hash(report)
    return report


def build_product_binding(request: ProductBindingRequest) -> Dict[str, Any]:
    contract_id = _bounded_string(request.contractId, 128)
    if not contract_id:
        raise ValueError("contractId is required")
    data = {
        "binding_key": _bounded_string(request.bindingKey, 160) or "workbench-v6-5-0",
        "contract_id": contract_id,
        "product_ref": PRODUCT_REF,
        "product_version": VERSION,
        "adapter_ref": ADAPTER_REF,
        "supported_capabilities": list(SUPPORTED_CAPABILITIES),
        "supported_object_types": list(SUPPORTED_OBJECT_TYPES),
        "status": "declared",
        "visibility": request.visibility,
        "metadata": {
            "workbenchRuntime": RUNTIME_KIND,
            "automaticDispatchAuthorized": False,
            **request.metadata,
        },
        "provenance": {
            "adapter": SCHEMA,
            "adapterVersion": VERSION,
            **request.provenance,
        },
    }
    return {
        "ok": True,
        "schema": PRODUCT_BINDING_SCHEMA,
        "version": VERSION,
        "productBinding": data,
        "coreRequest": _core_request("/v1/research/runtime-contract/product-bindings", data),
    }


def map_project(request: ProjectMapRequest) -> Dict[str, Any]:
    built = build_project(ProjectBuildRequest(project=request.project))
    project = built["project"]
    project_ref = _bounded_string(request.coreProjectRef, 512) or f"sc://workbench/project/{project['projectId']}"
    objects = []
    for item in project["objects"]:
        objects.append({
            "objectId": item["objectId"],
            "objectRef": f"sc://workbench/object/{project['projectId']}/{item['objectId']}",
            "objectType": "workbench.computational-object",
            "kind": item["kind"],
            "studio": item["studio"],
            "contentHash": item["objectHash"],
            "sourceSchema": item["sourceSchema"],
            "sourceVersion": item["sourceVersion"],
        })
    result = {
        "ok": built["ok"],
        "schema": PROJECT_MAP_SCHEMA,
        "version": VERSION,
        "contract": CORE_RUNTIME_CONTRACT,
        "projectRef": project_ref,
        "workbenchProjectId": project["projectId"],
        "workbenchProjectHash": project["projectHash"],
        "projectObjectRef": f"sc://workbench/project/{project['projectId']}",
        "projectObjectType": "workbench.computational-project",
        "objectRefs": [item["objectRef"] for item in objects],
        "objects": objects,
        "variableSetRef": f"sc://workbench/variables/{project['projectId']}/{project['projectHash'][:16]}",
        "integrityIssues": project["integrityIssues"],
        "automaticCorePersistenceAuthorized": False,
    }
    result["mappingHash"] = content_hash(result)
    return result


def consume_exchange(request: ExchangeConsumeRequest) -> Dict[str, Any]:
    exchange = dict(request.exchange or {})
    target = _bounded_string(exchange.get("target_product_ref"), 256)
    operation = _validate_operation(exchange.get("operation", ""), outbound=False)
    object_refs = _normalize_refs(list(exchange.get("object_refs") or []))
    accepted_target = target in TARGET_ALIASES
    supported_operation = operation in SUPPORTED_OPERATIONS
    plan = {
        "schema": EXCHANGE_ADAPTER_SCHEMA,
        "version": VERSION,
        "contract": CORE_RUNTIME_CONTRACT,
        "exchangeId": _bounded_string(exchange.get("id"), 128),
        "exchangeKey": _bounded_string(exchange.get("exchange_key"), 256),
        "contractId": _bounded_string(exchange.get("contract_id"), 128),
        "projectRef": _bounded_string(exchange.get("project_ref"), 512),
        "sourceProductRef": _bounded_string(exchange.get("source_product_ref"), 256),
        "targetProductRef": target,
        "operation": operation,
        "objectRefs": object_refs,
        "contextRef": _bounded_string(exchange.get("context_ref"), 512),
        "workflowRef": _bounded_string(exchange.get("workflow_ref"), 512),
        "provenanceRefs": _normalize_refs(list(exchange.get("provenance_refs") or [])),
        "envelopeHash": _bounded_string(exchange.get("envelope_hash"), 128),
        "acceptedTarget": accepted_target,
        "supportedOperation": supported_operation,
        "accepted": bool(accepted_target and supported_operation),
        "importPlan": {
            "resolveObjectReferences": bool(object_refs),
            "preserveProjectReference": True,
            "preserveProvenanceReferences": True,
            "requiresExplicitSpecialistOperationSelection": operation in {"handoff", "create", "read"},
            "requiresExplicitExecutionRequest": True,
            "automaticExecutionAuthorized": False,
        },
        "metadata": exchange.get("metadata") if isinstance(exchange.get("metadata"), dict) else {},
    }
    plan["adapterHash"] = content_hash(plan)
    return {"ok": plan["accepted"], "schema": EXCHANGE_ADAPTER_SCHEMA, "version": VERSION, "result": plan}


def build_exchange(request: ExchangeBuildRequest) -> Dict[str, Any]:
    operation = _validate_operation(request.operation, outbound=True)
    project_ref = _bounded_string(request.projectRef, 512)
    contract_id = _bounded_string(request.contractId, 128)
    if not contract_id or not project_ref:
        raise ValueError("contractId and projectRef are required")
    object_refs = _normalize_refs(request.objectRefs)
    key = _bounded_string(request.exchangeKey, 256) or content_hash({
        "project": project_ref, "target": request.targetProductRef, "operation": operation, "objects": object_refs
    })[:32]
    data = {
        "exchange_key": key,
        "contract_id": contract_id,
        "project_ref": project_ref,
        "source_product_ref": PRODUCT_REF,
        "target_product_ref": request.targetProductRef,
        "operation": operation,
        "object_refs": object_refs,
        "context_ref": _bounded_string(request.contextRef, 512) or None,
        "workflow_ref": _bounded_string(request.workflowRef, 512) or None,
        "provenance_refs": _normalize_refs(request.provenanceRefs),
        "status": _bounded_string(request.status, 64) or "declared",
        "visibility": request.visibility,
        "metadata": {"sourceAdapter": SCHEMA, **request.metadata},
    }
    return {
        "ok": True,
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "exchange": data,
        "coreRequest": _core_request("/v1/research/runtime-contract/exchanges", data),
    }


def build_invocation(request: InvocationBuildRequest) -> Dict[str, Any]:
    operation = _validate_operation(request.operation, outbound=True)
    contract_id = _bounded_string(request.contractId, 128)
    project_ref = _bounded_string(request.projectRef, 512)
    if not contract_id or not project_ref:
        raise ValueError("contractId and projectRef are required")
    input_refs = _normalize_refs(request.inputRefs)
    runtime_ref = _bounded_string(request.runtimeRef, 256) or f"sc://workbench/runtime/{VERSION}"
    key = _bounded_string(request.invocationKey, 256) or content_hash({
        "project": project_ref, "operation": operation, "inputs": input_refs, "runtime": runtime_ref
    })[:32]
    data = {
        "invocation_key": key,
        "contract_id": contract_id,
        "project_ref": project_ref,
        "exchange_id": _bounded_string(request.exchangeId, 128) or None,
        "caller_ref": PRODUCT_REF,
        "operation": operation,
        "input_refs": input_refs,
        "runtime_ref": runtime_ref,
        "status": _bounded_string(request.status, 64) or "recorded",
        "visibility": request.visibility,
        "provenance": {"adapter": SCHEMA, "workbenchVersion": VERSION, **request.provenance},
    }
    return {
        "ok": True,
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "invocation": data,
        "coreRequest": _core_request("/v1/research/runtime-contract/invocations", data),
    }


def build_result(request: ResultBuildRequest) -> Dict[str, Any]:
    invocation_id = _bounded_string(request.invocationId, 128)
    project_ref = _bounded_string(request.projectRef, 512)
    result_type = _bounded_string(request.resultType, 160)
    object_ref = _bounded_string(request.objectRef, 512)
    if not invocation_id or not project_ref or not result_type or not object_ref:
        raise ValueError("invocationId, projectRef, resultType, and objectRef are required")
    generated_hash = _bounded_string(request.contentHash, 128)
    if not generated_hash and request.resultPayload is not None:
        generated_hash = content_hash(request.resultPayload)
    key = _bounded_string(request.resultKey, 256) or content_hash({
        "invocation": invocation_id, "project": project_ref, "object": object_ref, "hash": generated_hash
    })[:32]
    data = {
        "result_key": key,
        "invocation_id": invocation_id,
        "project_ref": project_ref,
        "result_type": result_type,
        "object_ref": object_ref,
        "object_version_ref": _bounded_string(request.objectVersionRef, 256) or None,
        "content_hash": generated_hash or None,
        "status": _bounded_string(request.status, 64) or "declared",
        "visibility": request.visibility,
        "provenance": {"adapter": SCHEMA, "workbenchVersion": VERSION, **request.provenance},
    }
    return {
        "ok": True,
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "resultBinding": data,
        "coreRequest": _core_request("/v1/research/runtime-contract/results", data),
    }


def _auth(token: Optional[str]) -> None:
    _authorize_core_route(token)


@router.get("/integration/core/runtime-contract/manifest")
def runtime_contract_manifest(
    x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _auth(x_sc_service_token)
    return adapter_manifest()


@router.post("/integration/core/runtime-contract/validate")
def runtime_contract_validate(
    request: ContractValidateRequest,
    x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _auth(x_sc_service_token)
    return validate_contract_bundle(request)


@router.post("/integration/core/runtime-contract/product-binding")
def runtime_contract_product_binding(
    request: ProductBindingRequest,
    x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _auth(x_sc_service_token)
    try:
        return build_product_binding(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/integration/core/runtime-contract/project/map")
def runtime_contract_project_map(
    request: ProjectMapRequest,
    x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _auth(x_sc_service_token)
    return map_project(request)


@router.post("/integration/core/runtime-contract/exchanges/consume")
def runtime_contract_exchange_consume(
    request: ExchangeConsumeRequest,
    x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _auth(x_sc_service_token)
    try:
        return consume_exchange(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/integration/core/runtime-contract/exchanges/build")
def runtime_contract_exchange_build(
    request: ExchangeBuildRequest,
    x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _auth(x_sc_service_token)
    try:
        return build_exchange(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/integration/core/runtime-contract/invocations/build")
def runtime_contract_invocation_build(
    request: InvocationBuildRequest,
    x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _auth(x_sc_service_token)
    try:
        return build_invocation(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/integration/core/runtime-contract/results/build")
def runtime_contract_result_build(
    request: ResultBuildRequest,
    x_sc_service_token: Optional[str] = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _auth(x_sc_service_token)
    try:
        return build_result(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/v650/status")
def v650_status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Unified Runtime Contract Adapter",
        "contract": CORE_RUNTIME_CONTRACT,
        "productRef": PRODUCT_REF,
        "supportedOperations": sorted(SUPPORTED_OPERATIONS),
        "supportedCapabilities": list(SUPPORTED_CAPABILITIES),
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
        "specialistComputationRemainsWorkbenchOwned": True,
    }

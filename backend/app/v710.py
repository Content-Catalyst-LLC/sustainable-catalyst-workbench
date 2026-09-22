"""Workbench v7.1.0 — Unified Execution Object Model.

v7.1 turns v7.0 unified execution results and workflows into one portable,
content-addressed execution object.  The object preserves declared inputs,
parameters, runtime/environment identity, dependencies, outputs, result hashes,
provenance, and Platform Core binding metadata without introducing a second
execution engine or hidden persistence layer.

Scientific result content is immutable across object revisions.  Revisions may
change descriptive metadata only; Workbench does not silently recompute,
replace, certify, rank, or promote specialist results to truth.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v650 import CORE_RUNTIME_CONTRACT
from .v660 import CORE_UNIFIED_RUNTIME_CONTRACT
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT
from .v700 import (
    RESULT_SCHEMA,
    WORKFLOW_SCHEMA,
    RUNTIME_REF,
    UnifiedExecutionRequest,
    WorkflowRequest,
    _execute_request,
    execute_workflow,
    _stable_result_basis,
)

VERSION = APP_VERSION
SCHEMA = "sc-workbench-unified-execution-object-model/1.0"
OBJECT_SCHEMA = "sc-workbench-execution-object/1.0"
VALIDATION_SCHEMA = "sc-workbench-execution-object-validation/1.0"
REVISION_SCHEMA = "sc-workbench-execution-object-revision/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-execution-object-core-binding-plan/1.0"
CORE_RESEARCH_RUNTIME_CONTRACT = "sc.research.unified-research-scientific-investigation-runtime.v1"
OBJECT_MODEL_REF = "workbench:/execution/object-model"
router = APIRouter(tags=["workbench-v710-unified-execution-object-model"])


class ExecutionObjectProjectionRequest(BaseModel):
    source: Dict[str, Any]
    objectKey: str = Field(default="", max_length=180)
    label: str = Field(default="", max_length=400)
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    datasetRefs: List[str] = Field(default_factory=list, max_length=200)
    environmentRefs: List[str] = Field(default_factory=list, max_length=100)
    methodRefs: List[str] = Field(default_factory=list, max_length=100)
    parentExecutionRefs: List[str] = Field(default_factory=list, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionObjectRevisionRequest(BaseModel):
    executionObject: Dict[str, Any]
    reason: str = Field(min_length=1, max_length=1000)
    label: str = Field(default="", max_length=400)
    addTags: List[str] = Field(default_factory=list, max_length=100)
    metadataPatch: Dict[str, Any] = Field(default_factory=dict)
    revisedBy: str = Field(default="workbench-v7.1.0", max_length=180)


class CoreExecutionObjectBindingPlanRequest(BaseModel):
    executionObject: Dict[str, Any]
    coreRuntimeSessionId: str = Field(default="", max_length=128)
    coreRuntimeContractId: str = Field(default="", max_length=128)
    coreInvocationId: str = Field(default="", max_length=128)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench-v7.1.0", max_length=180)


class ValidationRequest(BaseModel):
    executionObject: Dict[str, Any]


def _bounded(values: List[str], limit: int = 1000) -> List[str]:
    return sorted({str(v).strip()[:limit] for v in values if str(v).strip()})


def _stable_hash(value: Any) -> str:
    return content_hash(_stable_result_basis(value))


def _without_object_hash(value: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(value)
    out.pop("objectHash", None)
    return out


def _object_hash(value: Dict[str, Any]) -> str:
    return _stable_hash(_without_object_hash(value))


def object_model_manifest() -> Dict[str, Any]:
    record = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Unified Execution Object Model",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "objectModelRef": OBJECT_MODEL_REF,
        "objectSchema": OBJECT_SCHEMA,
        "sourceSchemas": [RESULT_SCHEMA, WORKFLOW_SCHEMA],
        "coreContracts": {
            "runtimeContract": CORE_RUNTIME_CONTRACT,
            "unifiedResearchRuntime": CORE_RESEARCH_RUNTIME_CONTRACT,
            "unifiedSessionBridge": CORE_UNIFIED_RUNTIME_CONTRACT,
            "computationLineage": CORE_COMPUTATION_LINEAGE_CONTRACT,
        },
        "capabilities": {
            "singleExecutionObjects": True,
            "workflowExecutionObjects": True,
            "deterministicObjectIdentity": True,
            "contentAddressedObjectHash": True,
            "explicitObjectRevisions": True,
            "resultContentImmutableAcrossRevisions": True,
            "dependencyGraphPreservation": True,
            "inputParameterEnvironmentOutputModel": True,
            "objectIntegrityValidation": True,
            "coreExecutionBindingPlanning": True,
            "coreRuntimeInvocationPlanning": True,
            "portableReferenceFirstProjection": True,
        },
        "boundaries": {
            "automaticPersistenceAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "automaticExecutionReplayAuthorized": False,
            "resultMutationDuringRevisionAuthorized": False,
            "arbitraryCodeExecutionAuthorized": False,
            "scientificValidityCertificationAuthorized": False,
            "reproducibilityCertificationAuthorized": False,
            "truthDeterminationAuthorized": False,
            "recommendationOrRankingAuthorized": False,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


def _execution_object_from_result(
    source: Dict[str, Any],
    *,
    declared_request: Dict[str, Any] | None = None,
    object_key: str = "",
    label: str = "",
    project_ref: str = "",
    core_session_id: str = "",
    dataset_refs: List[str] | None = None,
    environment_refs: List[str] | None = None,
    method_refs: List[str] | None = None,
    parent_refs: List[str] | None = None,
    tags: List[str] | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if source.get("schema") != RESULT_SCHEMA:
        raise ValueError(f"source must use {RESULT_SCHEMA}")
    if not source.get("executionRef") or not source.get("resultHash"):
        raise ValueError("source execution result is missing executionRef or resultHash")

    declared_request = declared_request or {}
    payload = declared_request.get("payload") if isinstance(declared_request.get("payload"), dict) else None
    input_refs = _bounded(list(source.get("inputRefs") or []) + list(declared_request.get("inputRefs") or []))
    dataset_refs = _bounded(dataset_refs or [])
    environment_refs = _bounded(environment_refs or [])
    method_refs = _bounded((method_refs or []) + [f"{RUNTIME_REF}/operation/{source.get('operation')}"])
    parent_refs = _bounded(parent_refs or [])
    tags = _bounded(list(tags or []) + list(declared_request.get("tags") or []), 180)
    project = project_ref or str(source.get("projectRef") or declared_request.get("projectRef") or "")
    session = core_session_id or str(source.get("coreSessionId") or declared_request.get("coreSessionId") or "")

    identity_basis = {
        "sourceExecutionRef": source.get("executionRef"),
        "sourceRequestHash": source.get("requestHash"),
        "sourceResultHash": source.get("resultHash"),
        "objectKey": object_key,
        "projectRef": project,
    }
    object_id = "wbeo-" + content_hash(identity_basis)[:24]
    object_ref = f"sc://workbench/execution-object/{object_id}"
    output_ref = str(source.get("outputRef") or "")
    raw_result = source.get("result")
    status = "completed" if source.get("ok", True) else "failed"

    obj = {
        "ok": True,
        "schema": OBJECT_SCHEMA,
        "version": VERSION,
        "objectId": object_id,
        "objectRef": object_ref,
        "objectKey": object_key or str(source.get("requestKey") or object_id),
        "objectKind": "single_execution",
        "revision": 1,
        "previousObjectHash": None,
        "label": label or str(source.get("label") or source.get("operation") or "Execution"),
        "status": status,
        "terminal": True,
        "projectRef": project,
        "coreSessionId": session,
        "runtime": {
            "product": PRODUCT_KEY,
            "runtimeKind": source.get("runtimeKind", "workbench"),
            "runtimeRef": source.get("runtimeRef", RUNTIME_REF),
            "runtimeVersion": VERSION,
            "specialistSourceRelease": source.get("sourceRelease"),
        },
        "method": {
            "operation": source.get("operation"),
            "category": source.get("category"),
            "executionType": source.get("executionType"),
            "methodRefs": method_refs,
            "deterministicOperation": bool(source.get("deterministicOperation", True)),
        },
        "inputs": {
            "inputRefs": input_refs,
            "datasetRefs": dataset_refs,
            "declaredPayload": payload,
            "payloadHash": content_hash(payload) if payload is not None else None,
            "requestHash": source.get("requestHash"),
            "fidelity": "declared_payload_and_references" if payload is not None else "reference_hash_only",
        },
        "parameters": {
            "requestKey": declared_request.get("requestKey") or source.get("requestKey"),
            "metadata": declared_request.get("metadata", {}),
        },
        "environment": {
            "environmentRefs": environment_refs,
            "runtimeEnvironmentRef": f"sc://workbench/runtime/{VERSION}",
            "environmentHash": content_hash({"runtime": source.get("runtimeRef", RUNTIME_REF), "version": VERSION, "environmentRefs": environment_refs}),
        },
        "dependencies": {
            "parentExecutionRefs": parent_refs,
            "edges": [{"from": p, "to": object_ref, "relation": "precedes"} for p in parent_refs],
        },
        "outputs": [{
            "outputRef": output_ref,
            "outputType": source.get("outputType", "result_bundle"),
            "contentHash": source.get("resultHash"),
            "resultSchema": raw_result.get("schema") if isinstance(raw_result, dict) else None,
            "inlineResult": raw_result,
        }],
        "lineage": {
            "workbenchExecutionRefs": [str(source.get("executionRef"))],
            "executionEnvelopeHash": source.get("executionEnvelopeHash"),
            "coreLineageReady": True,
            "coreExecutionId": None,
        },
        "provenance": {
            "sourceSchema": source.get("schema"),
            "sourceVersion": source.get("version"),
            "sourceExecutionId": source.get("executionId"),
            "sourceExecutionRef": source.get("executionRef"),
            "sourceRequestHash": source.get("requestHash"),
            "sourceResultHash": source.get("resultHash"),
            "projectionMode": "execute-and-project" if declared_request else "reference-first-project",
        },
        "tags": tags,
        "metadata": metadata or {},
        "boundaries": {
            "resultContentImmutable": True,
            "automaticPersistencePerformed": False,
            "automaticCoreDispatchPerformed": False,
            "automaticCorePersistencePerformed": False,
            "automaticExecutionReplayPerformed": False,
            "scientificValidityCertified": False,
            "reproducibilityCertified": False,
            "truthDetermined": False,
            "recommendationOrRankingPerformed": False,
        },
    }
    obj["objectHash"] = _object_hash(obj)
    return obj


def _workflow_object_from_result(
    source: Dict[str, Any],
    *,
    declared_request: Dict[str, Any] | None = None,
    object_key: str = "",
    label: str = "",
    project_ref: str = "",
    core_session_id: str = "",
    dataset_refs: List[str] | None = None,
    environment_refs: List[str] | None = None,
    method_refs: List[str] | None = None,
    parent_refs: List[str] | None = None,
    tags: List[str] | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if source.get("schema") != WORKFLOW_SCHEMA:
        raise ValueError(f"source must use {WORKFLOW_SCHEMA}")
    if not source.get("workflowHash"):
        raise ValueError("source workflow result is missing workflowHash")

    declared_request = declared_request or {}
    step_requests = {str(s.get("stepId")): s for s in declared_request.get("steps", []) if isinstance(s, dict)}
    project = project_ref or str(source.get("projectRef") or declared_request.get("projectRef") or "")
    session = core_session_id or str(source.get("coreSessionId") or declared_request.get("coreSessionId") or "")
    workflow_key = str(source.get("workflowKey") or declared_request.get("workflowKey") or "workbench-unified-workflow")
    identity_basis = {"workflowKey": workflow_key, "workflowHash": source.get("workflowHash"), "objectKey": object_key, "projectRef": project}
    object_id = "wbeo-" + content_hash(identity_basis)[:24]
    object_ref = f"sc://workbench/execution-object/{object_id}"

    child_objects: List[Dict[str, Any]] = []
    step_to_ref: Dict[str, str] = {}
    for result in source.get("results", []):
        if not isinstance(result, dict) or result.get("schema") != RESULT_SCHEMA or not result.get("executionRef"):
            continue
        step_id = str(result.get("workflowStepId") or "")
        step_decl = step_requests.get(step_id, {})
        child = _execution_object_from_result(
            result,
            declared_request={
                "payload": step_decl.get("payload", {}),
                "inputRefs": step_decl.get("inputRefs", []),
                "requestKey": f"{workflow_key}:{step_id}" if step_id else result.get("requestKey"),
                "metadata": step_decl.get("metadata", {}),
            } if step_decl else None,
            object_key=f"{workflow_key}:{step_id}" if step_id else "",
            label=str(result.get("label") or step_decl.get("label") or step_id),
            project_ref=project,
            core_session_id=session,
            dataset_refs=dataset_refs or [],
            environment_refs=environment_refs or [],
            method_refs=method_refs or [],
            parent_refs=[],
            tags=tags or [],
            metadata={"workflowKey": workflow_key, "workflowStepId": step_id},
        )
        child_objects.append(child)
        if step_id:
            step_to_ref[step_id] = child["objectRef"]

    edges: List[Dict[str, Any]] = []
    for result in source.get("results", []):
        if not isinstance(result, dict):
            continue
        target = step_to_ref.get(str(result.get("workflowStepId") or ""))
        if not target:
            continue
        for dep in result.get("dependsOn", []) or []:
            dep_ref = step_to_ref.get(str(dep))
            if dep_ref:
                edges.append({"from": dep_ref, "to": target, "relation": "depends_on"})

    outputs = []
    for child in child_objects:
        outputs.extend(child.get("outputs", []))

    obj = {
        "ok": True,
        "schema": OBJECT_SCHEMA,
        "version": VERSION,
        "objectId": object_id,
        "objectRef": object_ref,
        "objectKey": object_key or workflow_key,
        "objectKind": "workflow_execution",
        "revision": 1,
        "previousObjectHash": None,
        "label": label or workflow_key,
        "status": "completed" if source.get("ok", False) else "failed",
        "terminal": True,
        "projectRef": project,
        "coreSessionId": session,
        "runtime": {"product": PRODUCT_KEY, "runtimeKind": "workbench", "runtimeRef": RUNTIME_REF, "runtimeVersion": VERSION},
        "method": {
            "operation": "workflow.run",
            "category": "scientific-engineering-workflow",
            "executionType": "workflow",
            "methodRefs": _bounded((method_refs or []) + [f"{RUNTIME_REF}/workflow"]),
            "deterministicOperation": True,
        },
        "inputs": {
            "inputRefs": _bounded([r for s in declared_request.get("steps", []) if isinstance(s, dict) for r in s.get("inputRefs", [])]),
            "datasetRefs": _bounded(dataset_refs or []),
            "declaredWorkflow": declared_request if declared_request else None,
            "payloadHash": content_hash(declared_request) if declared_request else None,
            "requestHash": source.get("workflowHash"),
            "fidelity": "declared_workflow_and_references" if declared_request else "reference_hash_only",
        },
        "parameters": {"workflowKey": workflow_key, "stopOnFailure": declared_request.get("stopOnFailure") if declared_request else None},
        "environment": {
            "environmentRefs": _bounded(environment_refs or []),
            "runtimeEnvironmentRef": f"sc://workbench/runtime/{VERSION}",
            "environmentHash": content_hash({"runtime": RUNTIME_REF, "version": VERSION, "environmentRefs": _bounded(environment_refs or [])}),
        },
        "dependencies": {
            "parentExecutionRefs": _bounded(parent_refs or []),
            "edges": edges + [{"from": p, "to": object_ref, "relation": "precedes"} for p in _bounded(parent_refs or [])],
            "dependencyOrder": source.get("dependencyOrder", []),
        },
        "outputs": outputs,
        "children": child_objects,
        "lineage": {
            "workbenchExecutionRefs": [ref for c in child_objects for ref in c.get("lineage", {}).get("workbenchExecutionRefs", [])],
            "workflowHash": source.get("workflowHash"),
            "coreLineageReady": True,
            "coreExecutionId": None,
        },
        "provenance": {
            "sourceSchema": source.get("schema"),
            "sourceVersion": source.get("version"),
            "sourceWorkflowKey": workflow_key,
            "sourceWorkflowHash": source.get("workflowHash"),
            "projectionMode": "execute-and-project" if declared_request else "reference-first-project",
        },
        "tags": _bounded(tags or [], 180),
        "metadata": metadata or {},
        "boundaries": {
            "resultContentImmutable": True,
            "automaticPersistencePerformed": False,
            "automaticCoreDispatchPerformed": False,
            "automaticCorePersistencePerformed": False,
            "automaticExecutionReplayPerformed": False,
            "hiddenOutputSubstitutionPerformed": False,
            "scientificValidityCertified": False,
            "reproducibilityCertified": False,
            "truthDetermined": False,
            "recommendationOrRankingPerformed": False,
        },
    }
    obj["objectHash"] = _object_hash(obj)
    return obj


def project_execution_object(request: ExecutionObjectProjectionRequest) -> Dict[str, Any]:
    try:
        if request.source.get("schema") == RESULT_SCHEMA:
            return _execution_object_from_result(
                request.source,
                object_key=request.objectKey,
                label=request.label,
                project_ref=request.projectRef,
                core_session_id=request.coreSessionId,
                dataset_refs=request.datasetRefs,
                environment_refs=request.environmentRefs,
                method_refs=request.methodRefs,
                parent_refs=request.parentExecutionRefs,
                tags=request.tags,
                metadata=request.metadata,
            )
        if request.source.get("schema") == WORKFLOW_SCHEMA:
            return _workflow_object_from_result(
                request.source,
                object_key=request.objectKey,
                label=request.label,
                project_ref=request.projectRef,
                core_session_id=request.coreSessionId,
                dataset_refs=request.datasetRefs,
                environment_refs=request.environmentRefs,
                method_refs=request.methodRefs,
                parent_refs=request.parentExecutionRefs,
                tags=request.tags,
                metadata=request.metadata,
            )
        raise ValueError(f"source schema must be {RESULT_SCHEMA} or {WORKFLOW_SCHEMA}")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def validate_execution_object(value: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    if not isinstance(value, dict):
        issues.append("execution object must be a JSON object")
        value = {}
    if value.get("schema") != OBJECT_SCHEMA:
        issues.append(f"schema must be {OBJECT_SCHEMA}")
    if value.get("version") != VERSION:
        issues.append(f"version must be {VERSION}")
    if value.get("objectKind") not in {"single_execution", "workflow_execution"}:
        issues.append("objectKind is unsupported")
    object_id = str(value.get("objectId") or "")
    object_ref = str(value.get("objectRef") or "")
    if not object_id or object_ref != f"sc://workbench/execution-object/{object_id}":
        issues.append("object identity/reference mismatch")
    expected_hash = _object_hash(value)
    if value.get("objectHash") != expected_hash:
        issues.append("objectHash does not match canonical object content")
    if not value.get("outputs"):
        issues.append("execution object must contain at least one output")
    for index, output in enumerate(value.get("outputs") or []):
        if not isinstance(output, dict):
            issues.append(f"output {index} is invalid")
            continue
        if not output.get("outputRef") or not output.get("contentHash"):
            issues.append(f"output {index} is missing reference or content hash")
        if "inlineResult" in output and output.get("inlineResult") is not None:
            if _stable_hash(output.get("inlineResult")) != output.get("contentHash"):
                issues.append(f"output {index} inline result hash mismatch")
    return {
        "ok": not issues,
        "schema": VALIDATION_SCHEMA,
        "version": VERSION,
        "objectRef": value.get("objectRef"),
        "valid": not issues,
        "issues": issues,
        "expectedObjectHash": expected_hash,
        "observedObjectHash": value.get("objectHash"),
        "resultContentMutationDetected": any("inline result hash mismatch" in x for x in issues),
        "scientificValidityCertified": False,
    }


def revise_execution_object(request: ExecutionObjectRevisionRequest) -> Dict[str, Any]:
    validation = validate_execution_object(request.executionObject)
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail={"message": "executionObject failed integrity validation", "issues": validation["issues"]})
    current = request.executionObject
    revised = deepcopy(current)
    revised["revision"] = int(current.get("revision") or 1) + 1
    revised["previousObjectHash"] = current.get("objectHash")
    if request.label:
        revised["label"] = request.label
    revised["tags"] = _bounded(list(current.get("tags") or []) + list(request.addTags), 180)
    revised["metadata"] = {**dict(current.get("metadata") or {}), **request.metadataPatch}
    revised["revisionRecord"] = {
        "schema": REVISION_SCHEMA,
        "reason": request.reason,
        "revisedBy": request.revisedBy,
        "priorObjectHash": current.get("objectHash"),
        "resultContentChanged": False,
    }
    revised["objectHash"] = _object_hash(revised)
    return revised


def build_core_binding_plan(request: CoreExecutionObjectBindingPlanRequest) -> Dict[str, Any]:
    validation = validate_execution_object(request.executionObject)
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail={"message": "executionObject failed integrity validation", "issues": validation["issues"]})
    obj = request.executionObject
    input_refs = _bounded(list(obj.get("inputs", {}).get("inputRefs") or []) + list(obj.get("inputs", {}).get("datasetRefs") or []))
    output_refs = _bounded([str(x.get("outputRef")) for x in obj.get("outputs", []) if isinstance(x, dict) and x.get("outputRef")])
    execution_refs = _bounded(obj.get("lineage", {}).get("workbenchExecutionRefs") or [])
    primary_execution_ref = execution_refs[0] if len(execution_refs) == 1 else obj.get("objectRef")

    scientific_binding = None
    if request.coreRuntimeSessionId:
        scientific_binding = {
            "method": "POST",
            "path": "/v1/research/unified-runtime/execution-bindings",
            "data": {
                "session_id": request.coreRuntimeSessionId,
                "execution_ref": primary_execution_ref,
                "runtime": "workbench",
                "environment_ref": obj.get("environment", {}).get("runtimeEnvironmentRef"),
                "method_ref": (obj.get("method", {}).get("methodRefs") or [OBJECT_MODEL_REF])[0],
                "input_refs": input_refs,
                "output_refs": output_refs,
                "visibility": request.visibility,
                "metadata": {
                    "executionObjectRef": obj.get("objectRef"),
                    "executionObjectHash": obj.get("objectHash"),
                    "objectKind": obj.get("objectKind"),
                    "objectRevision": obj.get("revision"),
                },
            },
            "automaticDispatchAuthorized": False,
        }

    invocation = None
    if request.coreRuntimeContractId:
        invocation = {
            "method": "POST",
            "path": "/v1/research/runtime-contract/invocations",
            "data": {
                "invocation_key": str(obj.get("objectId")),
                "contract_id": request.coreRuntimeContractId,
                "project_ref": str(obj.get("projectRef") or ""),
                "caller_ref": "product:workbench",
                "operation": "trace",
                "input_refs": input_refs,
                "runtime_ref": RUNTIME_REF,
                "status": "recorded",
                "visibility": request.visibility,
                "provenance": {"executionObjectRef": obj.get("objectRef"), "executionObjectHash": obj.get("objectHash")},
            },
            "automaticDispatchAuthorized": False,
        }

    result_binding = None
    if request.coreInvocationId:
        result_binding = {
            "method": "POST",
            "path": "/v1/research/runtime-contract/results",
            "data": {
                "result_key": f"{obj.get('objectId')}:object",
                "invocation_id": request.coreInvocationId,
                "project_ref": str(obj.get("projectRef") or ""),
                "result_type": "workbench_execution_object",
                "object_ref": str(obj.get("objectRef")),
                "object_version_ref": f"{obj.get('objectRef')}?revision={obj.get('revision')}",
                "content_hash": str(obj.get("objectHash")),
                "status": "declared",
                "visibility": request.visibility,
                "provenance": {"runtimeRef": RUNTIME_REF, "createdBy": request.createdBy},
            },
            "automaticDispatchAuthorized": False,
        }

    plan = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "objectRef": obj.get("objectRef"),
        "objectHash": obj.get("objectHash"),
        "coreRuntimeContract": CORE_RUNTIME_CONTRACT,
        "coreUnifiedResearchRuntimeContract": CORE_RESEARCH_RUNTIME_CONTRACT,
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "scientificRuntimeExecutionBinding": scientific_binding,
        "runtimeInvocationRegistration": invocation,
        "runtimeResultBinding": result_binding,
        "coreRuntimeSessionIdProvided": bool(request.coreRuntimeSessionId),
        "coreRuntimeSessionIdMustComeFromCore": not bool(request.coreRuntimeSessionId),
        "coreRuntimeContractIdProvided": bool(request.coreRuntimeContractId),
        "coreInvocationIdProvided": bool(request.coreInvocationId),
        "coreInvocationIdMustComeFromCoreBeforeResultBinding": bool(request.coreRuntimeContractId) and not bool(request.coreInvocationId),
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "automaticExecutionReplayAuthorized": False,
        "scientificValidityCertified": False,
        "reproducibilityCertified": False,
    }
    plan["planHash"] = content_hash(plan)
    return plan


@router.get("/execution/objects/manifest")
def manifest() -> Dict[str, Any]:
    return object_model_manifest()


@router.post("/execution/objects/execute")
def execute_object(request: UnifiedExecutionRequest) -> Dict[str, Any]:
    result = _execute_request(request)
    obj = _execution_object_from_result(
        result,
        declared_request=request.model_dump(),
        object_key=request.requestKey,
        label=request.label,
        project_ref=request.projectRef,
        core_session_id=request.coreSessionId,
        tags=request.tags,
        metadata=request.metadata,
    )
    return {"ok": True, "schema": "sc-workbench-execution-object-execution/1.0", "version": VERSION, "executionObject": obj, "executionResult": result}


@router.post("/execution/objects/workflow/run")
def run_workflow_object(request: WorkflowRequest) -> Dict[str, Any]:
    result = execute_workflow(request)
    obj = _workflow_object_from_result(
        result,
        declared_request=request.model_dump(),
        object_key=request.workflowKey,
        project_ref=request.projectRef,
        core_session_id=request.coreSessionId,
        metadata=request.metadata,
    )
    return {"ok": result.get("ok", False), "schema": "sc-workbench-execution-object-workflow/1.0", "version": VERSION, "executionObject": obj, "workflowResult": result}


@router.post("/execution/objects/project")
def project_object(request: ExecutionObjectProjectionRequest) -> Dict[str, Any]:
    return project_execution_object(request)


@router.post("/execution/objects/validate")
def validate_object(request: ValidationRequest) -> Dict[str, Any]:
    return validate_execution_object(request.executionObject)


@router.post("/execution/objects/revise")
def revise_object(request: ExecutionObjectRevisionRequest) -> Dict[str, Any]:
    return revise_execution_object(request)


@router.post("/integration/core/execution-objects/binding/plan")
def core_binding_plan(
    request: CoreExecutionObjectBindingPlanRequest,
    x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token"),
) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return build_core_binding_plan(request)


@router.get("/v710/status")
def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Unified Execution Object Model",
        "objectSchema": OBJECT_SCHEMA,
        "singleExecutionObjects": True,
        "workflowExecutionObjects": True,
        "deterministicObjectIdentity": True,
        "contentAddressedIntegrity": True,
        "explicitObjectRevisions": True,
        "resultContentImmutableAcrossRevisions": True,
        "dependencyGraphPreservation": True,
        "coreBindingPlanning": True,
        "automaticPersistence": False,
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
        "automaticExecutionReplay": False,
        "scientificValidityCertification": False,
        "truthDetermination": False,
    }

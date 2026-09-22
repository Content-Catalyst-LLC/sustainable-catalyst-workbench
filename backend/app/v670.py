"""Workbench v6.7.0 — Computation, Analysis & Execution Lineage Bridge.

Maps externally executed Workbench computation into Platform Core's exact
``sc.research.computation-analysis-execution-lineage.v1`` persistence contract.
The bridge is reference-first and two-phase: Workbench first prepares a Core
execution-registration request; Core returns the authoritative execution id;
Workbench then prepares input, parameter, assumption, environment, ordered
step, output, research-binding, dependency, verification, revision, snapshot,
and unified-session execution-binding requests against that id.

No v6.7 endpoint dispatches HTTP to Core, executes code because Core requested
it, persists Core state, validates scientific truth, or infers reproducibility.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field, field_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route
from .v650 import PRODUCT_REF
from .v660 import (
    CORE_UNIFIED_RUNTIME_CONTRACT,
    ExecutionBindingRequest,
    build_execution_binding,
)

VERSION = APP_VERSION
SCHEMA = "sc-workbench-core-computation-lineage-bridge/1.0"
PLAN_SCHEMA = "sc-workbench-core-computation-lineage-plan/1.0"
CONTEXT_SCHEMA = "sc-workbench-core-computation-lineage-context/1.0"
CORE_REQUEST_SCHEMA = "sc-workbench-core-computation-lineage-request/1.0"
CORE_COMPUTATION_LINEAGE_CONTRACT = "sc.research.computation-analysis-execution-lineage.v1"
BRIDGE_REF = "workbench:/integration/core/computation-lineage"

CORE_PATHS = {
    "readiness": "/v1/research/computation-lineage/readiness",
    "executions": "/v1/research/computation-lineage/executions",
    "inputs": "/v1/research/computation-lineage/executions/{execution_id}/inputs",
    "parameters": "/v1/research/computation-lineage/executions/{execution_id}/parameters",
    "assumptions": "/v1/research/computation-lineage/executions/{execution_id}/assumptions",
    "environments": "/v1/research/computation-lineage/executions/{execution_id}/environments",
    "steps": "/v1/research/computation-lineage/executions/{execution_id}/steps",
    "outputs": "/v1/research/computation-lineage/executions/{execution_id}/outputs",
    "researchBindings": "/v1/research/computation-lineage/executions/{execution_id}/research-bindings",
    "dependencies": "/v1/research/computation-lineage/executions/{execution_id}/dependencies",
    "verifications": "/v1/research/computation-lineage/executions/{execution_id}/verifications",
    "revisions": "/v1/research/computation-lineage/executions/{execution_id}/revisions",
    "snapshots": "/v1/research/computation-lineage/executions/{execution_id}/snapshots",
    "summary": "/v1/research/computation-lineage/executions/{execution_id}/summary",
    "lineage": "/v1/research/computation-lineage/executions/{execution_id}/lineage",
    "bundle": "/v1/research/computation-lineage/executions/{execution_id}/bundle",
    "unifiedSessionExecutionBindings": "/v1/research/unified-runtime/execution-bindings",
}

EXECUTION_TYPES = {
    "data_preparation", "statistical_analysis", "causal_analysis", "simulation",
    "engineering_calculation", "forensic_reconstruction", "ml_training",
    "ml_inference", "forecasting", "optimization", "visualization_transform",
    "notebook", "workflow_step", "other",
}
RUNTIME_KINDS = {"python", "r", "julia", "sql", "workbench", "ml_runtime", "container", "external_service", "manual", "other"}
INPUT_TYPES = {"dataset", "file", "research_object", "source", "model", "parameter_set", "evidence", "artifact", "other"}
OUTPUT_TYPES = {"dataset", "table", "model", "statistic", "prediction", "forecast", "figure", "visualization", "report", "artifact", "log", "result_bundle", "other"}
TARGET_TYPES = {"finding", "claim", "conclusion", "publication", "evidence", "visualization", "hypothesis", "decision", "protocol", "research_object", "other"}

router = APIRouter(tags=["workbench-v670-computation-analysis-execution-lineage"])


def _bounded(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _refs(items: List[str]) -> List[str]:
    return sorted({_bounded(x, 1000) for x in items if _bounded(x, 1000)})


def _core_execution_ref(core_execution_id: str) -> str:
    return f"sc://platform-core/computation-lineage/execution/{_bounded(core_execution_id, 128)}"


def _request(path: str, data: Dict[str, Any], phase: str, method: str = "POST") -> Dict[str, Any]:
    record = {
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "contract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "method": method,
        "path": path,
        "phase": phase,
        "data": data,
        "payload": {"data": data} if method != "GET" else None,
        "automaticDispatchAuthorized": False,
        "callerMustPersistToCore": method != "GET",
    }
    record["requestHash"] = content_hash(record)
    return record


def lineage_manifest() -> Dict[str, Any]:
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
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "corePaths": dict(CORE_PATHS),
        "executionTypes": sorted(EXECUTION_TYPES),
        "runtimeKinds": sorted(RUNTIME_KINDS),
        "bridgeLifecycle": [
            "prepare-execution-registration",
            "persist-execution-in-core",
            "receive-core-execution-id",
            "prepare-lineage-components",
            "bind-core-execution-to-unified-research-session",
            "prepare-revisions-and-immutable-snapshots",
        ],
        "lineageFamilies": [
            "inputs", "parameters", "assumptions", "environments", "ordered-steps",
            "outputs", "research-bindings", "dependencies", "verifications",
            "revisions", "snapshots",
        ],
        "boundaries": {
            "workbenchExecutesSpecialistComputation": True,
            "coreRecordsExternallyExecutedLineage": True,
            "coreExecutionIdMustComeFromCore": True,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "coreExecutesWorkbenchCode": False,
            "coreInfersFindingsOrClaims": False,
            "coreValidatesScientificResults": False,
            "coreInfersReproducibility": False,
            "coreDeterminesTruth": False,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


ExecutionType = Literal[
    "data_preparation", "statistical_analysis", "causal_analysis", "simulation",
    "engineering_calculation", "forensic_reconstruction", "ml_training",
    "ml_inference", "forecasting", "optimization", "visualization_transform",
    "notebook", "workflow_step", "other",
]
RuntimeKind = Literal["python", "r", "julia", "sql", "workbench", "ml_runtime", "container", "external_service", "manual", "other"]
Visibility = Literal["private", "internal", "public"]
ExecutionStatus = Literal["planned", "recorded", "running", "completed", "failed", "cancelled", "archived"]
InputType = Literal["dataset", "file", "research_object", "source", "model", "parameter_set", "evidence", "artifact", "other"]
OutputType = Literal["dataset", "table", "model", "statistic", "prediction", "forecast", "figure", "visualization", "report", "artifact", "log", "result_bundle", "other"]
TargetType = Literal["finding", "claim", "conclusion", "publication", "evidence", "visualization", "hypothesis", "decision", "protocol", "research_object", "other"]


class ExecutionCreateRequest(BaseModel):
    executionKey: str
    title: str
    executionType: ExecutionType = "engineering_calculation"
    runtimeKind: RuntimeKind = "workbench"
    status: ExecutionStatus = "recorded"
    visibility: Visibility = "internal"
    projectRef: str = ""
    coreSessionId: str = ""
    workbenchExecutionRef: str = ""
    protocolId: str = ""
    methodPlanRef: str = ""
    commandOrEntrypoint: str = ""
    codeRef: str = ""
    sourceRevision: str = ""
    startedAt: str = ""
    finishedAt: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"

    @field_validator("executionKey", "title")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = _bounded(value, 400)
        if not value:
            raise ValueError("value is required")
        return value


class InputItem(BaseModel):
    inputKey: str
    inputType: InputType
    objectRef: str
    versionRef: str = ""
    contentHash: str = ""
    role: str = ""
    selector: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"


class ParameterItem(BaseModel):
    parameterKey: str
    value: Any = Field(default_factory=dict)
    unit: str = ""
    sourceRef: str = ""
    sensitivityRole: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"


class AssumptionItem(BaseModel):
    assumptionKey: str
    statementText: str
    protocolAssumptionRef: str = ""
    evidenceRefs: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"


class EnvironmentItem(BaseModel):
    environmentKey: str
    environmentType: str = "workbench"
    runtimeName: str = "Sustainable Catalyst Workbench"
    runtimeVersion: str = VERSION
    osArch: str = ""
    containerImage: str = ""
    environmentHash: str = ""
    dependencyManifestRef: str = ""
    packages: List[str] = Field(default_factory=list)
    hardware: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"


class StepItem(BaseModel):
    stepKey: str
    sequence: int = 0
    stepType: str
    toolRef: str = ""
    operationText: str = ""
    codeRef: str = ""
    inputRefs: List[str] = Field(default_factory=list)
    outputRefs: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"


class OutputItem(BaseModel):
    outputKey: str
    outputType: OutputType
    objectRef: str = ""
    versionRef: str = ""
    contentHash: str = ""
    schemaData: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"


class ResearchBindingItem(BaseModel):
    bindingKey: str
    targetType: TargetType
    targetRef: str
    sourceOutputRef: str = ""
    relation: str = "basis_for"
    bindingRole: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"


class DependencyItem(BaseModel):
    dependencyKey: str
    upstreamExecutionRef: str
    upstreamOutputRef: str = ""
    relation: str = "consumes_output"
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"


class VerificationItem(BaseModel):
    verificationKey: str
    verificationType: str
    status: str = "recorded"
    evidence: Dict[str, Any] = Field(default_factory=dict)
    performedBy: str = ""
    observedAt: str = ""
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"


class ExecutionComponentsRequest(BaseModel):
    coreExecutionId: str
    coreSessionId: str = ""
    projectRef: str = ""
    workbenchExecutionRef: str = ""
    runtime: str = "workbench"
    environmentRef: str = ""
    methodRef: str = ""
    visibility: Visibility = "internal"
    inputs: List[InputItem] = Field(default_factory=list)
    parameters: List[ParameterItem] = Field(default_factory=list)
    assumptions: List[AssumptionItem] = Field(default_factory=list)
    environments: List[EnvironmentItem] = Field(default_factory=list)
    steps: List[StepItem] = Field(default_factory=list)
    outputs: List[OutputItem] = Field(default_factory=list)
    researchBindings: List[ResearchBindingItem] = Field(default_factory=list)
    dependencies: List[DependencyItem] = Field(default_factory=list)
    verifications: List[VerificationItem] = Field(default_factory=list)

    @field_validator("coreExecutionId")
    @classmethod
    def core_execution_required(cls, value: str) -> str:
        value = _bounded(value, 128)
        if not value:
            raise ValueError("coreExecutionId is required and must be returned by Platform Core")
        return value


class SessionExecutionBindingBuildRequest(BaseModel):
    coreExecutionId: str
    coreSessionId: str
    runtime: str = "workbench"
    environmentRef: str = ""
    methodRef: str = ""
    inputRefs: List[str] = Field(default_factory=list)
    outputRefs: List[str] = Field(default_factory=list)
    visibility: Visibility = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("coreExecutionId", "coreSessionId")
    @classmethod
    def core_ids_required(cls, value: str) -> str:
        value = _bounded(value, 128)
        if not value:
            raise ValueError("Core-issued execution and session IDs are required")
        return value


class ExecutionLifecycleRequest(BaseModel):
    coreExecutionId: str
    status: ExecutionStatus = "completed"
    visibility: Visibility = "internal"
    externalRunRef: str = ""
    commandOrEntrypoint: str = ""
    codeRef: str = ""
    sourceRevision: str = ""
    startedAt: str = ""
    finishedAt: str = ""
    changeSummary: str = "Recorded Workbench execution lifecycle update."
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    createdBy: str = "workbench"
    includeSnapshot: bool = True

    @field_validator("coreExecutionId")
    @classmethod
    def core_execution_required(cls, value: str) -> str:
        value = _bounded(value, 128)
        if not value:
            raise ValueError("coreExecutionId is required and must be returned by Platform Core")
        return value


class CoreLineageBundleConsumeRequest(BaseModel):
    bundle: Dict[str, Any]


def build_execution_create(request: ExecutionCreateRequest) -> Dict[str, Any]:
    workbench_ref = _bounded(request.workbenchExecutionRef, 1000) or f"sc://workbench/execution/{_bounded(request.executionKey, 180)}"
    metadata = dict(request.metadata)
    metadata.update({
        "workbenchVersion": VERSION,
        "workbenchExecutionRef": workbench_ref,
        "coreSessionId": _bounded(request.coreSessionId, 128) or None,
        "specialistComputationOwner": PRODUCT_REF,
    })
    provenance = {"sourceProductRef": PRODUCT_REF, "adapterRef": BRIDGE_REF, **dict(request.provenance)}
    data: Dict[str, Any] = {
        "execution_key": _bounded(request.executionKey, 180),
        "title": _bounded(request.title, 400),
        "execution_type": request.executionType,
        "runtime_kind": request.runtimeKind,
        "status": request.status,
        "visibility": request.visibility,
        "project_ref": _bounded(request.projectRef, 1000) or None,
        "protocol_id": _bounded(request.protocolId, 128) or None,
        "method_plan_ref": _bounded(request.methodPlanRef, 1000) or None,
        "external_run_ref": workbench_ref,
        "command_or_entrypoint": _bounded(request.commandOrEntrypoint, 1000) or None,
        "code_ref": _bounded(request.codeRef, 1000) or None,
        "source_revision": _bounded(request.sourceRevision, 256) or None,
        "started_at": _bounded(request.startedAt, 128) or None,
        "finished_at": _bounded(request.finishedAt, 128) or None,
        "provenance": provenance,
        "metadata": metadata,
        "created_by": _bounded(request.createdBy, 180) or "workbench",
    }
    execution_hash = content_hash(data)
    data["metadata"]["workbenchExecutionHash"] = execution_hash
    result = {
        "ok": True,
        "schema": PLAN_SCHEMA,
        "version": VERSION,
        "phase": "prepare-core-execution",
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "workbenchExecutionRef": workbench_ref,
        "executionHash": execution_hash,
        "executionDraft": data,
        "coreRequest": _request(CORE_PATHS["executions"], data, "execution-registration"),
        "coreExecutionIdMustComeFromCore": True,
        "automaticCorePersistenceAuthorized": False,
    }
    result["planHash"] = content_hash(result)
    return result


def _item_request(core_execution_id: str, family: str, data: Dict[str, Any], phase: str = "lineage-component") -> Dict[str, Any]:
    return _request(CORE_PATHS[family].format(execution_id=core_execution_id), data, phase)


def _input_data(x: InputItem) -> Dict[str, Any]:
    return {"input_key": _bounded(x.inputKey, 180), "input_type": x.inputType, "object_ref": _bounded(x.objectRef, 1000), "version_ref": _bounded(x.versionRef, 1000) or None, "content_hash": _bounded(x.contentHash, 256) or None, "role": _bounded(x.role, 180) or None, "selector": x.selector, "provenance": x.provenance, "created_by": _bounded(x.createdBy, 180) or "workbench"}


def _parameter_data(x: ParameterItem) -> Dict[str, Any]:
    return {"parameter_key": _bounded(x.parameterKey, 180), "value": x.value, "unit": _bounded(x.unit, 128) or None, "source_ref": _bounded(x.sourceRef, 1000) or None, "sensitivity_role": _bounded(x.sensitivityRole, 180) or None, "provenance": x.provenance, "created_by": _bounded(x.createdBy, 180) or "workbench"}


def _assumption_data(x: AssumptionItem) -> Dict[str, Any]:
    return {"assumption_key": _bounded(x.assumptionKey, 180), "statement_text": _bounded(x.statementText, 4000), "protocol_assumption_ref": _bounded(x.protocolAssumptionRef, 1000) or None, "evidence_refs": _refs(x.evidenceRefs), "provenance": x.provenance, "created_by": _bounded(x.createdBy, 180) or "workbench"}


def _environment_data(x: EnvironmentItem) -> Dict[str, Any]:
    return {"environment_key": _bounded(x.environmentKey, 180), "environment_type": _bounded(x.environmentType, 180), "runtime_name": _bounded(x.runtimeName, 400) or None, "runtime_version": _bounded(x.runtimeVersion, 180) or None, "os_arch": _bounded(x.osArch, 180) or None, "container_image": _bounded(x.containerImage, 1000) or None, "environment_hash": _bounded(x.environmentHash, 256) or None, "dependency_manifest_ref": _bounded(x.dependencyManifestRef, 1000) or None, "packages": _refs(x.packages), "hardware": x.hardware, "provenance": x.provenance, "created_by": _bounded(x.createdBy, 180) or "workbench"}


def _step_data(x: StepItem) -> Dict[str, Any]:
    return {"step_key": _bounded(x.stepKey, 180), "sequence": int(x.sequence), "step_type": _bounded(x.stepType, 180), "tool_ref": _bounded(x.toolRef, 1000) or None, "operation_text": _bounded(x.operationText, 4000) or None, "code_ref": _bounded(x.codeRef, 1000) or None, "input_refs": _refs(x.inputRefs), "output_refs": _refs(x.outputRefs), "parameters": x.parameters, "provenance": x.provenance, "created_by": _bounded(x.createdBy, 180) or "workbench"}


def _output_data(x: OutputItem) -> Dict[str, Any]:
    return {"output_key": _bounded(x.outputKey, 180), "output_type": x.outputType, "object_ref": _bounded(x.objectRef, 1000) or None, "version_ref": _bounded(x.versionRef, 1000) or None, "content_hash": _bounded(x.contentHash, 256) or None, "schema": x.schemaData, "metadata": x.metadata, "provenance": x.provenance, "created_by": _bounded(x.createdBy, 180) or "workbench"}


def _research_binding_data(x: ResearchBindingItem) -> Dict[str, Any]:
    return {"binding_key": _bounded(x.bindingKey, 180), "source_output_ref": _bounded(x.sourceOutputRef, 1000) or None, "target_type": x.targetType, "target_ref": _bounded(x.targetRef, 1000), "relation": _bounded(x.relation, 180), "binding_role": _bounded(x.bindingRole, 180) or None, "provenance": x.provenance, "created_by": _bounded(x.createdBy, 180) or "workbench"}


def _dependency_data(x: DependencyItem) -> Dict[str, Any]:
    return {"dependency_key": _bounded(x.dependencyKey, 180), "upstream_execution_ref": _bounded(x.upstreamExecutionRef, 1000), "upstream_output_ref": _bounded(x.upstreamOutputRef, 1000) or None, "relation": _bounded(x.relation, 180), "provenance": x.provenance, "created_by": _bounded(x.createdBy, 180) or "workbench"}


def _verification_data(x: VerificationItem) -> Dict[str, Any]:
    return {"verification_key": _bounded(x.verificationKey, 180), "verification_type": _bounded(x.verificationType, 180), "status": _bounded(x.status, 80) or "recorded", "evidence": x.evidence, "performed_by": _bounded(x.performedBy, 400) or None, "observed_at": _bounded(x.observedAt, 128) or None, "provenance": x.provenance, "created_by": _bounded(x.createdBy, 180) or "workbench"}


def build_components(request: ExecutionComponentsRequest) -> Dict[str, Any]:
    eid = _bounded(request.coreExecutionId, 128)
    requests: List[Dict[str, Any]] = []
    families = [
        ("inputs", request.inputs, _input_data),
        ("parameters", request.parameters, _parameter_data),
        ("assumptions", request.assumptions, _assumption_data),
        ("environments", request.environments, _environment_data),
        ("steps", sorted(request.steps, key=lambda x: (x.sequence, x.stepKey)), _step_data),
        ("outputs", request.outputs, _output_data),
        ("researchBindings", request.researchBindings, _research_binding_data),
        ("dependencies", request.dependencies, _dependency_data),
        ("verifications", request.verifications, _verification_data),
    ]
    counts: Dict[str, int] = {}
    for family, items, transform in families:
        counts[family] = len(items)
        for item in items:
            requests.append(_item_request(eid, family, transform(item)))

    input_refs = _refs([x.objectRef for x in request.inputs])
    output_refs = _refs([x.objectRef for x in request.outputs if x.objectRef])
    core_execution_ref = _core_execution_ref(eid)
    session_binding = None
    if _bounded(request.coreSessionId, 128):
        session_binding = build_execution_binding(ExecutionBindingRequest(
            coreSessionId=_bounded(request.coreSessionId, 128),
            executionRef=core_execution_ref,
            runtime=_bounded(request.runtime, 180) or "workbench",
            environmentRef=_bounded(request.environmentRef, 1000),
            methodRef=_bounded(request.methodRef, 1000),
            inputRefs=input_refs,
            outputRefs=output_refs,
            visibility=request.visibility,
            metadata={"workbenchVersion": VERSION, "workbenchExecutionRef": _bounded(request.workbenchExecutionRef, 1000) or None, "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT},
        ))

    result = {
        "ok": True,
        "schema": PLAN_SCHEMA,
        "version": VERSION,
        "phase": "prepare-lineage-components",
        "coreExecutionId": eid,
        "coreExecutionRef": core_execution_ref,
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "componentCounts": counts,
        "requestCount": len(requests),
        "coreRequests": requests,
        "inputRefs": input_refs,
        "outputRefs": output_refs,
        "unifiedSessionExecutionBinding": session_binding,
        "orderedStepsPreserved": True,
        "contentHashesPreserved": True,
        "verificationEvidencePreserved": True,
        "automaticCorePersistenceAuthorized": False,
    }
    result["planHash"] = content_hash(result)
    return result


def build_session_execution_binding(request: SessionExecutionBindingBuildRequest) -> Dict[str, Any]:
    return build_execution_binding(ExecutionBindingRequest(
        coreSessionId=_bounded(request.coreSessionId, 128),
        executionRef=_core_execution_ref(request.coreExecutionId),
        runtime=_bounded(request.runtime, 180) or "workbench",
        environmentRef=_bounded(request.environmentRef, 1000),
        methodRef=_bounded(request.methodRef, 1000),
        inputRefs=_refs(request.inputRefs),
        outputRefs=_refs(request.outputRefs),
        visibility=request.visibility,
        metadata={"workbenchVersion": VERSION, "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT, **request.metadata},
    ))


def build_lifecycle(request: ExecutionLifecycleRequest) -> Dict[str, Any]:
    eid = _bounded(request.coreExecutionId, 128)
    revision = {
        "status": request.status,
        "visibility": request.visibility,
        "external_run_ref": _bounded(request.externalRunRef, 1000) or None,
        "command_or_entrypoint": _bounded(request.commandOrEntrypoint, 1000) or None,
        "code_ref": _bounded(request.codeRef, 1000) or None,
        "source_revision": _bounded(request.sourceRevision, 256) or None,
        "started_at": _bounded(request.startedAt, 128) or None,
        "finished_at": _bounded(request.finishedAt, 128) or None,
        "metadata": request.metadata,
        "change_summary": _bounded(request.changeSummary, 1000) or None,
        "provenance": request.provenance,
        "created_by": _bounded(request.createdBy, 180) or "workbench",
    }
    core_requests = [_item_request(eid, "revisions", revision, "execution-revision")]
    if request.includeSnapshot:
        core_requests.append(_item_request(eid, "snapshots", {"provenance": request.provenance, "created_by": _bounded(request.createdBy, 180) or "workbench"}, "immutable-execution-snapshot"))
    result = {"ok": True, "schema": PLAN_SCHEMA, "version": VERSION, "phase": "prepare-execution-lifecycle", "coreExecutionId": eid, "coreRequests": core_requests, "snapshotRequested": bool(request.includeSnapshot), "automaticCorePersistenceAuthorized": False}
    result["planHash"] = content_hash(result)
    return result


def consume_core_lineage_bundle(request: CoreLineageBundleConsumeRequest) -> Dict[str, Any]:
    bundle = request.bundle or {}
    execution = bundle.get("execution") if isinstance(bundle.get("execution"), dict) else {}
    if not execution or not _bounded(execution.get("id"), 128):
        return {"ok": False, "schema": CONTEXT_SCHEMA, "version": VERSION, "error": "Core computation-lineage bundle must include execution.id", "readOnlyContext": True, "automaticWorkbenchMutationAuthorized": False}
    arrays = ("inputs", "parameters", "assumptions", "environments", "steps", "outputs", "research_bindings", "dependencies", "verifications", "revisions", "snapshots")
    counts = {name: len(bundle.get(name) or []) if isinstance(bundle.get(name), list) else 0 for name in arrays}
    outputs = bundle.get("outputs") if isinstance(bundle.get("outputs"), list) else []
    inputs = bundle.get("inputs") if isinstance(bundle.get("inputs"), list) else []
    context = {
        "coreExecutionId": _bounded(execution.get("id"), 128),
        "coreExecutionRef": _core_execution_ref(execution.get("id")),
        "executionKey": execution.get("execution_key"),
        "executionType": execution.get("execution_type"),
        "runtimeKind": execution.get("runtime_kind"),
        "status": execution.get("status"),
        "projectRef": execution.get("project_ref"),
        "workbenchExecutionRef": execution.get("external_run_ref"),
        "sourceRevision": execution.get("source_revision"),
        "inputRefs": _refs([x.get("object_ref", "") for x in inputs if isinstance(x, dict)]),
        "outputRefs": _refs([x.get("object_ref", "") for x in outputs if isinstance(x, dict)]),
        "componentCounts": counts,
        "lineageIsDeclaredNotInferred": True,
        "scientificValidityInferred": False,
        "reproducibilityInferred": False,
        "readOnlyContext": True,
        "automaticWorkbenchMutationAuthorized": False,
    }
    context["contextHash"] = content_hash(context)
    return {"ok": True, "schema": CONTEXT_SCHEMA, "version": VERSION, "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT, "context": context}


@router.get("/integration/core/computation-lineage/manifest")
def manifest(x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return lineage_manifest()


@router.post("/integration/core/computation-lineage/executions/build")
def execution_build(request: ExecutionCreateRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return build_execution_create(request)


@router.post("/integration/core/computation-lineage/executions/components/build")
def components_build(request: ExecutionComponentsRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return build_components(request)


@router.post("/integration/core/computation-lineage/executions/session-binding/build")
def session_binding_build(request: SessionExecutionBindingBuildRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return build_session_execution_binding(request)


@router.post("/integration/core/computation-lineage/executions/lifecycle/build")
def lifecycle_build(request: ExecutionLifecycleRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return build_lifecycle(request)


@router.post("/integration/core/computation-lineage/bundles/consume")
def bundle_consume(request: CoreLineageBundleConsumeRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return consume_core_lineage_bundle(request)


@router.get("/v670/status")
def v670_status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Computation, Analysis & Execution Lineage Bridge",
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "twoPhaseExecutionLineage": True,
        "coreExecutionIdMustComeFromCore": True,
        "unifiedSessionExecutionBinding": True,
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
    }

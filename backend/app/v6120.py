"""Workbench v6.12.0 — Research State, Reproduction & Snapshot Integration.

Bridges deterministic Workbench research/computation state into Platform Core's
project-state, reproducible-research, and cross-product context/handoff
contracts. The adapter is reference-first and plan-only: Workbench can capture
its own declared state and prepare exact Core write requests, but Core owns its
registries and immutable snapshots.

No endpoint in this module dispatches network requests to Core, restores
historical state automatically, replays executions automatically, infers
missing state, certifies reproducibility, validates scientific results, or
determines truth.
"""
from __future__ import annotations

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
SCHEMA = "sc-workbench-research-state-reproduction-snapshot-integration/1.0"
SNAPSHOT_SCHEMA = "sc-workbench-research-state-snapshot/1.0"
RESUME_SCHEMA = "sc-workbench-research-state-resume-plan/1.0"
CORE_REQUEST_SCHEMA = "sc-workbench-core-research-state-request/1.0"
CORE_PROJECT_STATE_CONTRACT = "sc.research.project-state-versioning-reproducibility.v1"
CORE_REPRODUCIBLE_RESEARCH_CONTRACT = "sc.research.reproducible-package.v1"
CORE_CONTEXT_HANDOFF_CONTRACT = "sc.research.cross-product-context-handoff.v1"
BRIDGE_REF = "workbench:/integration/core/research-state"

CORE_PATHS = {
    "projectStateReadiness": "/v1/research/project-state/readiness",
    "projectStates": "/v1/research/project-state/states",
    "projectStateVersions": "/v1/research/project-state/states/{state_id}/versions",
    "projectStateBindings": "/v1/research/project-state/states/{state_id}/versions/{version}/bindings",
    "projectStateDependencies": "/v1/research/project-state/states/{state_id}/versions/{version}/dependencies",
    "projectStateEnvironments": "/v1/research/project-state/states/{state_id}/versions/{version}/environments",
    "projectStateFreeze": "/v1/research/project-state/states/{state_id}/versions/{version}/freeze",
    "projectStateManifest": "/v1/research/project-state/states/{state_id}/versions/{version}/manifest",
    "projectStateCheckpoints": "/v1/research/project-state/states/{state_id}/checkpoints",
    "projectStateReconstructionPlans": "/v1/research/project-state/states/{state_id}/reconstruction-plans",
    "projectStateVerifications": "/v1/research/project-state/states/{state_id}/reconstruction-plans/{plan_key}/verifications",
    "projectStateSnapshots": "/v1/research/project-state/states/{state_id}/snapshots",
    "reproducibleReadiness": "/v1/research/reproducible/readiness",
    "reproduciblePackages": "/v1/research/reproducible/projects/{project_id}/packages",
    "reproducibleComponents": "/v1/research/reproducible/packages/{package_id}/components",
    "reproducibleArtifacts": "/v1/research/reproducible/packages/{package_id}/artifacts",
    "reproducibleEnvironments": "/v1/research/reproducible/packages/{package_id}/environments",
    "reproducibleReplayPlans": "/v1/research/reproducible/packages/{package_id}/replay-plans",
    "reproducibleVerifications": "/v1/research/reproducible/packages/{package_id}/verifications",
    "reproducibleSnapshots": "/v1/research/reproducible/packages/{package_id}/snapshots",
    "contextReadiness": "/v1/research/context-handoffs/readiness",
    "contexts": "/v1/research/context-handoffs/contexts",
    "contextObjectBindings": "/v1/research/context-handoffs/contexts/{context_id}/object-bindings",
    "contextStateMarkers": "/v1/research/context-handoffs/contexts/{context_id}/state-markers",
    "contextProtocols": "/v1/research/context-handoffs/contexts/{context_id}/protocols",
    "contextPackages": "/v1/research/context-handoffs/contexts/{context_id}/packages",
    "contextSnapshots": "/v1/research/context-handoffs/contexts/{context_id}/snapshots",
}

CORE_PROJECT_OBJECT_TYPES = {
    "project", "question", "source", "evidence", "protocol", "dataset", "method",
    "execution", "parameter", "assumption", "output", "finding", "claim", "inference",
    "hypothesis", "argument", "conclusion", "audit", "review", "replication",
    "publication", "synthesis", "notebook", "visualization", "workflow", "handoff",
    "forensic_object", "predictive_object", "other",
}
CORE_ENVIRONMENT_TYPES = {
    "software", "python", "r", "julia", "ml", "container", "notebook", "workbench",
    "database", "operating_system", "external_service", "other",
}
CONTEXT_PRODUCTS = {
    "core", "library", "research_librarian", "workspace", "research_lab", "workbench",
    "site_intelligence", "decision_studio", "catalyst_data", "external",
}
REPRO_PRODUCTS = {
    "library", "lab", "workbench", "decision-studio", "site-intelligence", "workspace",
    "research-librarian", "platform-core", "external",
}

router = APIRouter(tags=["workbench-v6120-research-state-reproduction-snapshot"])


def _bounded(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _required(value: str, label: str, limit: int = 1000) -> str:
    out = _bounded(value, limit)
    if not out:
        raise ValueError(f"{label} is required")
    return out


def _refs(items: List[str]) -> List[str]:
    return sorted({_bounded(x) for x in items if _bounded(x)})


def _core_request(path: str, data: Dict[str, Any], phase: str, method: str = "POST", contract: str = CORE_PROJECT_STATE_CONTRACT) -> Dict[str, Any]:
    record = {
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "contract": contract,
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


def integration_manifest() -> Dict[str, Any]:
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
        "coreProjectStateContract": CORE_PROJECT_STATE_CONTRACT,
        "coreReproducibleResearchContract": CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        "coreContextHandoffContract": CORE_CONTEXT_HANDOFF_CONTRACT,
        "corePaths": dict(CORE_PATHS),
        "lifecycle": [
            "capture-deterministic-workbench-state",
            "prepare-core-project-state",
            "receive-core-state-id",
            "prepare-version-bindings-dependencies-environments",
            "freeze-version-in-core",
            "prepare-checkpoint-and-reconstruction-plan",
            "prepare-reproducible-package",
            "receive-core-package-id",
            "prepare-components-environments-replay-plan-and-snapshot",
            "prepare-cross-product-context-and-snapshot",
            "consume-core-state-for-explicit-resume-plan",
        ],
        "boundaries": {
            "workbenchCapturesDeclaredLocalState": True,
            "coreOwnsHistoricalStateRegistry": True,
            "coreStateIdMustComeFromCore": True,
            "corePackageIdMustComeFromCore": True,
            "coreContextIdMustComeFromCore": True,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "automaticStateRestoreAuthorized": False,
            "automaticExecutionReplayAuthorized": False,
            "coreRestoresWorkbenchState": False,
            "coreReplaysWorkbenchExecutions": False,
            "coreInfersMissingVersions": False,
            "coreInfersReproducibility": False,
            "workbenchCertifiesReproducibility": False,
            "coreCertifiesReproducibility": False,
            "scientificResultValidationByThisBridge": False,
            "truthDeterminationAuthorized": False,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


Visibility = Literal["private", "internal", "public"]
CheckpointType = Literal["milestone", "analysis", "review", "replication", "publication", "handoff", "archive", "other"]


class StateBinding(BaseModel):
    bindingKey: str
    objectType: str
    objectRef: str
    versionRef: str = ""
    contentHash: str = ""
    role: str = "project_state"
    visibility: Visibility = "internal"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("bindingKey", "objectRef")
    @classmethod
    def required_text(cls, value: str) -> str:
        return _required(value, "binding field")

    @field_validator("objectType")
    @classmethod
    def object_type_supported(cls, value: str) -> str:
        value = _required(value, "objectType", 80)
        if value not in CORE_PROJECT_OBJECT_TYPES:
            raise ValueError("objectType is not supported by Platform Core project-state")
        return value


class StateEnvironment(BaseModel):
    environmentKey: str
    environmentType: str = "workbench"
    environmentRef: str
    versionRef: str = ""
    contentHash: str = ""
    visibility: Visibility = "internal"
    details: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("environmentKey", "environmentRef")
    @classmethod
    def required_env_text(cls, value: str) -> str:
        return _required(value, "environment field")

    @field_validator("environmentType")
    @classmethod
    def environment_supported(cls, value: str) -> str:
        value = _required(value, "environmentType", 80)
        if value not in CORE_ENVIRONMENT_TYPES:
            raise ValueError("environmentType is not supported by Platform Core project-state")
        return value


class StateDependency(BaseModel):
    dependencyKey: str
    fromBindingKey: str
    toBindingKey: str
    relation: str
    details: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class SnapshotArtifact(BaseModel):
    artifactKey: str
    artifactType: str
    artifactRef: str
    mediaType: str = ""
    contentHash: str = ""
    sizeBytes: int | None = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ResearchStateSnapshotRequest(BaseModel):
    snapshotKey: str
    projectRef: str
    title: str
    projectHash: str = ""
    workbenchProjectVersion: str = ""
    coreSessionId: str = ""
    bindings: List[StateBinding] = Field(default_factory=list)
    environments: List[StateEnvironment] = Field(default_factory=list)
    dependencies: List[StateDependency] = Field(default_factory=list)
    artifacts: List[SnapshotArtifact] = Field(default_factory=list)
    researchState: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("snapshotKey", "projectRef", "title")
    @classmethod
    def snapshot_required(cls, value: str) -> str:
        return _required(value, "snapshot field")


class ProjectStatePrepareRequest(BaseModel):
    snapshot: Dict[str, Any]
    stateKey: str = ""
    visibility: Visibility = "internal"
    createdBy: str = "workbench"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ProjectStateVersionPlanRequest(BaseModel):
    coreStateId: str
    snapshot: Dict[str, Any]
    version: int = 1
    label: str = "Workbench captured state"
    checkpointType: CheckpointType = "analysis"
    checkpointKey: str = ""
    reconstructionPlanKey: str = ""
    createdBy: str = "workbench"

    @field_validator("coreStateId")
    @classmethod
    def core_state_required(cls, value: str) -> str:
        return _required(value, "coreStateId", 128)


class ReproductionPrepareRequest(BaseModel):
    coreProjectEntityId: str
    snapshot: Dict[str, Any]
    packageKey: str = ""
    purpose: str = "Reproduce declared Workbench research state"
    createdBy: str = "workbench"

    @field_validator("coreProjectEntityId")
    @classmethod
    def project_entity_required(cls, value: str) -> str:
        return _required(value, "coreProjectEntityId", 128)


class ReproductionPackagePlanRequest(BaseModel):
    corePackageId: str
    snapshot: Dict[str, Any]
    targetProduct: str = "workbench"
    planKey: str = ""
    createdBy: str = "workbench"

    @field_validator("corePackageId")
    @classmethod
    def package_required(cls, value: str) -> str:
        return _required(value, "corePackageId", 128)

    @field_validator("targetProduct")
    @classmethod
    def product_supported(cls, value: str) -> str:
        value = _required(value, "targetProduct", 80)
        if value not in REPRO_PRODUCTS:
            raise ValueError("targetProduct is not supported by Platform Core reproducible research")
        return value


class ContextPrepareRequest(BaseModel):
    snapshot: Dict[str, Any]
    contextKey: str = ""
    visibility: Visibility = "internal"
    workflowRef: str = ""
    workflowStageRef: str = ""
    protocolRef: str = ""
    createdBy: str = "workbench"


class ContextPlanRequest(BaseModel):
    coreContextId: str
    snapshot: Dict[str, Any]
    toProduct: str = "core"
    handoffKey: str = ""
    packageKey: str = ""
    createdBy: str = "workbench"

    @field_validator("coreContextId")
    @classmethod
    def context_required(cls, value: str) -> str:
        return _required(value, "coreContextId", 128)

    @field_validator("toProduct")
    @classmethod
    def context_product_supported(cls, value: str) -> str:
        value = _required(value, "toProduct", 80)
        if value not in CONTEXT_PRODUCTS:
            raise ValueError("toProduct is not supported by Platform Core context handoffs")
        return value


class ResumeConsumeRequest(BaseModel):
    bundle: Dict[str, Any]


class StateVerificationCompareRequest(BaseModel):
    snapshot: Dict[str, Any]
    coreManifest: Dict[str, Any]


def _validate_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError(f"snapshot.schema must be {SNAPSHOT_SCHEMA}")
    if not snapshot.get("snapshotHash"):
        raise ValueError("snapshotHash is required")
    return snapshot


def build_snapshot(request: ResearchStateSnapshotRequest) -> Dict[str, Any]:
    bindings = [x.model_dump() for x in request.bindings]
    project_binding_key = "workbench-project"
    if not any(x["bindingKey"] == project_binding_key for x in bindings):
        bindings.append({
            "bindingKey": project_binding_key,
            "objectType": "project",
            "objectRef": request.projectRef,
            "versionRef": request.workbenchProjectVersion,
            "contentHash": request.projectHash,
            "role": "project_state",
            "visibility": "internal",
            "metadata": {"autoAddedByV6120": True},
            "provenance": {},
        })
    bindings = sorted(bindings, key=lambda x: x["bindingKey"])
    keys = {x["bindingKey"] for x in bindings}
    deps = [x.model_dump() for x in request.dependencies]
    bad = [x["dependencyKey"] for x in deps if x["fromBindingKey"] not in keys or x["toBindingKey"] not in keys]
    if bad:
        raise ValueError("dependency endpoints must reference bindings in the snapshot: " + ", ".join(sorted(bad)))
    environments = sorted([x.model_dump() for x in request.environments], key=lambda x: x["environmentKey"])
    artifacts = sorted([x.model_dump() for x in request.artifacts], key=lambda x: x["artifactKey"])
    record = {
        "ok": True,
        "schema": SNAPSHOT_SCHEMA,
        "version": VERSION,
        "snapshotKey": request.snapshotKey,
        "projectRef": request.projectRef,
        "title": request.title,
        "projectHash": request.projectHash,
        "workbenchProjectVersion": request.workbenchProjectVersion or VERSION,
        "coreSessionId": request.coreSessionId,
        "bindings": bindings,
        "dependencies": sorted(deps, key=lambda x: x["dependencyKey"]),
        "environments": environments,
        "artifacts": artifacts,
        "researchState": request.researchState,
        "metadata": {**request.metadata, "workbenchVersion": VERSION},
        "provenance": request.provenance,
        "captureSemantics": {
            "declaredStateOnly": True,
            "historicalExecutionEmbedded": False,
            "automaticRestoreAuthorized": False,
            "automaticReplayAuthorized": False,
        },
    }
    record["snapshotHash"] = content_hash(record)
    return record


def prepare_project_state(request: ProjectStatePrepareRequest) -> Dict[str, Any]:
    snapshot = _validate_snapshot(request.snapshot)
    state_key = _bounded(request.stateKey, 240) or f"workbench-{snapshot['snapshotKey']}"
    data = {
        "state_key": state_key,
        "project_ref": snapshot["projectRef"],
        "title": snapshot["title"],
        "status": "active",
        "visibility": request.visibility,
        "metadata": {**request.metadata, "workbench_snapshot_hash": snapshot["snapshotHash"], "workbench_version": VERSION},
        "provenance": {**request.provenance, "source_product": "workbench"},
        "created_by": request.createdBy,
    }
    return {
        "ok": True,
        "schema": SCHEMA,
        "phase": "prepare-core-project-state",
        "snapshotHash": snapshot["snapshotHash"],
        "coreStateIdMustComeFromCore": True,
        "coreRequest": _core_request(CORE_PATHS["projectStates"], data, "create-project-state"),
        "automaticCoreDispatchAuthorized": False,
    }


def build_project_state_version_plan(request: ProjectStateVersionPlanRequest) -> Dict[str, Any]:
    snapshot = _validate_snapshot(request.snapshot)
    sid = request.coreStateId
    version = int(request.version)
    if version < 1:
        raise ValueError("version must be >= 1")
    base = f"/v1/research/project-state/states/{sid}/versions/{version}"
    create_version = _core_request(
        f"/v1/research/project-state/states/{sid}/versions",
        {"version": version, "label": request.label, "status": "draft", "summary": f"Workbench snapshot {snapshot['snapshotKey']}", "metadata": {"workbench_snapshot_hash": snapshot["snapshotHash"]}, "provenance": snapshot.get("provenance", {}), "created_by": request.createdBy},
        "create-draft-state-version",
    )
    binding_requests = []
    for item in snapshot.get("bindings", []):
        binding_requests.append(_core_request(
            base + "/bindings",
            {"binding_key": item["bindingKey"], "product_key": "workbench", "object_type": item["objectType"], "object_ref": item["objectRef"], "object_version_ref": item.get("versionRef") or None, "content_hash": item.get("contentHash") or None, "role": item.get("role") or "project_state", "visibility": item.get("visibility") or "internal", "metadata": item.get("metadata", {}), "provenance": item.get("provenance", {}), "created_by": request.createdBy},
            "bind-version-object",
        ))
    dependency_requests = []
    for item in snapshot.get("dependencies", []):
        dependency_requests.append(_core_request(
            base + "/dependencies",
            {"dependency_key": item["dependencyKey"], "from_binding_key": item["fromBindingKey"], "to_binding_key": item["toBindingKey"], "relation": item["relation"], "details": item.get("details", {}), "provenance": item.get("provenance", {}), "created_by": request.createdBy},
            "bind-version-dependency",
        ))
    environment_requests = []
    for item in snapshot.get("environments", []):
        environment_requests.append(_core_request(
            base + "/environments",
            {"environment_key": item["environmentKey"], "environment_type": item["environmentType"], "environment_ref": item["environmentRef"], "version_ref": item.get("versionRef") or None, "content_hash": item.get("contentHash") or None, "visibility": item.get("visibility") or "internal", "details": item.get("details", {}), "provenance": item.get("provenance", {}), "created_by": request.createdBy},
            "bind-version-environment",
        ))
    freeze = _core_request(base + "/freeze", {"provenance": snapshot.get("provenance", {}), "created_by": request.createdBy}, "freeze-state-version")
    checkpoint_key = _bounded(request.checkpointKey, 240) or f"{snapshot['snapshotKey']}-v{version}"
    checkpoint = _core_request(
        f"/v1/research/project-state/states/{sid}/checkpoints",
        {"version": version, "checkpoint_key": checkpoint_key, "checkpoint_type": request.checkpointType, "title": f"Workbench state {snapshot['title']}", "status": "declared", "notes": "Declared Workbench research-state checkpoint; no restore or replay is performed by Core.", "provenance": snapshot.get("provenance", {}), "created_by": request.createdBy},
        "create-state-checkpoint",
    )
    plan_key = _bounded(request.reconstructionPlanKey, 240) or f"{snapshot['snapshotKey']}-reconstruct-v{version}"
    reconstruction = _core_request(
        f"/v1/research/project-state/states/{sid}/reconstruction-plans",
        {"version": version, "plan_key": plan_key, "status": "declared", "required_binding_keys": [x["bindingKey"] for x in snapshot.get("bindings", [])], "required_environment_keys": [x["environmentKey"] for x in snapshot.get("environments", [])], "steps": [
            {"step": 1, "action": "resolve-declared-object-references", "executor": "caller"},
            {"step": 2, "action": "materialize-compatible-workbench-environment", "executor": "workbench-or-operator"},
            {"step": 3, "action": "request-explicit-replay-if-desired", "executor": "operator", "automatic": False},
            {"step": 4, "action": "record-observed-verification-evidence", "executor": "caller"},
        ], "notes": "Reference-first reconstruction plan. Core does not restore Workbench state or replay executions.", "provenance": snapshot.get("provenance", {}), "created_by": request.createdBy},
        "create-reconstruction-plan",
    )
    requests = [create_version, *binding_requests, *dependency_requests, *environment_requests, freeze, checkpoint, reconstruction]
    return {
        "ok": True,
        "schema": SCHEMA,
        "phase": "prepare-version-freeze-checkpoint-reconstruction",
        "coreStateId": sid,
        "version": version,
        "snapshotHash": snapshot["snapshotHash"],
        "coreRequests": requests,
        "requestCount": len(requests),
        "orderingRequired": True,
        "freezeMustFollowBindings": True,
        "checkpointAndReconstructionRequireFrozenVersion": True,
        "automaticStateRestoreAuthorized": False,
        "automaticExecutionReplayAuthorized": False,
    }


def prepare_reproducible_package(request: ReproductionPrepareRequest) -> Dict[str, Any]:
    snapshot = _validate_snapshot(request.snapshot)
    package_key = _bounded(request.packageKey, 240) or f"workbench-{snapshot['snapshotKey']}"
    data = {
        "package_key": package_key,
        "title": f"Workbench reproduction package — {snapshot['title']}",
        "purpose": request.purpose,
        "status": "draft",
        "manifest_version": "1.0",
        "provenance": snapshot.get("provenance", {}),
        "metadata": {"workbench_snapshot_hash": snapshot["snapshotHash"], "workbench_version": VERSION, "created_by": request.createdBy},
    }
    path = f"/v1/research/reproducible/projects/{request.coreProjectEntityId}/packages"
    return {
        "ok": True,
        "schema": SCHEMA,
        "phase": "prepare-reproducible-package",
        "corePackageIdMustComeFromCore": True,
        "coreRequest": _core_request(path, data, "create-reproducible-package", contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT),
        "automaticCoreDispatchAuthorized": False,
    }


def _component_type(object_type: str) -> str:
    mapping = {
        "project": "project", "question": "question", "source": "literature", "evidence": "evidence",
        "dataset": "dataset", "method": "methodology", "execution": "analysis_run", "output": "analysis_output",
        "finding": "finding", "visualization": "visualization", "forensic_object": "investigation",
    }
    return mapping.get(object_type, "other")


def build_reproducible_package_plan(request: ReproductionPackagePlanRequest) -> Dict[str, Any]:
    snapshot = _validate_snapshot(request.snapshot)
    pid = request.corePackageId
    base = f"/v1/research/reproducible/packages/{pid}"
    components = []
    for item in snapshot.get("bindings", []):
        components.append(_core_request(
            base + "/components",
            {"component_key": item["bindingKey"], "component_type": _component_type(item["objectType"]), "component_ref": item["objectRef"], "version_ref": item.get("versionRef") or None, "content_hash": item.get("contentHash") or None, "required": True, "metadata": {"workbench_object_type": item["objectType"], **item.get("metadata", {})}},
            "add-reproducible-component",
            contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        ))
    artifacts = []
    for item in snapshot.get("artifacts", []):
        artifacts.append(_core_request(
            base + "/artifacts",
            {"artifact_key": item["artifactKey"], "artifact_type": item["artifactType"], "artifact_ref": item["artifactRef"], "media_type": item.get("mediaType") or None, "content_hash": item.get("contentHash") or None, "size_bytes": item.get("sizeBytes"), "provenance": item.get("provenance", {})},
            "add-reproducible-artifact",
            contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        ))
    environments = []
    for item in snapshot.get("environments", []):
        environments.append(_core_request(
            base + "/environments",
            {"environment_key": item["environmentKey"], "environment_ref": item["environmentRef"], "runtime_manifest": {"environment_type": item["environmentType"], "version_ref": item.get("versionRef"), "workbench_version": VERSION}, "dependency_manifest": item.get("details", {}), "container_ref": item["environmentRef"] if item["environmentType"] == "container" else None, "hardware": {}},
            "add-reproducible-environment",
            contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        ))
    plan_key = _bounded(request.planKey, 240) or f"{snapshot['snapshotKey']}-workbench-replay"
    replay = _core_request(
        base + "/replay-plans",
        {"plan_key": plan_key, "target_product": request.targetProduct, "instructions": {"mode": "explicit-workbench-resume", "snapshot_schema": SNAPSHOT_SCHEMA, "snapshot_hash": snapshot["snapshotHash"], "automatic_replay": False, "steps": ["resolve references", "verify environment compatibility", "request explicit execution", "compare observed outputs"]}, "entrypoint_ref": "workbench:/integration/core/research-state/resume/consume", "expected_outputs": [x["objectRef"] for x in snapshot.get("bindings", []) if x["objectType"] in {"output", "visualization", "predictive_object", "forensic_object"}], "provenance": snapshot.get("provenance", {})},
        "add-declarative-replay-plan",
        contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
    )
    snap = _core_request(base + "/snapshots", {"provenance": snapshot.get("provenance", {}), "created_by": request.createdBy}, "snapshot-reproducible-package", contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT)
    requests = [*components, *artifacts, *environments, replay, snap]
    return {
        "ok": True,
        "schema": SCHEMA,
        "phase": "prepare-reproducible-package-components-and-snapshot",
        "corePackageId": pid,
        "snapshotHash": snapshot["snapshotHash"],
        "coreRequests": requests,
        "requestCount": len(requests),
        "automaticReplayAuthorized": False,
        "reproducibilityCertified": False,
        "truthDeterminationAuthorized": False,
    }


def prepare_context(request: ContextPrepareRequest) -> Dict[str, Any]:
    snapshot = _validate_snapshot(request.snapshot)
    context_key = _bounded(request.contextKey, 240) or f"workbench-{snapshot['snapshotKey']}"
    data = {
        "context_key": context_key,
        "title": f"Workbench research context — {snapshot['title']}",
        "status": "active",
        "visibility": request.visibility,
        "schema_version": "1.0",
        "source_product": "workbench",
        "project_ref": snapshot["projectRef"],
        "workflow_ref": request.workflowRef or None,
        "workflow_stage_ref": request.workflowStageRef or None,
        "protocol_ref": request.protocolRef or None,
        "research_state": {"snapshot_schema": SNAPSHOT_SCHEMA, "snapshot_key": snapshot["snapshotKey"], "snapshot_hash": snapshot["snapshotHash"], "workbench_version": VERSION},
        "metadata": {"workbench_state_capture": True},
        "provenance": snapshot.get("provenance", {}),
        "created_by": request.createdBy,
    }
    return {
        "ok": True,
        "schema": SCHEMA,
        "phase": "prepare-cross-product-context",
        "coreContextIdMustComeFromCore": True,
        "coreRequest": _core_request(CORE_PATHS["contexts"], data, "create-research-context", contract=CORE_CONTEXT_HANDOFF_CONTRACT),
        "automaticCoreDispatchAuthorized": False,
    }


def build_context_plan(request: ContextPlanRequest) -> Dict[str, Any]:
    snapshot = _validate_snapshot(request.snapshot)
    cid = request.coreContextId
    base = f"/v1/research/context-handoffs/contexts/{cid}"
    binding_requests = []
    for item in snapshot.get("bindings", []):
        object_type = item["objectType"] if item["objectType"] in CORE_PROJECT_OBJECT_TYPES else "other"
        binding_requests.append(_core_request(
            base + "/object-bindings",
            {"binding_key": item["bindingKey"], "product_key": "workbench", "object_type": object_type, "object_ref": item["objectRef"], "role": item.get("role") or "context", "version_ref": item.get("versionRef") or None, "visibility": item.get("visibility") or "internal", "metadata": item.get("metadata", {}), "provenance": item.get("provenance", {}), "created_by": request.createdBy},
            "bind-context-object",
            contract=CORE_CONTEXT_HANDOFF_CONTRACT,
        ))
    state_key = f"workbench-state-{snapshot['snapshotKey']}"
    state_marker = _core_request(
        base + "/state-markers",
        {"state_key": state_key, "namespace": "workbench.research-state", "product_key": "workbench", "visibility": "internal", "value": {"snapshot_schema": SNAPSHOT_SCHEMA, "snapshot_hash": snapshot["snapshotHash"], "workbench_version": VERSION}, "provenance": snapshot.get("provenance", {}), "created_by": request.createdBy},
        "bind-context-state-marker",
        contract=CORE_CONTEXT_HANDOFF_CONTRACT,
    )
    handoff_key = _bounded(request.handoffKey, 240) or f"workbench-{snapshot['snapshotKey']}-handoff"
    protocol = _core_request(
        base + "/protocols",
        {"handoff_key": handoff_key, "from_product": "workbench", "to_product": request.toProduct, "status": "prepared", "transfer_mode": "snapshot", "required_bindings": [x["bindingKey"] for x in snapshot.get("bindings", [])], "required_state_keys": [state_key], "requested_capabilities": ["resume", "reconstruct", "verify"], "redaction_policy": {}, "integrity_policy": {"require_content_hashes": True, "snapshot_hash": snapshot["snapshotHash"]}, "provenance": snapshot.get("provenance", {}), "created_by": request.createdBy},
        "declare-context-handoff-protocol",
        contract=CORE_CONTEXT_HANDOFF_CONTRACT,
    )
    package_key = _bounded(request.packageKey, 240) or f"workbench-{snapshot['snapshotKey']}-package"
    package = _core_request(
        base + "/packages",
        {"handoff_key": handoff_key, "package_key": package_key, "status": "prepared", "require_complete": True, "supplement": {"workbench_snapshot_schema": SNAPSHOT_SCHEMA, "workbench_snapshot_hash": snapshot["snapshotHash"], "automatic_restore": False}, "provenance": snapshot.get("provenance", {}), "created_by": request.createdBy},
        "create-context-handoff-package",
        contract=CORE_CONTEXT_HANDOFF_CONTRACT,
    )
    snap = _core_request(base + "/snapshots", {"provenance": snapshot.get("provenance", {}), "created_by": request.createdBy}, "snapshot-research-context", contract=CORE_CONTEXT_HANDOFF_CONTRACT)
    requests = [*binding_requests, state_marker, protocol, package, snap]
    return {
        "ok": True,
        "schema": SCHEMA,
        "phase": "prepare-context-bindings-protocol-package-snapshot",
        "coreContextId": cid,
        "coreRequests": requests,
        "requestCount": len(requests),
        "orderingRequired": True,
        "packageRequiresProtocolAndDeclaredBindings": True,
        "automaticHandoffExecutionAuthorized": False,
        "automaticStateRestoreAuthorized": False,
    }


def consume_resume_bundle(request: ResumeConsumeRequest) -> Dict[str, Any]:
    bundle = request.bundle
    source_kind = "unknown"
    project_ref = ""
    refs: List[str] = []
    env_refs: List[str] = []
    instructions: List[Any] = []
    source_hash = content_hash(bundle)
    if bundle.get("state") and bundle.get("version") and "bindings" in bundle:
        source_kind = "core-project-state-historical-manifest"
        project_ref = _bounded(bundle.get("state", {}).get("project_ref"))
        refs = _refs([x.get("object_ref", "") for x in bundle.get("bindings", [])])
        env_refs = _refs([x.get("environment_ref", "") for x in bundle.get("environments", [])])
        instructions = ["resolve frozen manifest references", "materialize compatible environment", "request explicit Workbench execution if reproduction is desired"]
    elif bundle.get("contract") == CORE_REPRODUCIBLE_RESEARCH_CONTRACT and bundle.get("package"):
        source_kind = "core-reproducible-research-package"
        refs = _refs([x.get("component_ref", "") for x in bundle.get("components", [])] + [x.get("artifact_ref", "") for x in bundle.get("artifacts", [])])
        env_refs = _refs([x.get("environment_ref", "") for x in bundle.get("environments", [])])
        instructions = [x.get("instructions", {}) for x in bundle.get("replay_plans", [])]
    elif bundle.get("context") and "object_bindings" in bundle:
        source_kind = "core-cross-product-research-context"
        project_ref = _bounded(bundle.get("context", {}).get("project_ref"))
        refs = _refs([x.get("object_ref", "") for x in bundle.get("object_bindings", [])])
        instructions = ["resolve declared context object bindings", "inspect state markers", "request explicit Workbench resume"]
    else:
        raise ValueError("unsupported Core research-state/reproduction/context bundle")
    plan = {
        "ok": True,
        "schema": RESUME_SCHEMA,
        "version": VERSION,
        "sourceKind": source_kind,
        "sourceHash": source_hash,
        "projectRef": project_ref,
        "requiredObjectRefs": refs,
        "environmentRefs": env_refs,
        "declaredInstructions": instructions,
        "callerMustResolveReferences": True,
        "environmentCompatibilityMustBeChecked": True,
        "automaticRestoreAuthorized": False,
        "automaticExecutionReplayAuthorized": False,
        "automaticCoreMutationAuthorized": False,
        "reproducibilityCertified": False,
        "scientificResultsValidated": False,
        "truthDeterminationAuthorized": False,
    }
    plan["resumePlanHash"] = content_hash(plan)
    return plan


def compare_state(request: StateVerificationCompareRequest) -> Dict[str, Any]:
    snapshot = _validate_snapshot(request.snapshot)
    manifest = request.coreManifest
    core_bindings = {x.get("object_ref"): x for x in manifest.get("bindings", []) if x.get("object_ref")}
    results = []
    for item in snapshot.get("bindings", []):
        core = core_bindings.get(item["objectRef"])
        local_hash = item.get("contentHash") or ""
        core_hash = (core or {}).get("content_hash") or ""
        if core is None:
            status = "missing-in-core-manifest"
        elif local_hash and core_hash and local_hash != core_hash:
            status = "hash-mismatch"
        elif local_hash and core_hash and local_hash == core_hash:
            status = "hash-match"
        else:
            status = "reference-match-hash-unavailable"
        results.append({"objectRef": item["objectRef"], "status": status, "localHash": local_hash, "coreHash": core_hash})
    counts: Dict[str, int] = {}
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    out = {
        "ok": True,
        "schema": "sc-workbench-research-state-verification-evidence/1.0",
        "version": VERSION,
        "snapshotHash": snapshot["snapshotHash"],
        "coreManifestHash": content_hash(manifest),
        "results": results,
        "statusCounts": counts,
        "evidenceOnly": True,
        "reproducibilityCertified": False,
        "scientificResultsValidated": False,
        "truthDeterminationAuthorized": False,
    }
    out["verificationHash"] = content_hash(out)
    return out


@router.get("/integration/core/research-state/manifest")
def manifest(x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return integration_manifest()


@router.post("/research-state/snapshot/build")
def snapshot_build(request: ResearchStateSnapshotRequest) -> Dict[str, Any]:
    try:
        return build_snapshot(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/research-state/project-state/prepare")
def project_state_prepare(request: ProjectStatePrepareRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return prepare_project_state(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/research-state/project-state/version/plan")
def project_state_version_plan(request: ProjectStateVersionPlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return build_project_state_version_plan(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/research-state/reproduction/prepare")
def reproduction_prepare(request: ReproductionPrepareRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return prepare_reproducible_package(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/research-state/reproduction/package/plan")
def reproduction_package_plan(request: ReproductionPackagePlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return build_reproducible_package_plan(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/research-state/context/prepare")
def context_prepare(request: ContextPrepareRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return prepare_context(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/research-state/context/plan")
def context_plan(request: ContextPlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return build_context_plan(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/integration/core/research-state/resume/consume")
def resume_consume(request: ResumeConsumeRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return consume_resume_bundle(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/research-state/verification/compare")
def verification_compare(request: StateVerificationCompareRequest) -> Dict[str, Any]:
    try:
        return compare_state(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/v6120/status")
def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Research State, Reproduction & Snapshot Integration",
        "deterministicWorkbenchStateCapture": True,
        "coreProjectStateVersioning": True,
        "coreReproduciblePackages": True,
        "crossProductContextSnapshots": True,
        "explicitResumePlanning": True,
        "stateVerificationEvidence": True,
        "automaticStateRestore": False,
        "automaticExecutionReplay": False,
        "reproducibilityCertification": False,
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
        "truthDetermination": False,
    }

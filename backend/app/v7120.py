"""Workbench v7.12.0 — Reproducible Experiment & Engineering Package.

Closing v7 packaging layer. Builds content-addressed, reference-preserving packages
for experiments and engineering studies from declared Workbench state. Packages can
contain datasets/workspaces, parameters, assumptions, notebooks, workflow graphs,
execution objects, solver/simulation/engineering/design-space results, validation
reports, visual workspaces, environments, artifacts and lineage references.

The runtime never automatically replays computation, restores hidden state, writes
archives to disk, dispatches to Platform Core, certifies scientific truth, or grants
engineering/regulatory approval. Platform Core package registration is two-phase and
reuses sc.research.reproducible-package.v1.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from .release import APP_VERSION
from .v510 import canonical, content_hash
from .v6120 import CORE_REPRODUCIBLE_RESEARCH_CONTRACT, _core_request
from .v640 import _authorize_core_route

VERSION = APP_VERSION
SCHEMA = "sc-workbench-reproducible-experiment-engineering-package/1.0"
PACKAGE_SCHEMA = "sc-workbench-reproducible-package/1.0"
EXPORT_PLAN_SCHEMA = "sc-workbench-reproducible-package-export-plan/1.0"
REPLAY_PLAN_SCHEMA = "sc-workbench-reproducible-package-replay-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-core-reproducible-package-plan/1.0"
INTEGRITY_SCHEMA = "sc-workbench-package-integrity-manifest/1.0"
MAX_COMPONENTS = 160
MAX_ARTIFACTS = 160
MAX_ENVIRONMENTS = 32
MAX_REPLAY_STEPS = 96
MAX_LINEAGE_REFS = 256
MAX_EMBEDDED_CANONICAL_BYTES = 2_000_000

router = APIRouter(tags=["workbench-v7120-reproducible-experiment-engineering-package"])

PackageKind = Literal["experiment", "engineering", "mixed"]
ComponentType = Literal[
    "dataset-workspace", "dataset", "variables", "parameter-set", "assumptions",
    "notebook-run", "workflow-graph-run", "execution-object", "solver-run",
    "simulation-run", "engineering-run", "design-space-run", "validation-report",
    "visual-workspace", "predictive-run", "forensic-run", "method", "source",
    "output", "artifact", "other",
]
EnvironmentType = Literal[
    "workbench", "python", "r", "julia", "ml", "container", "operating-system",
    "database", "external-service", "other",
]


def _embedded_size(value: Any) -> int:
    return len(canonical(value).encode("utf-8"))


def _safe_key(value: str) -> str:
    text = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in str(value or "").strip())
    return text.strip("-.") or "item"


class PackageComponentSpec(BaseModel):
    componentKey: str = Field(min_length=1, max_length=160)
    componentType: ComponentType
    componentRef: str = Field(default="", max_length=1000)
    versionRef: str = Field(default="", max_length=240)
    contentHash: str = Field(default="", max_length=256)
    required: bool = True
    mediaType: str = Field(default="application/json", max_length=160)
    payload: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_identity(self):
        if self.payload is None and not self.componentRef:
            raise ValueError("componentRef or payload is required")
        if self.payload is not None and _embedded_size(self.payload) > MAX_EMBEDDED_CANONICAL_BYTES:
            raise ValueError("embedded component exceeds bounded package size")
        if self.required and self.payload is None and not self.contentHash:
            raise ValueError("required reference-only components must declare contentHash")
        return self


class PackageEnvironmentSpec(BaseModel):
    environmentKey: str = Field(min_length=1, max_length=160)
    environmentType: EnvironmentType = "workbench"
    environmentRef: str = Field(min_length=1, max_length=1000)
    versionRef: str = Field(default="", max_length=240)
    contentHash: str = Field(default="", max_length=256)
    dependencies: List[str] = Field(default_factory=list, max_length=256)
    hardware: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PackageArtifactSpec(BaseModel):
    artifactKey: str = Field(min_length=1, max_length=160)
    artifactType: str = Field(min_length=1, max_length=160)
    artifactRef: str = Field(min_length=1, max_length=1000)
    mediaType: str = Field(default="application/octet-stream", max_length=160)
    contentHash: str = Field(min_length=1, max_length=256)
    sizeBytes: Optional[int] = Field(default=None, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ReplayStepSpec(BaseModel):
    stepKey: str = Field(min_length=1, max_length=160)
    action: str = Field(min_length=1, max_length=300)
    targetRef: str = Field(default="", max_length=1000)
    expectedHash: str = Field(default="", max_length=256)
    dependsOn: List[str] = Field(default_factory=list, max_length=64)
    instructions: Dict[str, Any] = Field(default_factory=dict)


class ReproPackageSpec(BaseModel):
    packageKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=300)
    projectEntityId: str = Field(min_length=1, max_length=255)
    packageKind: PackageKind = "mixed"
    components: List[PackageComponentSpec] = Field(min_length=1, max_length=MAX_COMPONENTS)
    environments: List[PackageEnvironmentSpec] = Field(default_factory=list, max_length=MAX_ENVIRONMENTS)
    artifacts: List[PackageArtifactSpec] = Field(default_factory=list, max_length=MAX_ARTIFACTS)
    replaySteps: List[ReplayStepSpec] = Field(default_factory=list, max_length=MAX_REPLAY_STEPS)
    lineageRefs: List[str] = Field(default_factory=list, max_length=MAX_LINEAGE_REFS)
    assumptions: List[str] = Field(default_factory=list, max_length=256)
    limitations: List[str] = Field(default_factory=list, max_length=256)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_keys(self):
        for values, label in [
            ([x.componentKey for x in self.components], "componentKey"),
            ([x.environmentKey for x in self.environments], "environmentKey"),
            ([x.artifactKey for x in self.artifacts], "artifactKey"),
            ([x.stepKey for x in self.replaySteps], "stepKey"),
        ]:
            if len(values) != len(set(values)):
                raise ValueError(f"{label} values must be unique")
        step_keys = {x.stepKey for x in self.replaySteps}
        for step in self.replaySteps:
            unknown = [x for x in step.dependsOn if x not in step_keys]
            if unknown:
                raise ValueError(f"replay step {step.stepKey} has unknown dependencies: {unknown}")
        return self


class PackageBuildRequest(BaseModel):
    package: ReproPackageSpec


class PackageValidateRequest(BaseModel):
    reproduciblePackage: Dict[str, Any]


class PackageReplayPlanRequest(BaseModel):
    reproduciblePackage: Dict[str, Any]
    mode: Literal["verify-only", "reconstruct", "replay"] = "reconstruct"


class PackageExportPlanRequest(BaseModel):
    reproduciblePackage: Dict[str, Any]
    archiveName: str = Field(default="", max_length=240)


class PackageAssembleRequest(BaseModel):
    packageKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=300)
    projectEntityId: str = Field(min_length=1, max_length=255)
    packageKind: PackageKind = "mixed"
    dataWorkspace: Optional[Dict[str, Any]] = None
    notebookRun: Optional[Dict[str, Any]] = None
    workflowGraphRun: Optional[Dict[str, Any]] = None
    visualWorkspace: Optional[Dict[str, Any]] = None
    validationReport: Optional[Dict[str, Any]] = None
    executionObjects: List[Dict[str, Any]] = Field(default_factory=list, max_length=96)
    additionalComponents: List[PackageComponentSpec] = Field(default_factory=list, max_length=96)
    environments: List[PackageEnvironmentSpec] = Field(default_factory=list, max_length=MAX_ENVIRONMENTS)
    artifacts: List[PackageArtifactSpec] = Field(default_factory=list, max_length=MAX_ARTIFACTS)
    lineageRefs: List[str] = Field(default_factory=list, max_length=MAX_LINEAGE_REFS)
    assumptions: List[str] = Field(default_factory=list, max_length=256)
    limitations: List[str] = Field(default_factory=list, max_length=256)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class CorePackagePlanRequest(BaseModel):
    reproduciblePackage: Dict[str, Any]
    coreProjectEntityId: str = Field(min_length=1, max_length=255)
    corePackageId: str = Field(default="", max_length=255)
    createdBy: str = Field(default="workbench", max_length=160)


def _normalized_component(item: PackageComponentSpec) -> Dict[str, Any]:
    payload_hash = content_hash(item.payload) if item.payload is not None else ""
    if item.contentHash and payload_hash and item.contentHash != payload_hash:
        raise ValueError(f"component {item.componentKey} contentHash does not match embedded payload")
    normalized_hash = item.contentHash or payload_hash
    return {
        "componentKey": item.componentKey,
        "componentType": item.componentType,
        "componentRef": item.componentRef,
        "versionRef": item.versionRef,
        "contentHash": normalized_hash,
        "required": item.required,
        "mediaType": item.mediaType,
        "payload": deepcopy(item.payload),
        "embedded": item.payload is not None,
        "integrityMode": "embedded-content-hash" if item.payload is not None else "declared-reference-hash",
        "metadata": item.metadata,
        "provenance": item.provenance,
    }


def _default_replay_steps(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    refs = [x.get("componentRef") for x in components if x.get("componentRef")]
    expected = [x.get("contentHash") for x in components if x.get("contentHash")]
    return [
        {"stepKey": "verify-package", "action": "verify package and component hashes", "targetRef": "", "expectedHash": "", "dependsOn": [], "instructions": {"failClosedOnMismatch": True}},
        {"stepKey": "resolve-components", "action": "resolve embedded or reference-first package components", "targetRef": "", "expectedHash": "", "dependsOn": ["verify-package"], "instructions": {"componentRefs": refs}},
        {"stepKey": "materialize-environment", "action": "materialize a compatible declared environment", "targetRef": "", "expectedHash": "", "dependsOn": ["resolve-components"], "instructions": {"automaticEnvironmentMutation": False}},
        {"stepKey": "request-explicit-replay", "action": "request explicit notebook/workflow/runtime replay if desired", "targetRef": "", "expectedHash": "", "dependsOn": ["materialize-environment"], "instructions": {"automaticExecution": False, "expectedComponentHashes": expected}},
        {"stepKey": "compare-results", "action": "compare replay outputs and V&V evidence with packaged expectations", "targetRef": "", "expectedHash": "", "dependsOn": ["request-explicit-replay"], "instructions": {"scientificValidityInferred": False}},
    ]


def build_package(spec: ReproPackageSpec) -> Dict[str, Any]:
    components = sorted((_normalized_component(x) for x in spec.components), key=lambda x: x["componentKey"])
    environments = sorted([x.model_dump() for x in spec.environments], key=lambda x: x["environmentKey"])
    artifacts = sorted([x.model_dump() for x in spec.artifacts], key=lambda x: x["artifactKey"])
    replay_steps = [x.model_dump() for x in spec.replaySteps] or _default_replay_steps(components)
    component_hashes = {x["componentKey"]: x["contentHash"] for x in components}
    environment_hashes = {x["environmentKey"]: x.get("contentHash", "") or content_hash(x) for x in environments}
    artifact_hashes = {x["artifactKey"]: x["contentHash"] for x in artifacts}
    integrity = {
        "schema": INTEGRITY_SCHEMA,
        "componentHashes": component_hashes,
        "environmentHashes": environment_hashes,
        "artifactHashes": artifact_hashes,
        "requiredComponentCount": sum(1 for x in components if x["required"]),
        "embeddedComponentCount": sum(1 for x in components if x["embedded"]),
        "allRequiredComponentsHashed": all(bool(x["contentHash"]) for x in components if x["required"]),
    }
    integrity["integrityManifestHash"] = content_hash(integrity)
    record = {
        "ok": True,
        "schema": PACKAGE_SCHEMA,
        "version": VERSION,
        "packageKey": spec.packageKey,
        "title": spec.title,
        "projectEntityId": spec.projectEntityId,
        "packageKind": spec.packageKind,
        "components": components,
        "environments": environments,
        "artifacts": artifacts,
        "replaySteps": replay_steps,
        "lineageRefs": sorted(set(spec.lineageRefs)),
        "assumptions": spec.assumptions,
        "limitations": spec.limitations,
        "metadata": {**spec.metadata, "workbenchVersion": VERSION},
        "provenance": spec.provenance,
        "integrityManifest": integrity,
        "boundaries": {
            "automaticReplayAuthorized": False,
            "automaticStateRestoreAuthorized": False,
            "automaticEnvironmentMutationAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "reproducibilityCertified": False,
            "scientificValidityCertified": False,
            "engineeringSafetyCertified": False,
            "codeOrRegulatoryComplianceCertified": False,
            "truthDeterminationAuthorized": False,
        },
    }
    record["packageHash"] = content_hash(record)
    return record


def _component_from_payload(key: str, component_type: ComponentType, payload: Optional[Dict[str, Any]], ref_field: str = "") -> Optional[PackageComponentSpec]:
    if payload is None:
        return None
    ref = str(payload.get(ref_field, "")) if ref_field else ""
    return PackageComponentSpec(componentKey=key, componentType=component_type, componentRef=ref, payload=payload, required=True)


def assemble_package(req: PackageAssembleRequest) -> Dict[str, Any]:
    components: List[PackageComponentSpec] = []
    candidates = [
        _component_from_payload("data-workspace", "dataset-workspace", req.dataWorkspace, "workspaceRef"),
        _component_from_payload("notebook-run", "notebook-run", req.notebookRun, "notebookRunRef"),
        _component_from_payload("workflow-graph-run", "workflow-graph-run", req.workflowGraphRun, "graphRunRef"),
        _component_from_payload("visual-workspace", "visual-workspace", req.visualWorkspace, "visualWorkspaceRef"),
        _component_from_payload("validation-report", "validation-report", req.validationReport, "reportRef"),
    ]
    components.extend([x for x in candidates if x is not None])
    for index, execution in enumerate(req.executionObjects):
        ref = str(execution.get("objectRef") or execution.get("executionObjectRef") or "")
        key = str(execution.get("objectId") or execution.get("executionId") or f"execution-{index+1}")
        components.append(PackageComponentSpec(componentKey=f"execution-{_safe_key(key)}", componentType="execution-object", componentRef=ref, payload=execution, required=True))
    components.extend(req.additionalComponents)
    if not components:
        raise ValueError("assemble requires at least one Workbench component")
    return build_package(ReproPackageSpec(
        packageKey=req.packageKey,
        title=req.title,
        projectEntityId=req.projectEntityId,
        packageKind=req.packageKind,
        components=components,
        environments=req.environments,
        artifacts=req.artifacts,
        lineageRefs=req.lineageRefs,
        assumptions=req.assumptions,
        limitations=req.limitations,
        metadata=req.metadata,
        provenance=req.provenance,
    ))


def validate_package(pkg: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    if pkg.get("schema") != PACKAGE_SCHEMA:
        reasons.append("package schema mismatch")
    claimed = pkg.get("packageHash", "")
    tmp = deepcopy(pkg)
    tmp.pop("packageHash", None)
    computed = content_hash(tmp)
    if not claimed or claimed != computed:
        reasons.append("package hash mismatch")
    integrity = pkg.get("integrityManifest") or {}
    integrity_claimed = integrity.get("integrityManifestHash", "")
    integ_tmp = deepcopy(integrity)
    integ_tmp.pop("integrityManifestHash", None)
    if not integrity_claimed or integrity_claimed != content_hash(integ_tmp):
        reasons.append("integrity manifest hash mismatch")
    for comp in pkg.get("components", []):
        if comp.get("embedded"):
            if not comp.get("contentHash") or comp.get("contentHash") != content_hash(comp.get("payload")):
                reasons.append(f"component hash mismatch: {comp.get('componentKey','unknown')}")
        if comp.get("required") and not comp.get("contentHash"):
            reasons.append(f"required component missing hash: {comp.get('componentKey','unknown')}")
    return {
        "ok": True,
        "schema": "sc-workbench-reproducible-package-validation/1.0",
        "version": VERSION,
        "valid": not reasons,
        "packageHash": claimed,
        "computedPackageHash": computed,
        "reasons": reasons,
        "reproducibilityCertified": False,
        "scientificValidityCertified": False,
    }


def replay_plan(req: PackageReplayPlanRequest) -> Dict[str, Any]:
    validation = validate_package(req.reproduciblePackage)
    if not validation["valid"]:
        raise ValueError("package integrity validation must pass before replay planning")
    pkg = req.reproduciblePackage
    plan = {
        "ok": True,
        "schema": REPLAY_PLAN_SCHEMA,
        "version": VERSION,
        "packageKey": pkg["packageKey"],
        "packageHash": pkg["packageHash"],
        "mode": req.mode,
        "steps": deepcopy(pkg.get("replaySteps", [])),
        "requiredEnvironments": [x.get("environmentRef") for x in pkg.get("environments", [])],
        "requiredComponents": [x.get("componentRef") or f"embedded:{x.get('componentKey')}" for x in pkg.get("components", []) if x.get("required")],
        "expectedComponentHashes": {x.get("componentKey"): x.get("contentHash") for x in pkg.get("components", [])},
        "operatorMustExplicitlyExecute": req.mode == "replay",
        "replayPerformed": False,
        "automaticExecutionReplayAuthorized": False,
        "automaticStateRestoreAuthorized": False,
        "hiddenInterpreterStateReplayAuthorized": False,
        "environmentCompatibilityMustBeChecked": True,
        "reproducibilityCertified": False,
    }
    plan["replayPlanHash"] = content_hash(plan)
    return plan


def export_plan(req: PackageExportPlanRequest) -> Dict[str, Any]:
    validation = validate_package(req.reproduciblePackage)
    if not validation["valid"]:
        raise ValueError("package integrity validation must pass before export planning")
    pkg = req.reproduciblePackage
    archive_name = req.archiveName or f"{_safe_key(pkg['packageKey'])}-{pkg['packageHash'][:12]}.zip"
    files = [{"path": "manifest.json", "contentHash": pkg["packageHash"], "source": "package-manifest"}]
    for comp in pkg.get("components", []):
        path = f"components/{_safe_key(comp['componentKey'])}.json"
        files.append({"path": path, "contentHash": comp.get("contentHash", ""), "source": "embedded-payload" if comp.get("embedded") else "reference-descriptor", "componentRef": comp.get("componentRef", "")})
    for env in pkg.get("environments", []):
        files.append({"path": f"environments/{_safe_key(env['environmentKey'])}.json", "contentHash": env.get("contentHash", "") or content_hash(env), "source": "environment-descriptor"})
    for artifact in pkg.get("artifacts", []):
        files.append({"path": f"artifacts/{_safe_key(artifact['artifactKey'])}.ref.json", "contentHash": artifact.get("contentHash", ""), "source": "artifact-reference", "artifactRef": artifact.get("artifactRef", "")})
    record = {
        "ok": True,
        "schema": EXPORT_PLAN_SCHEMA,
        "version": VERSION,
        "packageHash": pkg["packageHash"],
        "archiveName": archive_name,
        "files": files,
        "fileCount": len(files),
        "archiveWritePerformed": False,
        "callerMustMaterializeReferences": True,
        "automaticFilesystemWriteAuthorized": False,
    }
    record["exportPlanHash"] = content_hash(record)
    return record


def core_package_plan(req: CorePackagePlanRequest) -> Dict[str, Any]:
    validation = validate_package(req.reproduciblePackage)
    if not validation["valid"]:
        raise ValueError("package integrity validation must pass before Core planning")
    pkg = req.reproduciblePackage
    if not req.corePackageId:
        path = f"/v1/research/reproducible/projects/{req.coreProjectEntityId}/packages"
        data = {
            "package_key": pkg["packageKey"],
            "title": pkg["title"],
            "purpose": "Reproduce declared Workbench experiment/engineering state",
            "status": "draft",
            "manifest_version": "1.0",
            "provenance": pkg.get("provenance", {}),
            "metadata": {"workbench_package_hash": pkg["packageHash"], "workbench_version": VERSION, "package_kind": pkg.get("packageKind")},
        }
        return {
            "ok": True,
            "schema": CORE_PLAN_SCHEMA,
            "version": VERSION,
            "coreContract": CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
            "phase": "create-core-reproducible-package",
            "corePackageIdMustComeFromCore": True,
            "coreRequest": _core_request(path, data, "create-reproducible-package", contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT),
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
        }
    pid = req.corePackageId
    base = f"/v1/research/reproducible/packages/{pid}"
    requests: List[Dict[str, Any]] = []
    type_map = {
        "dataset-workspace": "dataset", "dataset": "dataset", "variables": "methodology",
        "parameter-set": "methodology", "assumptions": "methodology", "notebook-run": "analysis_run",
        "workflow-graph-run": "analysis_run", "execution-object": "analysis_run", "solver-run": "analysis_run",
        "simulation-run": "analysis_run", "engineering-run": "analysis_run", "design-space-run": "analysis_run",
        "validation-report": "evidence", "visual-workspace": "visualization", "predictive-run": "analysis_run",
        "forensic-run": "investigation", "method": "methodology", "source": "literature", "output": "analysis_output",
        "artifact": "other", "other": "other",
    }
    for comp in pkg.get("components", []):
        requests.append(_core_request(
            base + "/components",
            {"component_key": comp["componentKey"], "component_type": type_map.get(comp["componentType"], "other"), "component_ref": comp.get("componentRef") or f"sc://workbench/repro-package/{pkg['packageKey']}/components/{comp['componentKey']}", "version_ref": comp.get("versionRef") or None, "content_hash": comp.get("contentHash") or None, "required": bool(comp.get("required", True)), "metadata": {"workbench_component_type": comp["componentType"], "embedded": bool(comp.get("embedded")), **comp.get("metadata", {})}},
            "add-reproducible-component", contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        ))
    for art in pkg.get("artifacts", []):
        requests.append(_core_request(base + "/artifacts", {"artifact_key": art["artifactKey"], "artifact_type": art["artifactType"], "artifact_ref": art["artifactRef"], "media_type": art.get("mediaType") or None, "content_hash": art.get("contentHash") or None, "size_bytes": art.get("sizeBytes"), "provenance": art.get("provenance", {})}, "add-reproducible-artifact", contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT))
    for env in pkg.get("environments", []):
        requests.append(_core_request(base + "/environments", {"environment_key": env["environmentKey"], "environment_type": env["environmentType"], "environment_ref": env["environmentRef"], "version_ref": env.get("versionRef") or None, "content_hash": env.get("contentHash") or None, "details": {"dependencies": env.get("dependencies", []), "hardware": env.get("hardware", {}), **env.get("metadata", {})}, "provenance": pkg.get("provenance", {})}, "add-reproducible-environment", contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT))
    replay = replay_plan(PackageReplayPlanRequest(reproduciblePackage=pkg, mode="reconstruct"))
    requests.append(_core_request(base + "/replay-plans", {"plan_key": f"workbench-{pkg['packageKey']}-replay", "target_product": "workbench", "status": "prepared", "instructions": replay, "expected_outputs": [x.get("componentRef") for x in pkg.get("components", []) if x.get("componentType") in {"output", "visual-workspace", "validation-report"}], "provenance": pkg.get("provenance", {})}, "add-declarative-replay-plan", contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT))
    requests.append(_core_request(base + "/snapshots", {"provenance": pkg.get("provenance", {}), "created_by": req.createdBy}, "snapshot-reproducible-package", contract=CORE_REPRODUCIBLE_RESEARCH_CONTRACT))
    return {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "coreContract": CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        "phase": "register-core-reproducible-package-contents",
        "corePackageId": pid,
        "packageHash": pkg["packageHash"],
        "coreRequests": requests,
        "requestCount": len(requests),
        "orderingRequired": True,
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "automaticReplayAuthorized": False,
        "reproducibilityCertified": False,
        "scientificValidityCertified": False,
    }


def manifest() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "packageSchema": PACKAGE_SCHEMA,
        "coreContract": CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        "packageKinds": ["experiment", "engineering", "mixed"],
        "componentTypes": list(ComponentType.__args__),
        "limits": {"components": MAX_COMPONENTS, "artifacts": MAX_ARTIFACTS, "environments": MAX_ENVIRONMENTS, "embeddedCanonicalBytesPerComponent": MAX_EMBEDDED_CANONICAL_BYTES},
        "capabilities": {
            "contentAddressedPackage": True,
            "embeddedAndReferenceFirstComponents": True,
            "environmentManifest": True,
            "integrityManifest": True,
            "explicitReplayPlan": True,
            "exportPlan": True,
            "workbenchStateAssembly": True,
            "coreReproduciblePackagePlanning": True,
        },
        "boundaries": {
            "automaticReplayAuthorized": False,
            "automaticFilesystemWriteAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "reproducibilityCertified": False,
            "scientificValidityCertified": False,
            "engineeringSafetyCertified": False,
        },
    }


@router.get("/repro-package/manifest")
def get_manifest():
    return manifest()


@router.post("/repro-package/build")
def build_endpoint(req: PackageBuildRequest):
    try:
        return build_package(req.package)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/repro-package/assemble")
def assemble_endpoint(req: PackageAssembleRequest):
    try:
        return assemble_package(req)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/repro-package/validate")
def validate_endpoint(req: PackageValidateRequest):
    return validate_package(req.reproduciblePackage)


@router.post("/repro-package/replay/plan")
def replay_endpoint(req: PackageReplayPlanRequest):
    try:
        return replay_plan(req)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/repro-package/export/plan")
def export_endpoint(req: PackageExportPlanRequest):
    try:
        return export_plan(req)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/integration/core/repro-package/plan")
def core_plan_endpoint(req: CorePackagePlanRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token"), x_sc_gateway_service: str | None = Header(default=None, alias="X-SC-Gateway-Service"), x_sc_core_version: str | None = Header(default=None, alias="X-SC-Core-Version")):
    _authorize_core_route(x_sc_service_token)
    try:
        return core_package_plan(req)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/v7120/status")
def status():
    return {
        "ok": True,
        "version": VERSION,
        "release": "Reproducible Experiment & Engineering Package",
        "schema": SCHEMA,
        "contentAddressedPackages": True,
        "explicitReplayPlanning": True,
        "workbenchStateAssembly": True,
        "coreReproduciblePackageContract": CORE_REPRODUCIBLE_RESEARCH_CONTRACT,
        "automaticReplayAuthorized": False,
        "automaticFilesystemWriteAuthorized": False,
        "automaticCoreDispatchAuthorized": False,
        "reproducibilityCertified": False,
        "scientificValidityCertified": False,
        "engineeringSafetyCertified": False,
        "v7SeriesComplete": True,
    }

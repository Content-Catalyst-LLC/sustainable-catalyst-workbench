"""Workbench v5.0.0 — Sustainable Catalyst Integrated Research and Engineering Platform."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "5.0.0"
EXPECTED_STUDIOS = 28
router = APIRouter(prefix="/v500", tags=["workbench-v500"])

CORE_SURFACES: Set[str] = {
    "workbench", "lab", "site-intelligence", "decision-studio",
    "research-librarian", "knowledge-library", "wordpress", "offline",
}
FORBIDDEN_AUTOMATIONS: Set[str] = {
    "automatic-publication", "automatic-certification", "automatic-device-execution",
    "automatic-destructive-sync", "automatic-high-stakes-decision", "remote-shell",
    "arbitrary-command-execution", "safety-bypass",
}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def slug(value: str, fallback: str = "platform") -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned or fallback


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def unique_strings(values: List[str]) -> List[str]:
    return sorted({str(v).strip() for v in values if str(v).strip()})


def topological_order(items: List[Dict[str, Any]]) -> Tuple[List[str], List[str], List[str]]:
    ids = [str(item.get("id", "")).strip() for item in items if str(item.get("id", "")).strip()]
    idset = set(ids)
    missing: Set[str] = set()
    deps: Dict[str, Set[str]] = {}
    for item in items:
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            continue
        values = {str(v).strip() for v in item.get("dependsOn", []) if str(v).strip()}
        missing.update(values - idset)
        deps[item_id] = values & idset
    order: List[str] = []
    ready = sorted([key for key, values in deps.items() if not values])
    while ready:
        key = ready.pop(0)
        order.append(key)
        for other in sorted(deps):
            if key in deps[other]:
                deps[other].remove(key)
                if not deps[other] and other not in order and other not in ready:
                    ready.append(other)
                    ready.sort()
    cycles = sorted(key for key, values in deps.items() if values)
    return order, sorted(missing), cycles


class SurfaceRegistryInput(BaseModel):
    surfaces: List[Dict[str, Any]] = Field(default_factory=list)
    requiredSurfaces: List[str] = Field(default_factory=lambda: sorted(CORE_SURFACES))


class PlatformProjectInput(BaseModel):
    projectId: str = ""
    title: str
    description: str = ""
    domains: List[str] = Field(default_factory=list)
    surfaces: List[Dict[str, Any]] = Field(default_factory=list)
    records: List[Dict[str, Any]] = Field(default_factory=list)
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    workflows: List[Dict[str, Any]] = Field(default_factory=list)
    teamId: str = ""
    dataClassification: Literal["public", "internal", "restricted", "sensitive"] = "internal"
    highStakes: bool = False
    offlineAllowed: bool = True


class PortfolioInput(BaseModel):
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    portfolioId: str = "sustainable-catalyst"
    title: str = "Sustainable Catalyst Project Portfolio"


class WorkflowPlanInput(BaseModel):
    workflowId: str = ""
    title: str
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    projectId: str = "default"
    highStakes: bool = False


class IntegrityAuditInput(BaseModel):
    project: Dict[str, Any]
    expectedSchema: str = "sc-workbench-integrated-project/1.0"
    requiredEvidenceIds: List[str] = Field(default_factory=list)
    requiredRequirementIds: List[str] = Field(default_factory=list)


class GovernanceGateInput(BaseModel):
    project: Dict[str, Any]
    integrity: Dict[str, Any] = Field(default_factory=dict)
    traceabilityComplete: bool = False
    securityReviewPassed: bool = False
    evaluationPassed: bool = False
    professionalReviewPassed: bool = False
    unresolvedCriticalFindings: int = Field(default=0, ge=0)
    humanApproved: bool = False
    approver: str = ""


class DeploymentPlanInput(BaseModel):
    project: Dict[str, Any]
    targets: List[str] = Field(default_factory=lambda: ["wordpress", "offline"])
    packageChecksumsVerified: bool = False
    backupVerified: bool = False
    rollbackVerified: bool = False
    governanceGate: Dict[str, Any] = Field(default_factory=dict)
    explicitApproval: bool = False


class DossierInput(BaseModel):
    project: Dict[str, Any]
    registry: Dict[str, Any] = Field(default_factory=dict)
    workflows: List[Dict[str, Any]] = Field(default_factory=list)
    integrity: Dict[str, Any] = Field(default_factory=dict)
    governance: Dict[str, Any] = Field(default_factory=dict)
    deployment: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)


class PlatformPackageInput(BaseModel):
    project: Dict[str, Any]
    dossier: Dict[str, Any] = Field(default_factory=dict)
    files: Dict[str, str] = Field(default_factory=dict)
    manifests: List[Dict[str, Any]] = Field(default_factory=list)
    includeSensitiveRecords: bool = False


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-integrated-platform-status/1.0",
        "version": VERSION,
        "expectedStudioCount": EXPECTED_STUDIOS,
        "integratedSurfaces": sorted(CORE_SURFACES),
        "browserLocalOperation": True,
        "privateWordPressStorage": True,
        "offlineOperation": True,
        "paidExternalServiceRequired": False,
        "automaticWorkflowExecutionAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticCertificationAuthorized": False,
        "automaticDeviceExecutionAuthorized": False,
        "automaticDestructiveSynchronizationAuthorized": False,
        "automaticHighStakesDecisionAuthorized": False,
        "remoteShellAuthorized": False,
        "arbitraryCommandExecutionAuthorized": False,
    }


def build_surface_registry(payload: SurfaceRegistryInput) -> Dict[str, Any]:
    normalized: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    duplicates: Set[str] = set()
    for raw in payload.surfaces:
        surface_id = slug(str(raw.get("id") or raw.get("surface") or ""), "surface")
        if surface_id in seen:
            duplicates.add(surface_id)
        seen.add(surface_id)
        state = str(raw.get("state", "unknown")).lower()
        if state not in {"ready", "degraded", "offline", "unavailable", "unknown"}:
            state = "unknown"
        record = {
            "id": surface_id,
            "label": str(raw.get("label") or surface_id.replace("-", " ").title()),
            "version": str(raw.get("version", "")),
            "state": state,
            "capabilities": unique_strings(list(raw.get("capabilities", []))),
            "schemaVersions": unique_strings(list(raw.get("schemaVersions", []))),
            "endpoint": str(raw.get("endpoint", "")),
            "required": bool(raw.get("required", surface_id in payload.requiredSurfaces)),
            "lastVerified": str(raw.get("lastVerified", "")),
        }
        record["surfaceHash"] = content_hash(record)
        normalized.append(record)
    by_id = {item["id"]: item for item in normalized}
    required = unique_strings(payload.requiredSurfaces)
    missing = sorted(set(required) - set(by_id))
    unavailable = sorted(item["id"] for item in normalized if item["required"] and item["state"] in {"unavailable", "unknown"})
    degraded = sorted(item["id"] for item in normalized if item["state"] in {"degraded", "offline"})
    ready = not duplicates and not missing and not unavailable
    base = {
        "schema": "sc-workbench-surface-registry/1.0",
        "version": VERSION,
        "surfaces": sorted(normalized, key=lambda item: item["id"]),
        "requiredSurfaces": required,
        "duplicateSurfaceIds": sorted(duplicates),
        "missingRequiredSurfaces": missing,
        "unavailableRequiredSurfaces": unavailable,
        "degradedSurfaces": degraded,
        "ready": ready,
        "offlineFallbackAvailable": any(item["id"] == "offline" and item["state"] in {"ready", "degraded"} for item in normalized),
        "automaticConnectionAuthorized": False,
        "automaticCredentialUseAuthorized": False,
    }
    base["registryHash"] = content_hash(base)
    return base


def build_platform_project(payload: PlatformProjectInput) -> Dict[str, Any]:
    project_id = slug(payload.projectId or payload.title, "project")
    surface_ids = [slug(str(item.get("id") or item.get("surface") or ""), "surface") for item in payload.surfaces]
    duplicate_surfaces = sorted({value for value in surface_ids if surface_ids.count(value) > 1})
    record_ids = [str(item.get("id", "")).strip() for item in payload.records if str(item.get("id", "")).strip()]
    duplicate_records = sorted({value for value in record_ids if record_ids.count(value) > 1})
    requirement_ids = [str(item.get("id", "")).strip() for item in payload.requirements if str(item.get("id", "")).strip()]
    evidence_ids = [str(item.get("id", "")).strip() for item in payload.evidence if str(item.get("id", "")).strip()]
    blockers: List[Dict[str, str]] = []
    if duplicate_surfaces:
        blockers.append({"code": "duplicate-surface", "message": ", ".join(duplicate_surfaces)})
    if duplicate_records:
        blockers.append({"code": "duplicate-record", "message": ", ".join(duplicate_records)})
    if not payload.domains:
        blockers.append({"code": "domain-required", "message": "At least one scientific, engineering, sustainability, or research domain is required."})
    if not payload.requirements:
        blockers.append({"code": "requirements-required", "message": "Define traceable project requirements."})
    if payload.highStakes and not any(bool(item.get("professionalReviewRequired")) for item in payload.requirements):
        blockers.append({"code": "professional-review-boundary-required", "message": "High-stakes projects must carry an explicit professional-review requirement."})
    base = {
        "schema": "sc-workbench-integrated-project/1.0",
        "version": VERSION,
        "projectId": project_id,
        "title": payload.title.strip(),
        "description": payload.description.strip(),
        "domains": unique_strings(payload.domains),
        "surfaces": payload.surfaces,
        "surfaceIds": sorted(set(surface_ids)),
        "records": payload.records,
        "recordIds": sorted(set(record_ids)),
        "requirements": payload.requirements,
        "requirementIds": sorted(set(requirement_ids)),
        "evidence": payload.evidence,
        "evidenceIds": sorted(set(evidence_ids)),
        "workflows": payload.workflows,
        "teamId": slug(payload.teamId, "") if payload.teamId else "",
        "dataClassification": payload.dataClassification,
        "highStakes": payload.highStakes,
        "offlineAllowed": payload.offlineAllowed,
        "blockers": blockers,
        "readyForIntegrityAudit": not blockers,
        "humanReviewRequired": True,
        "automaticProjectExecutionAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticCertificationAuthorized": False,
        "createdAt": utc_now(),
    }
    hashable = dict(base)
    hashable.pop("createdAt", None)
    base["projectHash"] = content_hash(hashable)
    return base


def build_portfolio(payload: PortfolioInput) -> Dict[str, Any]:
    projects = list(payload.projects)
    ids = [str(item.get("projectId", "")).strip() for item in projects if str(item.get("projectId", "")).strip()]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    by_domain: Dict[str, int] = {}
    by_state: Dict[str, int] = {}
    for project in projects:
        for domain in project.get("domains", []):
            by_domain[str(domain)] = by_domain.get(str(domain), 0) + 1
        state = str(project.get("state") or ("ready" if project.get("readyForIntegrityAudit") else "draft"))
        by_state[state] = by_state.get(state, 0) + 1
    base = {
        "schema": "sc-workbench-platform-portfolio/1.0",
        "version": VERSION,
        "portfolioId": slug(payload.portfolioId, "portfolio"),
        "title": payload.title,
        "projects": projects,
        "projectCount": len(projects),
        "duplicateProjectIds": duplicates,
        "projectsByDomain": dict(sorted(by_domain.items())),
        "projectsByState": dict(sorted(by_state.items())),
        "ready": bool(projects) and not duplicates,
        "automaticProjectMergeAuthorized": False,
        "automaticPortfolioPublicationAuthorized": False,
    }
    base["portfolioHash"] = content_hash(base)
    return base


def build_workflow_plan(payload: WorkflowPlanInput) -> Dict[str, Any]:
    stages: List[Dict[str, Any]] = []
    duplicate_ids: Set[str] = set()
    seen: Set[str] = set()
    for index, raw in enumerate(payload.stages):
        stage_id = slug(str(raw.get("id") or raw.get("title") or f"stage-{index+1}"), f"stage-{index+1}")
        if stage_id in seen:
            duplicate_ids.add(stage_id)
        seen.add(stage_id)
        stage = {
            "id": stage_id,
            "title": str(raw.get("title") or stage_id.replace("-", " ").title()),
            "surface": slug(str(raw.get("surface", "workbench")), "workbench"),
            "dependsOn": unique_strings(list(raw.get("dependsOn", []))),
            "requiredInputs": unique_strings(list(raw.get("requiredInputs", []))),
            "expectedOutputs": unique_strings(list(raw.get("expectedOutputs", []))),
            "approvalRequired": bool(raw.get("approvalRequired", False)),
            "professionalReviewRequired": bool(raw.get("professionalReviewRequired", False)),
        }
        stage["stageHash"] = content_hash(stage)
        stages.append(stage)
    order, missing, cycles = topological_order(stages)
    blockers: List[Dict[str, str]] = []
    if duplicate_ids:
        blockers.append({"code": "duplicate-stage", "message": ", ".join(sorted(duplicate_ids))})
    if missing:
        blockers.append({"code": "missing-stage-dependency", "message": ", ".join(missing)})
    if cycles:
        blockers.append({"code": "workflow-cycle", "message": ", ".join(cycles)})
    if payload.highStakes and not any(stage["professionalReviewRequired"] for stage in stages):
        blockers.append({"code": "professional-review-stage-required", "message": "High-stakes workflows require a qualified-review stage."})
    handoffs = []
    by_id = {stage["id"]: stage for stage in stages}
    for stage in stages:
        for dep in stage["dependsOn"]:
            if dep in by_id and by_id[dep]["surface"] != stage["surface"]:
                handoffs.append({"fromStage": dep, "toStage": stage["id"], "fromSurface": by_id[dep]["surface"], "toSurface": stage["surface"]})
    base = {
        "schema": "sc-workbench-integrated-workflow/1.0",
        "version": VERSION,
        "workflowId": slug(payload.workflowId or payload.title, "workflow"),
        "projectId": slug(payload.projectId, "default"),
        "title": payload.title,
        "stages": stages,
        "executionOrder": order,
        "crossSurfaceHandoffs": handoffs,
        "missingDependencies": missing,
        "cycleStages": cycles,
        "blockers": blockers,
        "ready": bool(stages) and not blockers,
        "automaticWorkflowExecutionAuthorized": False,
        "automaticHandoffDeliveryAuthorized": False,
    }
    base["workflowHash"] = content_hash(base)
    return base


def audit_integrity(payload: IntegrityAuditInput) -> Dict[str, Any]:
    project = payload.project
    findings: List[Dict[str, str]] = []
    if project.get("schema") != payload.expectedSchema:
        findings.append({"severity": "critical", "code": "schema-mismatch", "message": f"Expected {payload.expectedSchema}."})
    stored_hash = str(project.get("projectHash", ""))
    if not stored_hash:
        findings.append({"severity": "high", "code": "project-hash-missing", "message": "Project hash is required."})
    req_ids = set(project.get("requirementIds", []))
    ev_ids = set(project.get("evidenceIds", []))
    missing_req = sorted(set(payload.requiredRequirementIds) - req_ids)
    missing_ev = sorted(set(payload.requiredEvidenceIds) - ev_ids)
    if missing_req:
        findings.append({"severity": "high", "code": "required-requirement-missing", "message": ", ".join(missing_req)})
    if missing_ev:
        findings.append({"severity": "high", "code": "required-evidence-missing", "message": ", ".join(missing_ev)})
    record_ids = set(project.get("recordIds", []))
    broken_links = []
    for record in project.get("records", []):
        for linked in record.get("linkedRecordIds", []):
            if linked not in record_ids:
                broken_links.append({"recordId": record.get("id", ""), "missingRecordId": linked})
    if broken_links:
        findings.append({"severity": "high", "code": "broken-record-links", "message": str(len(broken_links))})
    critical = sum(1 for item in findings if item["severity"] == "critical")
    high = sum(1 for item in findings if item["severity"] == "high")
    base = {
        "schema": "sc-workbench-platform-integrity-audit/1.0",
        "version": VERSION,
        "projectId": project.get("projectId", ""),
        "projectHash": stored_hash,
        "findings": findings,
        "brokenRecordLinks": broken_links,
        "criticalFindingCount": critical,
        "highFindingCount": high,
        "passed": critical == 0 and high == 0,
        "humanReviewRequired": True,
        "automaticRepairAuthorized": False,
        "automaticRecordDeletionAuthorized": False,
    }
    base["auditHash"] = content_hash(base)
    return base


def evaluate_governance_gate(payload: GovernanceGateInput) -> Dict[str, Any]:
    blockers: List[Dict[str, str]] = []
    high_stakes = bool(payload.project.get("highStakes"))
    if not payload.integrity or not payload.integrity.get("passed"):
        blockers.append({"code": "integrity-required", "message": "A passing integrity audit is required."})
    if not payload.traceabilityComplete:
        blockers.append({"code": "traceability-incomplete", "message": "Requirement, evidence, workflow, and review traceability must be complete."})
    if not payload.securityReviewPassed:
        blockers.append({"code": "security-review-required", "message": "Security and privacy review must pass."})
    if not payload.evaluationPassed:
        blockers.append({"code": "evaluation-required", "message": "Production evaluation must pass."})
    if high_stakes and not payload.professionalReviewPassed:
        blockers.append({"code": "professional-review-required", "message": "High-stakes projects require qualified professional review."})
    if payload.unresolvedCriticalFindings:
        blockers.append({"code": "critical-findings-unresolved", "message": str(payload.unresolvedCriticalFindings)})
    if not payload.humanApproved or not payload.approver.strip():
        blockers.append({"code": "human-approval-required", "message": "A named human approver is required."})
    base = {
        "schema": "sc-workbench-platform-governance-gate/1.0",
        "version": VERSION,
        "projectId": payload.project.get("projectId", ""),
        "projectHash": payload.project.get("projectHash", ""),
        "highStakes": high_stakes,
        "approver": payload.approver.strip(),
        "blockers": blockers,
        "approved": not blockers,
        "state": "approved-for-human-controlled-release" if not blockers else "blocked",
        "automaticPublicationAuthorized": False,
        "automaticCertificationAuthorized": False,
        "automaticHighStakesDecisionAuthorized": False,
    }
    base["gateHash"] = content_hash(base)
    return base


def build_deployment_plan(payload: DeploymentPlanInput) -> Dict[str, Any]:
    blockers: List[Dict[str, str]] = []
    targets = unique_strings(payload.targets)
    allowed = {"wordpress", "offline", "browser", "team-workspace", "local-service"}
    unsupported = sorted(set(targets) - allowed)
    if unsupported:
        blockers.append({"code": "unsupported-target", "message": ", ".join(unsupported)})
    if not payload.packageChecksumsVerified:
        blockers.append({"code": "package-checksum-required", "message": "Package checksums must be verified."})
    if not payload.backupVerified:
        blockers.append({"code": "backup-required", "message": "A verified backup is required."})
    if not payload.rollbackVerified:
        blockers.append({"code": "rollback-required", "message": "Rollback must be tested."})
    if not payload.governanceGate.get("approved"):
        blockers.append({"code": "governance-gate-required", "message": "A passing governance gate is required."})
    if not payload.explicitApproval:
        blockers.append({"code": "explicit-approval-required", "message": "Deployment requires explicit human approval."})
    steps = [
        {"id": "verify-package", "action": "Verify content hashes and checksums.", "automatic": False},
        {"id": "create-backup", "action": "Create and verify a recovery checkpoint.", "automatic": False},
        {"id": "deploy-targets", "action": "Deploy to approved targets only.", "automatic": False},
        {"id": "verify-health", "action": "Run activation, integration, and data-integrity checks.", "automatic": False},
        {"id": "record-receipt", "action": "Record deployment and rollback receipts.", "automatic": False},
    ]
    base = {
        "schema": "sc-workbench-platform-deployment-plan/1.0",
        "version": VERSION,
        "projectId": payload.project.get("projectId", ""),
        "targets": targets,
        "steps": steps,
        "blockers": blockers,
        "ready": bool(targets) and not blockers,
        "automaticDeploymentAuthorized": False,
        "automaticRollbackAuthorized": False,
        "remoteShellAuthorized": False,
    }
    base["deploymentPlanHash"] = content_hash(base)
    return base


def build_dossier(payload: DossierInput) -> Dict[str, Any]:
    components = {
        "project": payload.project,
        "registry": payload.registry,
        "workflows": payload.workflows,
        "integrity": payload.integrity,
        "governance": payload.governance,
        "deployment": payload.deployment,
        "artifacts": payload.artifacts,
    }
    component_hashes = {key: content_hash(value) for key, value in components.items()}
    ready = bool(payload.project.get("projectHash")) and bool(payload.integrity.get("passed")) and bool(payload.governance.get("approved"))
    base = {
        "schema": "sc-workbench-integrated-platform-dossier/1.0",
        "version": VERSION,
        "projectId": payload.project.get("projectId", ""),
        "components": components,
        "componentHashes": component_hashes,
        "readyForControlledRelease": ready,
        "humanReviewRequired": True,
        "automaticPublicationAuthorized": False,
        "automaticCertificationAuthorized": False,
    }
    base["dossierHash"] = content_hash(base)
    return base


def build_platform_package(payload: PlatformPackageInput) -> Dict[str, Any]:
    forbidden_keys = {"apiKey", "api_key", "password", "secret", "token", "accessToken", "refreshToken"}
    removed: List[str] = []

    def redact(value: Any, path: str = "") -> Any:
        if isinstance(value, dict):
            out = {}
            for key, item in value.items():
                key_path = f"{path}.{key}" if path else str(key)
                if key in forbidden_keys or any(term in str(key).lower() for term in ["password", "secret", "token", "api_key", "apikey"]):
                    removed.append(key_path)
                    continue
                if not payload.includeSensitiveRecords and str(key).lower() in {"sensitive", "restrictedrecords"}:
                    removed.append(key_path)
                    continue
                out[key] = redact(item, key_path)
            return out
        if isinstance(value, list):
            return [redact(item, f"{path}[]") for item in value]
        return value

    project = redact(payload.project, "project")
    dossier = redact(payload.dossier, "dossier")
    manifests = redact(payload.manifests, "manifests")
    file_hashes = {path: hashlib.sha256(text.encode("utf-8")).hexdigest() for path, text in sorted(payload.files.items())}
    blockers: List[Dict[str, str]] = []
    if not project.get("projectHash"):
        blockers.append({"code": "project-required", "message": "A content-hashed integrated project is required."})
    if not dossier.get("dossierHash"):
        blockers.append({"code": "dossier-required", "message": "A platform dossier is required."})
    if not payload.files:
        blockers.append({"code": "files-required", "message": "Include at least one portable artifact."})
    base = {
        "schema": "sc-workbench-integrated-platform-package/1.0",
        "version": VERSION,
        "project": project,
        "dossier": dossier,
        "manifests": manifests,
        "files": payload.files,
        "fileHashes": file_hashes,
        "removedSensitivePaths": sorted(set(removed)),
        "blockers": blockers,
        "ready": not blockers,
        "portable": True,
        "privateByDefault": True,
        "explicitImportRequired": True,
        "automaticInstallationAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticExecutionAuthorized": False,
    }
    base["packageHash"] = content_hash(base)
    return base


@router.get("/status")
def status() -> Dict[str, Any]:
    return status_record()


@router.post("/surfaces/registry")
def surfaces_registry(payload: SurfaceRegistryInput) -> Dict[str, Any]:
    return build_surface_registry(payload)


@router.post("/project/build")
def project_build(payload: PlatformProjectInput) -> Dict[str, Any]:
    return build_platform_project(payload)


@router.post("/portfolio/build")
def portfolio_build(payload: PortfolioInput) -> Dict[str, Any]:
    return build_portfolio(payload)


@router.post("/workflow/plan")
def workflow_plan(payload: WorkflowPlanInput) -> Dict[str, Any]:
    return build_workflow_plan(payload)


@router.post("/integrity/audit")
def integrity_audit(payload: IntegrityAuditInput) -> Dict[str, Any]:
    return audit_integrity(payload)


@router.post("/governance/gate")
def governance_gate(payload: GovernanceGateInput) -> Dict[str, Any]:
    return evaluate_governance_gate(payload)


@router.post("/deployment/plan")
def deployment_plan(payload: DeploymentPlanInput) -> Dict[str, Any]:
    return build_deployment_plan(payload)


@router.post("/dossier/build")
def dossier_build(payload: DossierInput) -> Dict[str, Any]:
    return build_dossier(payload)


@router.post("/package/build")
def package_build(payload: PlatformPackageInput) -> Dict[str, Any]:
    return build_platform_package(payload)

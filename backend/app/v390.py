"""Workbench v3.9.0 — Production Evaluation and Public Release Hardening."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Dict, List, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v390", tags=["Workbench v3.9.0"])
VERSION = "3.9.0"
SCHEMA_PREFIX = "sc-workbench-production-hardening"
REQUIRED_EVALUATIONS = [
    "accessibility",
    "performance",
    "security",
    "compatibility",
    "migration-stress",
    "failure-recovery",
    "onboarding",
    "extension-contract",
]
SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _finding(code: str, severity: str, message: str, blocking: bool = False) -> Dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "blocking": blocking}


class AccessibilityAuditRequest(BaseModel):
    pages_tested: int = 1
    keyboard_navigation: bool = True
    visible_focus: bool = True
    form_labels: bool = True
    landmarks: bool = True
    reduced_motion: bool = True
    screen_reader_smoke_test: bool = True
    contrast_failures: int = 0
    heading_failures: int = 0
    live_region_failures: int = 0
    mobile_overflow_failures: int = 0
    unresolved_critical: int = 0


class PerformanceBudgetRequest(BaseModel):
    transfer_kb: float = 500.0
    javascript_kb: float = 250.0
    css_kb: float = 120.0
    lcp_ms: float = 2000.0
    inp_ms: float = 150.0
    cls: float = 0.05
    api_p95_ms: float = 400.0
    memory_mb: float = 256.0
    budgets: Dict[str, float] = Field(default_factory=lambda: {
        "transfer_kb": 1500.0,
        "javascript_kb": 700.0,
        "css_kb": 250.0,
        "lcp_ms": 2500.0,
        "inp_ms": 200.0,
        "cls": 0.1,
        "api_p95_ms": 750.0,
        "memory_mb": 512.0,
    })


class SecurityAuditRequest(BaseModel):
    public_write_routes: int = 0
    nonce_protected_writes: bool = True
    capability_checks: bool = True
    secret_findings: int = 0
    high_dependency_findings: int = 0
    unsafe_html_findings: int = 0
    public_network_bind: bool = False
    export_controls_documented: bool = True
    threat_model_reviewed: bool = True
    destructive_actions_confirmed: bool = True


class CompatibilityMatrixRequest(BaseModel):
    browsers: List[str] = Field(default_factory=lambda: ["Chrome", "Firefox", "Safari", "Edge"])
    editors: List[str] = Field(default_factory=lambda: ["Gutenberg", "Classic Editor", "Elementor"])
    viewports: List[str] = Field(default_factory=lambda: ["360x800", "768x1024", "1440x900"])
    runtimes: List[str] = Field(default_factory=lambda: ["browser-local", "wordpress", "offline-fastapi"])
    failures: List[Dict[str, Any]] = Field(default_factory=list)


class MigrationStressRequest(BaseModel):
    projects: int = 100
    records: int = 10000
    corrupt_records: int = 0
    orphan_records: int = 0
    observed_duration_ms: int = 1000
    maximum_duration_ms: int = 5000
    backup_verified: bool = True
    rollback_verified: bool = True
    data_loss: bool = False


class FailureInjectionRequest(BaseModel):
    scenarios: List[Dict[str, Any]] = Field(default_factory=lambda: [
        {"id": "backend-offline", "severity": "high", "recovered": True, "dataLoss": False},
        {"id": "storage-quota", "severity": "high", "recovered": True, "dataLoss": False},
        {"id": "corrupt-import", "severity": "critical", "recovered": True, "dataLoss": False},
        {"id": "interrupted-update", "severity": "critical", "recovered": True, "dataLoss": False},
    ])


class OnboardingPackageRequest(BaseModel):
    personas: List[str] = Field(default_factory=lambda: ["researcher", "engineer", "educator", "reviewer"])
    quickstarts: List[str] = Field(default_factory=lambda: ["browser-local", "wordpress", "offline-install"])
    example_projects: int = 3
    accessibility_statement: bool = True
    privacy_statement: bool = True
    security_boundary: bool = True
    recovery_guide: bool = True
    support_route: bool = True


class ExtensionContractRequest(BaseModel):
    contract_name: str = "sc-workbench-extension-contract"
    contract_version: str = "1.0"
    stability: Literal["experimental", "preview", "stable"] = "stable"
    hooks: List[str] = Field(default_factory=list)
    rest_routes: List[str] = Field(default_factory=list)
    schemas: List[str] = Field(default_factory=list)
    deprecated_members: List[Dict[str, Any]] = Field(default_factory=list)
    breaking_changes: List[str] = Field(default_factory=list)
    compatibility_floor: str = "3.9.0"


class ReleaseGateRequest(BaseModel):
    evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_findings: List[Dict[str, Any]] = Field(default_factory=list)
    required_evaluations: List[str] = Field(default_factory=lambda: REQUIRED_EVALUATIONS.copy())
    documentation_complete: bool = True
    package_checksums_verified: bool = True
    rollback_verified: bool = True
    human_approval: bool = False


def build_accessibility_report(request: AccessibilityAuditRequest) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    boolean_checks = {
        "keyboard-navigation": (request.keyboard_navigation, "Keyboard navigation is incomplete."),
        "visible-focus": (request.visible_focus, "Visible focus indicators are incomplete."),
        "form-labels": (request.form_labels, "One or more form controls lack an accessible label."),
        "landmarks": (request.landmarks, "Page landmarks require review."),
        "reduced-motion": (request.reduced_motion, "Reduced-motion behavior is incomplete."),
        "screen-reader-smoke-test": (request.screen_reader_smoke_test, "Screen-reader smoke testing is incomplete."),
    }
    for code, (passed, message) in boolean_checks.items():
        if not passed:
            findings.append(_finding(code, "high", message, True))
    counts = {
        "contrast": request.contrast_failures,
        "headings": request.heading_failures,
        "liveRegions": request.live_region_failures,
        "mobileOverflow": request.mobile_overflow_failures,
    }
    for code, count in counts.items():
        if count:
            findings.append(_finding(code, "high", f"{count} unresolved {code} finding(s).", True))
    if request.unresolved_critical:
        findings.append(_finding("unresolved-critical", "critical", f"{request.unresolved_critical} critical accessibility finding(s) remain.", True))
    report = {
        "schema": f"{SCHEMA_PREFIX}-accessibility-report/1.0",
        "type": "accessibility",
        "version": VERSION,
        "target": "WCAG 2.2 AA evaluation target",
        "certificationClaim": False,
        "pagesTested": max(request.pages_tested, 0),
        "checks": {name: passed for name, (passed, _) in boolean_checks.items()},
        "failureCounts": counts,
        "findings": findings,
        "ready": not any(item["blocking"] for item in findings),
        "humanReviewRequired": True,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_performance_report(request: PerformanceBudgetRequest) -> Dict[str, Any]:
    observed = {
        "transfer_kb": request.transfer_kb,
        "javascript_kb": request.javascript_kb,
        "css_kb": request.css_kb,
        "lcp_ms": request.lcp_ms,
        "inp_ms": request.inp_ms,
        "cls": request.cls,
        "api_p95_ms": request.api_p95_ms,
        "memory_mb": request.memory_mb,
    }
    results, findings = {}, []
    for metric, value in observed.items():
        budget = float(request.budgets.get(metric, value))
        passed = value <= budget
        results[metric] = {"observed": value, "budget": budget, "passed": passed}
        if not passed:
            findings.append(_finding(f"budget-{metric}", "high", f"{metric} exceeds its release budget.", True))
    report = {
        "schema": f"{SCHEMA_PREFIX}-performance-report/1.0",
        "type": "performance",
        "version": VERSION,
        "metrics": results,
        "findings": findings,
        "ready": not findings,
        "syntheticMeasurement": True,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_security_report(request: SecurityAuditRequest) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    if request.public_write_routes:
        findings.append(_finding("public-write-routes", "critical", "Unauthenticated public write routes were detected.", True))
    if not request.nonce_protected_writes:
        findings.append(_finding("missing-nonce", "critical", "Authenticated browser writes lack nonce protection.", True))
    if not request.capability_checks:
        findings.append(_finding("missing-capability-checks", "critical", "Write routes lack capability checks.", True))
    if request.secret_findings:
        findings.append(_finding("secret-findings", "critical", f"{request.secret_findings} potential secret finding(s) remain.", True))
    if request.high_dependency_findings:
        findings.append(_finding("dependency-findings", "high", f"{request.high_dependency_findings} high-severity dependency finding(s) remain.", True))
    if request.unsafe_html_findings:
        findings.append(_finding("unsafe-html", "high", f"{request.unsafe_html_findings} unsafe output finding(s) remain.", True))
    if request.public_network_bind:
        findings.append(_finding("public-network-bind", "critical", "The local service permits a public network bind.", True))
    for code, passed, message in [
        ("export-controls", request.export_controls_documented, "Data export controls are undocumented."),
        ("threat-model", request.threat_model_reviewed, "Threat-model review is incomplete."),
        ("destructive-confirmation", request.destructive_actions_confirmed, "Destructive actions lack explicit confirmation."),
    ]:
        if not passed:
            findings.append(_finding(code, "high", message, True))
    report = {
        "schema": f"{SCHEMA_PREFIX}-security-report/1.0",
        "type": "security",
        "version": VERSION,
        "findings": findings,
        "ready": not findings,
        "remoteShellAllowed": False,
        "arbitraryCommandExecutionAllowed": False,
        "automaticCloudUpload": False,
        "humanReviewRequired": True,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_compatibility_report(request: CompatibilityMatrixRequest) -> Dict[str, Any]:
    matrix_size = len(request.browsers) * len(request.editors) * len(request.viewports) * len(request.runtimes)
    failures = []
    for raw in request.failures:
        item = dict(raw)
        severity = str(item.get("severity", "medium")).lower()
        item["severity"] = severity if severity in SEVERITY_ORDER else "medium"
        item["blocking"] = bool(item.get("blocking", SEVERITY_ORDER[item["severity"]] >= SEVERITY_ORDER["high"]))
        failures.append(item)
    report = {
        "schema": f"{SCHEMA_PREFIX}-compatibility-report/1.0",
        "type": "compatibility",
        "version": VERSION,
        "browsers": request.browsers,
        "editors": request.editors,
        "viewports": request.viewports,
        "runtimes": request.runtimes,
        "matrixSize": matrix_size,
        "failures": failures,
        "ready": matrix_size > 0 and not any(item["blocking"] for item in failures),
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_migration_stress_report(request: MigrationStressRequest) -> Dict[str, Any]:
    findings = []
    if request.observed_duration_ms > request.maximum_duration_ms:
        findings.append(_finding("migration-duration", "high", "Migration exceeded the maximum duration budget.", True))
    if not request.backup_verified:
        findings.append(_finding("backup-unverified", "critical", "Pre-migration backup was not verified.", True))
    if not request.rollback_verified:
        findings.append(_finding("rollback-unverified", "critical", "Migration rollback was not verified.", True))
    if request.data_loss:
        findings.append(_finding("data-loss", "critical", "Migration stress testing reported data loss.", True))
    total = max(request.records, 0)
    throughput = round(total / max(request.observed_duration_ms / 1000.0, 0.001), 2)
    report = {
        "schema": f"{SCHEMA_PREFIX}-migration-stress-report/1.0",
        "type": "migration-stress",
        "version": VERSION,
        "projects": max(request.projects, 0),
        "records": total,
        "corruptRecords": max(request.corrupt_records, 0),
        "orphanRecords": max(request.orphan_records, 0),
        "observedDurationMs": request.observed_duration_ms,
        "maximumDurationMs": request.maximum_duration_ms,
        "throughputRecordsPerSecond": throughput,
        "backupVerified": request.backup_verified,
        "rollbackVerified": request.rollback_verified,
        "findings": findings,
        "ready": not findings,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_failure_recovery_report(request: FailureInjectionRequest) -> Dict[str, Any]:
    normalized, findings = [], []
    for index, raw in enumerate(request.scenarios):
        item = dict(raw)
        item["id"] = str(item.get("id") or f"scenario-{index + 1}")
        severity = str(item.get("severity", "medium")).lower()
        item["severity"] = severity if severity in SEVERITY_ORDER else "medium"
        item["recovered"] = bool(item.get("recovered", False))
        item["dataLoss"] = bool(item.get("dataLoss", False))
        normalized.append(item)
        if item["dataLoss"]:
            findings.append(_finding(f"{item['id']}-data-loss", "critical", f"{item['id']} caused data loss.", True))
        elif not item["recovered"] and SEVERITY_ORDER[item["severity"]] >= SEVERITY_ORDER["high"]:
            findings.append(_finding(f"{item['id']}-unrecovered", item["severity"], f"{item['id']} did not recover.", True))
    report = {
        "schema": f"{SCHEMA_PREFIX}-failure-recovery-report/1.0",
        "type": "failure-recovery",
        "version": VERSION,
        "scenarios": normalized,
        "scenarioCount": len(normalized),
        "findings": findings,
        "ready": bool(normalized) and not findings,
        "automaticDataDeletion": False,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_onboarding_package(request: OnboardingPackageRequest) -> Dict[str, Any]:
    missing = []
    if not request.personas:
        missing.append("personas")
    if not request.quickstarts:
        missing.append("quickstarts")
    if request.example_projects < 1:
        missing.append("example-projects")
    for field_name in ["accessibility_statement", "privacy_statement", "security_boundary", "recovery_guide", "support_route"]:
        if not getattr(request, field_name):
            missing.append(field_name.replace("_", "-"))
    package = {
        "schema": f"{SCHEMA_PREFIX}-onboarding-package/1.0",
        "type": "onboarding",
        "version": VERSION,
        "personas": request.personas,
        "quickstarts": request.quickstarts,
        "exampleProjects": request.example_projects,
        "missingItems": missing,
        "ready": not missing,
        "claimsProductionCertification": False,
    }
    package["packageHash"] = stable_hash(package)
    return {"ok": package["ready"], "package": package}


def build_extension_contract(request: ExtensionContractRequest) -> Dict[str, Any]:
    blocking = []
    if request.stability == "stable" and request.breaking_changes:
        blocking.append("stable-contract-has-breaking-changes")
    if not request.schemas:
        blocking.append("schemas-required")
    contract = {
        "schema": f"{SCHEMA_PREFIX}-extension-contract/1.0",
        "type": "extension-contract",
        "version": VERSION,
        "contractName": request.contract_name,
        "contractVersion": request.contract_version,
        "stability": request.stability,
        "hooks": sorted(set(request.hooks)),
        "restRoutes": sorted(set(request.rest_routes)),
        "schemas": sorted(set(request.schemas)),
        "deprecatedMembers": request.deprecated_members,
        "breakingChanges": request.breaking_changes,
        "compatibilityFloor": request.compatibility_floor,
        "blockingIssues": blocking,
        "ready": not blocking,
    }
    contract["contractHash"] = stable_hash(contract)
    return {"ok": contract["ready"], "contract": contract}


def build_release_gate(request: ReleaseGateRequest) -> Dict[str, Any]:
    evaluation_map = {str(item.get("type", "")): item for item in request.evaluations}
    missing = [item for item in request.required_evaluations if item not in evaluation_map]
    failed = [key for key, item in evaluation_map.items() if not bool(item.get("ready", False))]
    unresolved = []
    for raw in request.unresolved_findings:
        item = dict(raw)
        severity = str(item.get("severity", "medium")).lower()
        item["severity"] = severity if severity in SEVERITY_ORDER else "medium"
        item["blocking"] = bool(item.get("blocking", SEVERITY_ORDER[item["severity"]] >= SEVERITY_ORDER["high"]))
        unresolved.append(item)
    blocking_findings = [item for item in unresolved if item["blocking"]]
    blockers = []
    if missing:
        blockers.append("missing-required-evaluations")
    if failed:
        blockers.append("failed-evaluations")
    if blocking_findings:
        blockers.append("unresolved-high-or-critical-findings")
    if not request.documentation_complete:
        blockers.append("documentation-incomplete")
    if not request.package_checksums_verified:
        blockers.append("package-checksums-unverified")
    if not request.rollback_verified:
        blockers.append("rollback-unverified")
    if not request.human_approval:
        blockers.append("human-approval-required")
    gate = {
        "schema": f"{SCHEMA_PREFIX}-release-gate/1.0",
        "type": "release-gate",
        "version": VERSION,
        "requiredEvaluations": request.required_evaluations,
        "receivedEvaluations": sorted(evaluation_map),
        "missingEvaluations": missing,
        "failedEvaluations": failed,
        "unresolvedFindings": unresolved,
        "blockingFindings": blocking_findings,
        "documentationComplete": request.documentation_complete,
        "packageChecksumsVerified": request.package_checksums_verified,
        "rollbackVerified": request.rollback_verified,
        "humanApproval": request.human_approval,
        "blockingIssues": blockers,
        "status": "ready-for-public-release" if not blockers else "hold",
        "ready": not blockers,
        "automaticPublicationAuthorized": False,
    }
    gate["gateHash"] = stable_hash(gate)
    return {"ok": gate["ready"], "gate": gate}


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": f"{SCHEMA_PREFIX}-status/1.0",
        "version": VERSION,
        "requiredEvaluations": REQUIRED_EVALUATIONS,
        "automaticPublicationAuthorized": False,
        "humanReleaseApprovalRequired": True,
        "productionCertificationClaim": False,
    }


@router.get("/status")
def status_route() -> Dict[str, Any]:
    return status()


@router.post("/accessibility/audit")
def accessibility_route(request: AccessibilityAuditRequest) -> Dict[str, Any]:
    return build_accessibility_report(request)


@router.post("/performance/evaluate")
def performance_route(request: PerformanceBudgetRequest) -> Dict[str, Any]:
    return build_performance_report(request)


@router.post("/security/audit")
def security_route(request: SecurityAuditRequest) -> Dict[str, Any]:
    return build_security_report(request)


@router.post("/compatibility/matrix")
def compatibility_route(request: CompatibilityMatrixRequest) -> Dict[str, Any]:
    return build_compatibility_report(request)


@router.post("/migration/stress")
def migration_route(request: MigrationStressRequest) -> Dict[str, Any]:
    return build_migration_stress_report(request)


@router.post("/failure/recovery")
def failure_route(request: FailureInjectionRequest) -> Dict[str, Any]:
    return build_failure_recovery_report(request)


@router.post("/onboarding/package")
def onboarding_route(request: OnboardingPackageRequest) -> Dict[str, Any]:
    return build_onboarding_package(request)


@router.post("/extension/contract")
def extension_route(request: ExtensionContractRequest) -> Dict[str, Any]:
    return build_extension_contract(request)


@router.post("/release/gate")
def release_gate_route(request: ReleaseGateRequest) -> Dict[str, Any]:
    return build_release_gate(request)

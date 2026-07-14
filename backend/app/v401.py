"""Workbench v4.0.1 — Connected Environment Activation and Integration Reliability."""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Dict, List, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v401", tags=["Workbench v4.0.1"])
VERSION = "4.0.1"
EXPECTED_STUDIO_COUNT = 22
SUPPORTED_PROJECT_SCHEMAS = {
    "sc-workbench-connected-environment-project/1.0": "4.0.0",
    "sc-workbench-persistent-project/1.0": "3.1.0",
    "sc-workbench-platform-handoff/1.0": "3.3.0",
    "sc-workbench-domain-laboratory-contract/1.0": "3.7.0",
    "sc-workbench-offline-sync-bundle/1.0": "3.8.0",
}
CRITICAL_CODES = {
    "primary-shortcode-missing",
    "studio-shortcode-missing",
    "literal-shortcode-output",
    "required-integration-offline",
    "schema-incompatible",
    "project-propagation-failed",
}
SAFE_REPAIR_ACTIONS = {
    "refresh-assets",
    "clear-workbench-cache",
    "re-register-shortcodes",
    "rebuild-studio-registry",
    "switch-to-browser-local",
    "switch-to-offline-service",
    "export-backup",
    "restore-last-known-good",
    "re-run-integration-probe",
}


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _unique(values: List[str]) -> List[str]:
    seen, result = set(), []
    for value in values:
        item = str(value).strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _version_tuple(value: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", str(value or ""))
    return tuple(int(part) for part in match.groups()) if match else (0, 0, 0)


class ActivationAuditRequest(BaseModel):
    primary_shortcode_registered: bool = True
    studios: List[Dict[str, Any]] = Field(default_factory=list)
    exposed_shortcode_text: List[str] = Field(default_factory=list)
    duplicate_shortcodes: List[str] = Field(default_factory=list)
    page_builder: str = "unknown"
    viewport: str = "desktop"


class SchemaCompatibilityRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(default_factory=list)
    supported_schemas: Dict[str, str] = Field(default_factory=lambda: SUPPORTED_PROJECT_SCHEMAS.copy())
    current_version: str = VERSION


class ProjectPropagationRequest(BaseModel):
    project_id: str = "default"
    studios: List[str] = Field(default_factory=list)
    active_project_by_studio: Dict[str, str] = Field(default_factory=dict)
    required_studios: List[str] = Field(default_factory=list)


class HandoffRoundTripRequest(BaseModel):
    source: str
    target: str
    packet: Dict[str, Any] = Field(default_factory=dict)
    receipt: Dict[str, Any] = Field(default_factory=dict)
    required_fields: List[str] = Field(default_factory=lambda: ["schema", "projectId", "source", "target"])


class AssetAuditRequest(BaseModel):
    assets: List[Dict[str, Any]] = Field(default_factory=list)
    expected_version: str = VERSION
    rendered_html: str = ""


class IntegrationProbeRequest(BaseModel):
    integrations: List[Dict[str, Any]] = Field(default_factory=list)
    offline_available: bool = True
    browser_local_available: bool = True


class RepairPlanRequest(BaseModel):
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    backup_verified: bool = False
    allow_destructive: bool = False


class FixtureEvaluationRequest(BaseModel):
    fixture: Dict[str, Any] = Field(default_factory=dict)


def build_activation_audit(request: ActivationAuditRequest) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    if not request.primary_shortcode_registered:
        findings.append({"code": "primary-shortcode-missing", "severity": "critical"})
    registered = 0
    rendered = 0
    for studio in request.studios:
        key = str(studio.get("key") or studio.get("studio") or "unknown")
        shortcode = str(studio.get("shortcode") or "")
        is_registered = bool(studio.get("registered", studio.get("available", False)))
        is_rendered = bool(studio.get("rendered", False))
        state = str(studio.get("state", "unknown"))
        if is_registered:
            registered += 1
        else:
            findings.append({"code": "studio-shortcode-missing", "severity": "critical", "studio": key, "shortcode": shortcode})
        if is_rendered and state not in {"empty", "error", "unavailable"}:
            rendered += 1
        elif is_registered:
            findings.append({"code": "studio-render-failed", "severity": "high", "studio": key, "state": state})
    for text in request.exposed_shortcode_text:
        findings.append({"code": "literal-shortcode-output", "severity": "critical", "sample": str(text)[:160]})
    for tag in _unique(request.duplicate_shortcodes):
        findings.append({"code": "duplicate-shortcode-owner", "severity": "high", "shortcode": tag})
    critical = [f for f in findings if f["severity"] == "critical"]
    audit = {
        "schema": "sc-workbench-connected-reliability-activation-audit/1.0",
        "version": VERSION,
        "expectedStudioCount": EXPECTED_STUDIO_COUNT,
        "observedStudioCount": len(request.studios),
        "registeredStudioCount": registered,
        "renderedStudioCount": rendered,
        "pageBuilder": request.page_builder,
        "viewport": request.viewport,
        "findings": findings,
        "criticalFindingCount": len(critical),
        "ready": not critical and registered == len(request.studios) and rendered == len(request.studios),
        "automaticRepairAuthorized": False,
    }
    audit["auditHash"] = stable_hash(audit)
    return {"ok": audit["ready"], "audit": audit}


def build_schema_compatibility(request: SchemaCompatibilityRequest) -> Dict[str, Any]:
    compatible, stale, incompatible, unknown = [], [], [], []
    current = _version_tuple(request.current_version)
    for index, record in enumerate(request.records):
        schema = str(record.get("schema", "")).strip()
        version = str(record.get("version", "0.0.0"))
        item = {"index": index, "id": record.get("id") or record.get("projectId"), "schema": schema, "version": version}
        if not schema:
            item["reason"] = "schema-missing"
            incompatible.append(item)
            continue
        if schema not in request.supported_schemas:
            item["reason"] = "schema-unknown"
            unknown.append(item)
            continue
        floor = request.supported_schemas[schema]
        item["compatibilityFloor"] = floor
        if _version_tuple(version) < _version_tuple(floor):
            item["reason"] = "below-compatibility-floor"
            incompatible.append(item)
        elif _version_tuple(version) < current:
            stale.append(item)
        else:
            compatible.append(item)
    report = {
        "schema": "sc-workbench-connected-reliability-schema-report/1.0",
        "version": VERSION,
        "compatible": compatible,
        "staleButSupported": stale,
        "unknownSchemas": unknown,
        "incompatible": incompatible,
        "migrationPreviewRequired": bool(stale or unknown or incompatible),
        "destructiveMigrationAuthorized": False,
        "ready": not incompatible,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_project_propagation(request: ProjectPropagationRequest) -> Dict[str, Any]:
    project_id = request.project_id.strip() or "default"
    studios = _unique(request.studios)
    required = _unique(request.required_studios or studios)
    actions, failed, already_active = [], [], []
    for studio in studios:
        current = str(request.active_project_by_studio.get(studio, ""))
        if current == project_id:
            already_active.append(studio)
        else:
            actions.append({"studio": studio, "action": "dispatch-project-change", "projectId": project_id})
    for studio in required:
        if studio not in studios:
            failed.append(studio)
    plan = {
        "schema": "sc-workbench-connected-reliability-project-propagation/1.0",
        "version": VERSION,
        "projectId": project_id,
        "studioCount": len(studios),
        "alreadyActive": already_active,
        "actions": actions,
        "missingRequiredStudios": failed,
        "event": "scwb:project-changed",
        "automaticDestructiveActionAuthorized": False,
        "ready": not failed,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": plan["ready"], "plan": plan}


def validate_handoff_roundtrip(request: HandoffRoundTripRequest) -> Dict[str, Any]:
    packet = dict(request.packet)
    receipt = dict(request.receipt)
    missing = [field for field in request.required_fields if not packet.get(field)]
    source_ok = str(packet.get("source", "")) == request.source
    target_ok = str(packet.get("target", "")) == request.target
    packet_hash = packet.get("packetHash") or stable_hash({k: v for k, v in packet.items() if k != "packetHash"})
    receipt_hash = receipt.get("packetHash") or receipt.get("receivedPacketHash")
    hash_ok = bool(receipt_hash) and receipt_hash == packet_hash
    accepted = str(receipt.get("status", "")).lower() in {"accepted", "received", "validated"}
    findings = []
    if missing: findings.append({"code": "handoff-required-fields-missing", "fields": missing})
    if not source_ok: findings.append({"code": "handoff-source-mismatch"})
    if not target_ok: findings.append({"code": "handoff-target-mismatch"})
    if not hash_ok: findings.append({"code": "handoff-receipt-hash-mismatch"})
    if not accepted: findings.append({"code": "handoff-not-accepted"})
    report = {
        "schema": "sc-workbench-connected-reliability-handoff-roundtrip/1.0",
        "version": VERSION,
        "source": request.source,
        "target": request.target,
        "packetHash": packet_hash,
        "receiptHashMatched": hash_ok,
        "accepted": accepted,
        "findings": findings,
        "ready": not findings,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_asset_audit(request: AssetAuditRequest) -> Dict[str, Any]:
    findings, seen = [], set()
    for asset in request.assets:
        handle = str(asset.get("handle", ""))
        loaded = bool(asset.get("loaded", False))
        version = str(asset.get("version", ""))
        if not loaded:
            findings.append({"code": "asset-missing", "severity": "high", "handle": handle})
        if handle in seen:
            findings.append({"code": "asset-duplicate", "severity": "high", "handle": handle})
        seen.add(handle)
        if version and version not in {request.expected_version, "filemtime"}:
            findings.append({"code": "asset-version-stale", "severity": "medium", "handle": handle, "version": version})
    literal = re.findall(r"\[sc_workbench_[a-z0-9_]+[^\]]*\]", request.rendered_html or "", flags=re.I)
    for sample in literal[:20]:
        findings.append({"code": "literal-shortcode-output", "severity": "critical", "sample": sample[:160]})
    report = {
        "schema": "sc-workbench-connected-reliability-asset-audit/1.0",
        "version": VERSION,
        "assetCount": len(request.assets),
        "findings": findings,
        "literalShortcodeCount": len(literal),
        "cacheBustStrategy": "filemtime",
        "ready": not any(item["severity"] in {"critical", "high"} for item in findings),
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_integration_probe(request: IntegrationProbeRequest) -> Dict[str, Any]:
    records, blocking, degraded = [], [], []
    for raw in request.integrations:
        item = dict(raw)
        integration_id = str(item.get("id", "unknown"))
        required = bool(item.get("required", False))
        status = str(item.get("status", "unknown")).lower()
        ready = status in {"ready", "online", "healthy"}
        fallback = None
        if not ready:
            if request.offline_available:
                fallback = "offline-fastapi"
            elif request.browser_local_available:
                fallback = "browser-local"
            record = {"id": integration_id, "required": required, "status": status, "fallback": fallback}
            if required and not fallback:
                blocking.append(record)
            else:
                degraded.append(record)
        records.append({"id": integration_id, "required": required, "status": status, "ready": ready, "fallback": fallback})
    report = {
        "schema": "sc-workbench-connected-reliability-integration-probe/1.0",
        "version": VERSION,
        "integrations": records,
        "blocking": blocking,
        "degraded": degraded,
        "offlineFallbackAvailable": request.offline_available,
        "browserLocalFallbackAvailable": request.browser_local_available,
        "ready": not blocking,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": report["ready"], "report": report}


def build_repair_plan(request: RepairPlanRequest) -> Dict[str, Any]:
    actions, blocked = [], []
    mapping = {
        "primary-shortcode-missing": "re-register-shortcodes",
        "studio-shortcode-missing": "rebuild-studio-registry",
        "literal-shortcode-output": "re-register-shortcodes",
        "asset-missing": "refresh-assets",
        "asset-version-stale": "clear-workbench-cache",
        "required-integration-offline": "switch-to-offline-service",
        "schema-incompatible": "restore-last-known-good",
        "project-propagation-failed": "re-run-integration-probe",
    }
    destructive_codes = {"schema-incompatible", "restore-failed", "migration-corrupt"}
    for finding in request.findings:
        code = str(finding.get("code", ""))
        action = mapping.get(code, "re-run-integration-probe")
        item = {"finding": code, "action": action, "safe": action in SAFE_REPAIR_ACTIONS}
        if code in destructive_codes and not request.backup_verified:
            item["blockedBy"] = "verified-backup-required"
            blocked.append(item)
        elif code in destructive_codes and not request.allow_destructive:
            item["blockedBy"] = "explicit-destructive-authorization-required"
            blocked.append(item)
        else:
            actions.append(item)
    plan = {
        "schema": "sc-workbench-connected-reliability-repair-plan/1.0",
        "version": VERSION,
        "actions": actions,
        "blockedActions": blocked,
        "backupVerified": request.backup_verified,
        "automaticExecutionAuthorized": False,
        "automaticDeletionAuthorized": False,
        "ready": not blocked,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": plan["ready"], "plan": plan}


def evaluate_fixture(request: FixtureEvaluationRequest) -> Dict[str, Any]:
    fixture = request.fixture
    project = fixture.get("project") if isinstance(fixture.get("project"), dict) else {}
    studios = fixture.get("studios") if isinstance(fixture.get("studios"), list) else []
    integrations = fixture.get("integrations") if isinstance(fixture.get("integrations"), list) else []
    workflow = fixture.get("workflow") if isinstance(fixture.get("workflow"), list) else []
    records = fixture.get("records") if isinstance(fixture.get("records"), list) else []
    required = fixture.get("requiredStudios") if isinstance(fixture.get("requiredStudios"), list) else []
    studio_keys = {str(item.get("key", item)) if isinstance(item, dict) else str(item) for item in studios}
    missing = [key for key in required if key not in studio_keys]
    integration_failures = [item for item in integrations if item.get("required") and str(item.get("status", "")).lower() not in {"ready", "online", "healthy"} and not item.get("fallback")]
    workflow_issues = [item for item in workflow if item.get("blocked") or item.get("cycle")]
    record_ids = [str(item.get("id", "")) for item in records if isinstance(item, dict)]
    duplicate_records = sorted({rid for rid in record_ids if rid and record_ids.count(rid) > 1})
    findings = []
    if not project.get("projectId"): findings.append("project-id-missing")
    if missing: findings.append("required-studios-missing")
    if integration_failures: findings.append("required-integrations-unavailable")
    if workflow_issues: findings.append("workflow-blocked")
    if duplicate_records: findings.append("duplicate-record-identifiers")
    evaluation = {
        "schema": "sc-workbench-connected-reliability-fixture-evaluation/1.0",
        "version": VERSION,
        "projectId": project.get("projectId"),
        "studioCount": len(studio_keys),
        "requiredStudioCount": len(required),
        "missingRequiredStudios": missing,
        "integrationFailureCount": len(integration_failures),
        "workflowIssueCount": len(workflow_issues),
        "duplicateRecordIds": duplicate_records,
        "findings": findings,
        "ready": not findings,
        "humanReviewRequired": True,
    }
    evaluation["evaluationHash"] = stable_hash(evaluation)
    return {"ok": evaluation["ready"], "evaluation": evaluation}


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-connected-reliability-status/1.0",
        "version": VERSION,
        "milestone": "Connected Environment Activation and Integration Reliability",
        "expectedStudioCount": EXPECTED_STUDIO_COUNT,
        "offlineSupported": True,
        "browserLocalFallback": True,
        "renderRequired": False,
        "automaticRepairAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticDestructiveActionAuthorized": False,
    }


@router.get("/status")
def status_route() -> Dict[str, Any]:
    return status()


@router.post("/activation/audit")
def activation_audit_route(request: ActivationAuditRequest) -> Dict[str, Any]:
    return build_activation_audit(request)


@router.post("/schema/compatibility")
def schema_compatibility_route(request: SchemaCompatibilityRequest) -> Dict[str, Any]:
    return build_schema_compatibility(request)


@router.post("/project/propagation")
def project_propagation_route(request: ProjectPropagationRequest) -> Dict[str, Any]:
    return build_project_propagation(request)


@router.post("/handoff/roundtrip")
def handoff_roundtrip_route(request: HandoffRoundTripRequest) -> Dict[str, Any]:
    return validate_handoff_roundtrip(request)


@router.post("/assets/audit")
def asset_audit_route(request: AssetAuditRequest) -> Dict[str, Any]:
    return build_asset_audit(request)


@router.post("/integration/probe")
def integration_probe_route(request: IntegrationProbeRequest) -> Dict[str, Any]:
    return build_integration_probe(request)


@router.post("/repair/plan")
def repair_plan_route(request: RepairPlanRequest) -> Dict[str, Any]:
    return build_repair_plan(request)


@router.post("/fixture/evaluate")
def fixture_evaluate_route(request: FixtureEvaluationRequest) -> Dict[str, Any]:
    return evaluate_fixture(request)

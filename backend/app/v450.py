"""Workbench v4.5.0 — Extension SDK, Plugin Registry, and Third-Party Module Framework."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "4.5.0"
EXPECTED_STUDIOS = 27
router = APIRouter(prefix="/v450", tags=["workbench-v450"])

ExtensionState = Literal["draft", "review", "approved", "blocked", "deprecated"]
TrustTier = Literal["local", "community", "verified", "first-party"]
LifecycleAction = Literal["install", "activate", "deactivate", "update", "uninstall"]

ALLOWED_CAPABILITIES: Set[str] = {
    "project.read", "project.write", "record.read", "record.write",
    "dataset.read", "dataset.write", "evidence.read", "evidence.write",
    "workflow.read", "workflow.write", "review.read", "review.write",
    "ui.panel", "ui.command", "export.create", "network.fetch",
    "device.plan", "evaluation.read", "evaluation.write", "lab.read", "lab.write",
}
HIGH_RISK_CAPABILITIES: Set[str] = {
    "project.write", "record.write", "dataset.write", "evidence.write",
    "workflow.write", "review.write", "network.fetch", "device.plan",
    "evaluation.write", "lab.write",
}
FORBIDDEN_CAPABILITIES: Set[str] = {
    "shell.execute", "shell.remote", "process.spawn", "filesystem.unrestricted",
    "database.admin", "auth.bypass", "safety.bypass", "secrets.read",
    "device.execute", "publication.auto", "certification.auto",
}
ALLOWED_HOOKS: Set[str] = {
    "workbench.ready", "project.created", "project.opened", "project.saved",
    "dataset.ready", "dataset.validated", "workflow.planned", "workflow.completed",
    "evaluation.completed", "review.requested", "review.completed",
    "evidence.attached", "lab.experiment.planned", "export.prepared",
}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def slug(value: str, fallback: str = "extension") -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned or fallback


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_version(value: str) -> Tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?", (value or "").strip())
    if not match:
        raise ValueError(f"Invalid semantic version: {value}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def version_in_range(core_version: str, minimum: str, maximum: str = "") -> bool:
    core = parse_version(core_version)
    low = parse_version(minimum)
    if core < low:
        return False
    return not maximum or core <= parse_version(maximum)


class ExtensionManifestInput(BaseModel):
    extensionId: str = ""
    name: str
    version: str
    publisher: str
    description: str = ""
    entrypoint: str = "extension.js"
    minimumCoreVersion: str = "4.5.0"
    maximumCoreVersion: str = ""
    capabilities: List[str] = Field(default_factory=list)
    hooks: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    allowedHosts: List[str] = Field(default_factory=list)
    packageHash: str = ""
    signature: str = ""
    publicKeyId: str = ""
    license: str = ""
    repository: str = ""
    highRisk: bool = False


class CompatibilityInput(BaseModel):
    manifest: Dict[str, Any]
    coreVersion: str = VERSION
    availableCapabilities: List[str] = Field(default_factory=lambda: sorted(ALLOWED_CAPABILITIES))
    installedExtensions: Dict[str, str] = Field(default_factory=dict)


class RegistryEntryInput(BaseModel):
    manifest: Dict[str, Any]
    state: ExtensionState = "draft"
    trustTier: TrustTier = "local"
    reviewer: str = ""
    reviewNotes: List[str] = Field(default_factory=list)
    compatibility: Dict[str, Any] = Field(default_factory=dict)
    integrityVerified: bool = False
    signatureVerified: bool = False


class PermissionAuditInput(BaseModel):
    capabilities: List[str] = Field(default_factory=list)
    allowedHosts: List[str] = Field(default_factory=list)
    dataScopes: List[str] = Field(default_factory=list)
    explicitApproval: bool = False


class HookContractInput(BaseModel):
    extensionId: str
    hook: str
    handler: str
    inputSchema: Dict[str, Any] = Field(default_factory=dict)
    outputSchema: Dict[str, Any] = Field(default_factory=dict)
    timeoutMs: int = Field(default=5000, ge=100, le=30000)
    idempotent: bool = True
    retryLimit: int = Field(default=0, ge=0, le=5)
    capabilityScopes: List[str] = Field(default_factory=list)


class LifecyclePlanInput(BaseModel):
    action: LifecycleAction
    manifest: Dict[str, Any]
    installedVersion: str = ""
    compatibility: Dict[str, Any] = Field(default_factory=dict)
    integrityVerified: bool = False
    signatureVerified: bool = False
    backupVerified: bool = False
    explicitApproval: bool = False
    confirmationPhrase: str = ""


class SDKScaffoldInput(BaseModel):
    extensionId: str
    name: str
    publisher: str
    language: Literal["javascript", "typescript", "python"] = "javascript"
    capabilities: List[str] = Field(default_factory=lambda: ["project.read", "ui.panel"])
    hooks: List[str] = Field(default_factory=lambda: ["workbench.ready"])
    includeTests: bool = True
    includeDocumentation: bool = True


class ExtensionAuditInput(BaseModel):
    manifest: Dict[str, Any]
    sourceFiles: List[str] = Field(default_factory=list)
    sourceText: str = ""
    integrityVerified: bool = False
    signatureVerified: bool = False


class ExtensionPackageInput(BaseModel):
    manifest: Dict[str, Any]
    files: Dict[str, str] = Field(default_factory=dict)
    documentation: Dict[str, str] = Field(default_factory=dict)
    tests: Dict[str, str] = Field(default_factory=dict)
    audit: Dict[str, Any] = Field(default_factory=dict)
    compatibility: Dict[str, Any] = Field(default_factory=dict)
    signature: str = ""


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-extension-framework-status/1.0",
        "version": VERSION,
        "expectedStudioCount": EXPECTED_STUDIOS,
        "manifestSchema": "sc-workbench-extension-manifest/1.0",
        "allowedCapabilities": sorted(ALLOWED_CAPABILITIES),
        "allowedHooks": sorted(ALLOWED_HOOKS),
        "privateRegistryByDefault": True,
        "browserDevelopmentMode": True,
        "offlineSDK": True,
        "paidExternalRegistryRequired": False,
        "automaticExtensionInstallationAuthorized": False,
        "automaticExtensionActivationAuthorized": False,
        "automaticPrivilegeEscalationAuthorized": False,
        "arbitraryCodeExecutionAuthorized": False,
        "remoteShellAuthorized": False,
        "automaticPublicationAuthorized": False,
    }


def normalize_manifest(payload: ExtensionManifestInput) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    try:
        parse_version(payload.version)
    except ValueError:
        findings.append({"level": "block", "code": "invalid-extension-version", "message": "Extension version must use semantic versioning."})
    try:
        parse_version(payload.minimumCoreVersion)
        if payload.maximumCoreVersion:
            parse_version(payload.maximumCoreVersion)
    except ValueError:
        findings.append({"level": "block", "code": "invalid-core-version-range", "message": "Core compatibility versions must use semantic versioning."})

    capabilities = sorted(set(item.strip() for item in payload.capabilities if item.strip()))
    hooks = sorted(set(item.strip() for item in payload.hooks if item.strip()))
    permissions = sorted(set(item.strip() for item in payload.permissions if item.strip()))
    forbidden = sorted(set(capabilities) & FORBIDDEN_CAPABILITIES)
    unknown = sorted(set(capabilities) - ALLOWED_CAPABILITIES - FORBIDDEN_CAPABILITIES)
    invalid_hooks = sorted(set(hooks) - ALLOWED_HOOKS)
    if forbidden:
        findings.append({"level": "block", "code": "forbidden-capability", "message": ", ".join(forbidden)})
    if unknown:
        findings.append({"level": "block", "code": "unknown-capability", "message": ", ".join(unknown)})
    if invalid_hooks:
        findings.append({"level": "block", "code": "unknown-hook", "message": ", ".join(invalid_hooks)})
    if "*" in permissions or "*" in capabilities:
        findings.append({"level": "block", "code": "wildcard-permission-denied", "message": "Wildcard capability and permission scopes are not supported."})
    if payload.allowedHosts and "network.fetch" not in capabilities:
        findings.append({"level": "review", "code": "unused-host-allowlist", "message": "Allowed hosts were supplied without network.fetch capability."})
    invalid_hosts = [host for host in payload.allowedHosts if not re.fullmatch(r"[A-Za-z0-9.-]+", host or "")]
    if invalid_hosts:
        findings.append({"level": "block", "code": "invalid-allowed-host", "message": ", ".join(invalid_hosts)})
    high_risk = payload.highRisk or bool(set(capabilities) & HIGH_RISK_CAPABILITIES)
    if high_risk:
        findings.append({"level": "review", "code": "security-review-required", "message": "Requested capabilities require explicit security and governance review."})
    if not payload.packageHash:
        findings.append({"level": "review", "code": "package-hash-missing", "message": "Attach a SHA-256 package hash before installation review."})
    if not payload.signature or not payload.publicKeyId:
        findings.append({"level": "review", "code": "signature-metadata-missing", "message": "Signed distribution requires a signature and public key identifier."})

    record = {
        "schema": "sc-workbench-extension-manifest/1.0",
        "frameworkVersion": VERSION,
        "extensionId": slug(payload.extensionId or f"{payload.publisher}-{payload.name}"),
        "name": payload.name.strip(),
        "version": payload.version.strip(),
        "publisher": payload.publisher.strip(),
        "description": payload.description.strip(),
        "entrypoint": payload.entrypoint.strip(),
        "coreCompatibility": {"minimum": payload.minimumCoreVersion, "maximum": payload.maximumCoreVersion},
        "capabilities": capabilities,
        "hooks": hooks,
        "permissions": permissions,
        "dependencies": dict(sorted(payload.dependencies.items())),
        "allowedHosts": sorted(set(payload.allowedHosts)),
        "packageHash": payload.packageHash,
        "signature": payload.signature,
        "publicKeyId": payload.publicKeyId,
        "license": payload.license,
        "repository": payload.repository,
        "highRisk": high_risk,
        "findings": findings,
        "readyForCompatibilityReview": not any(item["level"] == "block" for item in findings),
        "automaticExtensionInstallationAuthorized": False,
        "automaticExtensionActivationAuthorized": False,
        "automaticPrivilegeEscalationAuthorized": False,
        "arbitraryCodeExecutionAuthorized": False,
    }
    record["manifestHash"] = content_hash({k: v for k, v in record.items() if k != "manifestHash"})
    return record


def evaluate_compatibility(payload: CompatibilityInput) -> Dict[str, Any]:
    manifest = payload.manifest
    blockers: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    compatibility = manifest.get("coreCompatibility", {})
    minimum = compatibility.get("minimum", "4.5.0")
    maximum = compatibility.get("maximum", "")
    try:
        core_compatible = version_in_range(payload.coreVersion, minimum, maximum)
    except ValueError as exc:
        core_compatible = False
        blockers.append({"code": "invalid-version-range", "message": str(exc)})
    if not core_compatible:
        blockers.append({"code": "core-version-incompatible", "message": f"Core {payload.coreVersion} is outside {minimum}..{maximum or 'unbounded'}."})
    available = set(payload.availableCapabilities)
    missing_capabilities = sorted(set(manifest.get("capabilities", [])) - available)
    for capability in missing_capabilities:
        blockers.append({"code": "capability-unavailable", "message": capability})
    dependency_results: List[Dict[str, Any]] = []
    for extension_id, minimum_version in sorted(manifest.get("dependencies", {}).items()):
        installed = payload.installedExtensions.get(extension_id, "")
        satisfied = False
        if installed:
            try:
                satisfied = parse_version(installed) >= parse_version(minimum_version)
            except ValueError:
                satisfied = False
        dependency_results.append({"extensionId": extension_id, "minimumVersion": minimum_version, "installedVersion": installed, "satisfied": satisfied})
        if not satisfied:
            blockers.append({"code": "dependency-unsatisfied", "message": f"{extension_id}>={minimum_version}"})
    if manifest.get("highRisk"):
        warnings.append({"code": "high-risk-review", "message": "Compatibility does not replace security approval."})
    result = {
        "schema": "sc-workbench-extension-compatibility/1.0",
        "version": VERSION,
        "extensionId": manifest.get("extensionId", "extension"),
        "extensionVersion": manifest.get("version", ""),
        "coreVersion": payload.coreVersion,
        "coreCompatible": core_compatible,
        "missingCapabilities": missing_capabilities,
        "dependencies": dependency_results,
        "blockers": blockers,
        "warnings": warnings,
        "compatible": not blockers,
        "humanReviewRequired": True,
        "automaticExtensionInstallationAuthorized": False,
    }
    result["compatibilityHash"] = content_hash({k: v for k, v in result.items() if k != "compatibilityHash"})
    return result


def build_registry_entry(payload: RegistryEntryInput) -> Dict[str, Any]:
    blockers: List[Dict[str, str]] = []
    manifest = payload.manifest
    if payload.state == "approved":
        if not payload.compatibility.get("compatible", False):
            blockers.append({"code": "compatibility-required", "message": "Approved registry entries require a passing compatibility report."})
        if not payload.integrityVerified:
            blockers.append({"code": "integrity-verification-required", "message": "Approved registry entries require package integrity verification."})
        if payload.trustTier in {"verified", "first-party"} and not payload.signatureVerified:
            blockers.append({"code": "signature-verification-required", "message": "Verified trust tiers require signature verification."})
        if not payload.reviewer.strip():
            blockers.append({"code": "reviewer-required", "message": "Record a human reviewer before approval."})
    effective_state = "blocked" if blockers else payload.state
    result = {
        "schema": "sc-workbench-extension-registry-entry/1.0",
        "version": VERSION,
        "extensionId": manifest.get("extensionId", "extension"),
        "extensionVersion": manifest.get("version", ""),
        "manifestHash": manifest.get("manifestHash", content_hash(manifest)),
        "state": effective_state,
        "requestedState": payload.state,
        "trustTier": payload.trustTier,
        "reviewer": payload.reviewer,
        "reviewNotes": payload.reviewNotes,
        "integrityVerified": payload.integrityVerified,
        "signatureVerified": payload.signatureVerified,
        "compatibilityHash": payload.compatibility.get("compatibilityHash", ""),
        "blockers": blockers,
        "privateByDefault": True,
        "automaticRegistryPublicationAuthorized": False,
        "automaticExtensionActivationAuthorized": False,
    }
    result["registryHash"] = content_hash({k: v for k, v in result.items() if k != "registryHash"})
    return result


def audit_permissions(payload: PermissionAuditInput) -> Dict[str, Any]:
    capabilities = sorted(set(payload.capabilities))
    blockers: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    forbidden = sorted(set(capabilities) & FORBIDDEN_CAPABILITIES)
    unknown = sorted(set(capabilities) - ALLOWED_CAPABILITIES - FORBIDDEN_CAPABILITIES)
    high_risk = sorted(set(capabilities) & HIGH_RISK_CAPABILITIES)
    if forbidden:
        blockers.append({"code": "forbidden-capabilities", "message": ", ".join(forbidden)})
    if unknown:
        blockers.append({"code": "unknown-capabilities", "message": ", ".join(unknown)})
    if "network.fetch" in capabilities and not payload.allowedHosts:
        blockers.append({"code": "network-host-allowlist-required", "message": "network.fetch requires one or more explicit hostnames."})
    if high_risk and not payload.explicitApproval:
        blockers.append({"code": "explicit-approval-required", "message": ", ".join(high_risk)})
    if not payload.dataScopes and set(capabilities) & {"project.write", "record.write", "dataset.write", "evidence.write"}:
        warnings.append({"code": "data-scope-missing", "message": "Write capabilities should be limited to named project or record scopes."})
    result = {
        "schema": "sc-workbench-extension-permission-audit/1.0",
        "version": VERSION,
        "capabilities": capabilities,
        "allowedHosts": sorted(set(payload.allowedHosts)),
        "dataScopes": sorted(set(payload.dataScopes)),
        "highRiskCapabilities": high_risk,
        "blockers": blockers,
        "warnings": warnings,
        "ready": not blockers,
        "leastPrivilegeRequired": True,
        "automaticPrivilegeEscalationAuthorized": False,
        "arbitraryCodeExecutionAuthorized": False,
    }
    result["auditHash"] = content_hash({k: v for k, v in result.items() if k != "auditHash"})
    return result


def build_hook_contract(payload: HookContractInput) -> Dict[str, Any]:
    blockers: List[Dict[str, str]] = []
    if payload.hook not in ALLOWED_HOOKS:
        blockers.append({"code": "hook-not-allowed", "message": payload.hook})
    forbidden = sorted(set(payload.capabilityScopes) & FORBIDDEN_CAPABILITIES)
    if forbidden:
        blockers.append({"code": "forbidden-hook-capability", "message": ", ".join(forbidden)})
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_.$:-]*", payload.handler or ""):
        blockers.append({"code": "invalid-handler-name", "message": "Handler must be a symbolic function or service identifier."})
    core = {
        "extensionId": slug(payload.extensionId), "hook": payload.hook, "handler": payload.handler,
        "inputSchema": payload.inputSchema, "outputSchema": payload.outputSchema,
        "timeoutMs": payload.timeoutMs, "idempotent": payload.idempotent,
        "retryLimit": payload.retryLimit, "capabilityScopes": sorted(set(payload.capabilityScopes)),
    }
    result = {
        "schema": "sc-workbench-extension-hook-contract/1.0",
        "version": VERSION,
        **core,
        "hookId": "hook-" + content_hash(core)[:16],
        "blockers": blockers,
        "ready": not blockers,
        "isolatedExecutionRequired": True,
        "automaticHookExecutionAuthorized": False,
        "arbitraryCodeExecutionAuthorized": False,
    }
    result["contractHash"] = content_hash({k: v for k, v in result.items() if k != "contractHash"})
    return result


def build_lifecycle_plan(payload: LifecyclePlanInput) -> Dict[str, Any]:
    blockers: List[Dict[str, str]] = []
    manifest = payload.manifest
    destructive = payload.action in {"update", "uninstall"}
    if not payload.compatibility.get("compatible", False) and payload.action in {"install", "activate", "update"}:
        blockers.append({"code": "compatibility-required", "message": "A passing compatibility report is required."})
    if payload.action in {"install", "update"} and not payload.integrityVerified:
        blockers.append({"code": "integrity-required", "message": "Verify the package hash before installation or update."})
    if manifest.get("signature") and payload.action in {"install", "update"} and not payload.signatureVerified:
        blockers.append({"code": "signature-required", "message": "Verify the extension signature."})
    if destructive and not payload.backupVerified:
        blockers.append({"code": "backup-required", "message": "A verified backup is required before update or uninstall."})
    if not payload.explicitApproval:
        blockers.append({"code": "explicit-approval-required", "message": "A human operator must approve lifecycle changes."})
    required_phrase = "UNINSTALL WORKBENCH EXTENSION" if payload.action == "uninstall" else ""
    if required_phrase and payload.confirmationPhrase != required_phrase:
        blockers.append({"code": "confirmation-required", "message": required_phrase})
    steps = ["validate-manifest", "check-compatibility", "audit-permissions", "verify-integrity"]
    if manifest.get("signature"):
        steps.append("verify-signature")
    if destructive:
        steps.append("verify-backup")
    steps.extend([f"prepare-{payload.action}", "human-review", f"execute-{payload.action}-externally", "verify-result", "write-receipt"])
    result = {
        "schema": "sc-workbench-extension-lifecycle-plan/1.0",
        "version": VERSION,
        "action": payload.action,
        "extensionId": manifest.get("extensionId", "extension"),
        "extensionVersion": manifest.get("version", ""),
        "installedVersion": payload.installedVersion,
        "steps": steps,
        "blockers": blockers,
        "ready": not blockers,
        "requiredConfirmationPhrase": required_phrase,
        "automaticExtensionInstallationAuthorized": False,
        "automaticExtensionActivationAuthorized": False,
        "automaticExtensionDeletionAuthorized": False,
        "automaticDataDeletionAuthorized": False,
    }
    result["planHash"] = content_hash({k: v for k, v in result.items() if k != "planHash"})
    return result


def build_sdk_scaffold(payload: SDKScaffoldInput) -> Dict[str, Any]:
    extension_id = slug(payload.extensionId or f"{payload.publisher}-{payload.name}")
    extension_extension = {"javascript": "js", "typescript": "ts", "python": "py"}[payload.language]
    files = [f"{extension_id}/extension.json", f"{extension_id}/src/extension.{extension_extension}"]
    if payload.includeTests:
        files.append(f"{extension_id}/tests/test_extension.{extension_extension}")
    if payload.includeDocumentation:
        files.extend([f"{extension_id}/README.md", f"{extension_id}/SECURITY.md"])
    manifest = normalize_manifest(ExtensionManifestInput(
        extensionId=extension_id, name=payload.name, version="0.1.0", publisher=payload.publisher,
        capabilities=payload.capabilities, hooks=payload.hooks,
    ))
    result = {
        "schema": "sc-workbench-extension-sdk-scaffold/1.0",
        "version": VERSION,
        "extensionId": extension_id,
        "language": payload.language,
        "files": files,
        "manifest": manifest,
        "commands": ["validate-manifest", "run-tests", "build-package", "audit-package"],
        "testRequirements": ["manifest-schema", "capability-scope", "hook-contract", "compatibility", "security-boundary"],
        "requiresDeveloperReview": True,
        "automaticCodeExecutionAuthorized": False,
        "automaticPublicationAuthorized": False,
    }
    result["scaffoldHash"] = content_hash({k: v for k, v in result.items() if k != "scaffoldHash"})
    return result


def audit_extension(payload: ExtensionAuditInput) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    manifest = payload.manifest
    capability_audit = audit_permissions(PermissionAuditInput(
        capabilities=manifest.get("capabilities", []), allowedHosts=manifest.get("allowedHosts", []),
        dataScopes=manifest.get("permissions", []), explicitApproval=False,
    ))
    for item in capability_audit["blockers"]:
        findings.append({"level": "block", "code": item["code"], "message": item["message"]})
    source = payload.sourceText
    patterns = {
        "dynamic-code-evaluation": r"\b(eval|exec)\s*\(",
        "shell-process-use": r"\b(subprocess|child_process|os\.system|popen|spawn)\b",
        "credential-pattern": r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}",
        "unrestricted-file-access": r"(/etc/|~/.ssh|\.\.\/\.\.)",
    }
    for code, pattern in patterns.items():
        if re.search(pattern, source, re.IGNORECASE):
            findings.append({"level": "block", "code": code, "message": "Source review identified a restricted pattern."})
    if not payload.integrityVerified:
        findings.append({"level": "block", "code": "integrity-not-verified", "message": "Package integrity has not been verified."})
    if manifest.get("signature") and not payload.signatureVerified:
        findings.append({"level": "block", "code": "signature-not-verified", "message": "The declared package signature has not been verified."})
    result = {
        "schema": "sc-workbench-extension-security-audit/1.0",
        "version": VERSION,
        "extensionId": manifest.get("extensionId", "extension"),
        "sourceFiles": sorted(set(payload.sourceFiles)),
        "findings": findings,
        "ready": not any(item["level"] == "block" for item in findings),
        "humanSecurityReviewRequired": True,
        "sandboxRequired": True,
        "arbitraryCodeExecutionAuthorized": False,
        "remoteShellAuthorized": False,
        "automaticExtensionActivationAuthorized": False,
    }
    result["auditHash"] = content_hash({k: v for k, v in result.items() if k != "auditHash"})
    return result


def build_extension_package(payload: ExtensionPackageInput) -> Dict[str, Any]:
    file_hashes = {name: hashlib.sha256(content.encode("utf-8")).hexdigest() for name, content in sorted(payload.files.items())}
    components = {
        "manifest": payload.manifest,
        "files": payload.files,
        "documentation": payload.documentation,
        "tests": payload.tests,
        "audit": payload.audit,
        "compatibility": payload.compatibility,
    }
    blockers: List[Dict[str, str]] = []
    if not payload.compatibility.get("compatible", False):
        blockers.append({"code": "compatibility-required", "message": "A passing compatibility report is required."})
    if not payload.audit.get("ready", False):
        blockers.append({"code": "security-audit-required", "message": "A passing extension security audit is required."})
    if not payload.files:
        blockers.append({"code": "extension-files-required", "message": "Package at least one extension source file."})
    result = {
        "schema": "sc-workbench-extension-package/1.0",
        "version": VERSION,
        "createdAt": utc_now(),
        "extensionId": payload.manifest.get("extensionId", "extension"),
        "extensionVersion": payload.manifest.get("version", ""),
        "components": components,
        "fileHashes": file_hashes,
        "componentHashes": {name: content_hash(value) for name, value in components.items()},
        "signature": payload.signature,
        "blockers": blockers,
        "ready": not blockers,
        "portable": True,
        "privateByDefault": True,
        "requiresExplicitImport": True,
        "requiresHumanReview": True,
        "automaticExtensionInstallationAuthorized": False,
        "automaticExtensionActivationAuthorized": False,
        "automaticRegistryPublicationAuthorized": False,
    }
    result["packageHash"] = content_hash({k: v for k, v in result.items() if k not in {"packageHash", "createdAt"}})
    return result


@router.get("/status")
def route_status() -> Dict[str, Any]:
    return status_record()


@router.post("/manifest/normalize")
def route_manifest(payload: ExtensionManifestInput) -> Dict[str, Any]:
    return normalize_manifest(payload)


@router.post("/compatibility/evaluate")
def route_compatibility(payload: CompatibilityInput) -> Dict[str, Any]:
    return evaluate_compatibility(payload)


@router.post("/registry/entry")
def route_registry(payload: RegistryEntryInput) -> Dict[str, Any]:
    return build_registry_entry(payload)


@router.post("/permissions/audit")
def route_permissions(payload: PermissionAuditInput) -> Dict[str, Any]:
    return audit_permissions(payload)


@router.post("/hooks/contract")
def route_hooks(payload: HookContractInput) -> Dict[str, Any]:
    return build_hook_contract(payload)


@router.post("/lifecycle/plan")
def route_lifecycle(payload: LifecyclePlanInput) -> Dict[str, Any]:
    return build_lifecycle_plan(payload)


@router.post("/sdk/scaffold")
def route_scaffold(payload: SDKScaffoldInput) -> Dict[str, Any]:
    return build_sdk_scaffold(payload)


@router.post("/security/audit")
def route_audit(payload: ExtensionAuditInput) -> Dict[str, Any]:
    return audit_extension(payload)


@router.post("/package/build")
def route_package(payload: ExtensionPackageInput) -> Dict[str, Any]:
    return build_extension_package(payload)

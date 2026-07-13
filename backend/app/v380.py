"""Workbench v3.8.0 — Offline and Installable Workbench."""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v380", tags=["Workbench v3.8.0"])
VERSION = "3.8.0"
SCHEMA_PREFIX = "sc-workbench-offline"
SUPPORTED_PLATFORMS = {
    "macos": {
        "label": "macOS",
        "architectures": ["arm64", "x86_64"],
        "installRoot": "~/Library/Application Support/Sustainable Catalyst Workbench",
        "launcher": "~/Applications/Sustainable Catalyst Workbench.command",
    },
    "linux": {
        "label": "Linux",
        "architectures": ["x86_64", "aarch64"],
        "installRoot": "~/.local/share/sustainable-catalyst-workbench",
        "launcher": "~/.local/share/applications/sustainable-catalyst-workbench.desktop",
    },
    "raspberry-pi": {
        "label": "Raspberry Pi OS",
        "architectures": ["aarch64", "armv7l"],
        "installRoot": "~/.local/share/sustainable-catalyst-workbench",
        "launcher": "~/.local/share/applications/sustainable-catalyst-workbench.desktop",
    },
}
CORE_COMPONENTS = [
    "local-fastapi-service",
    "offline-web-app",
    "browser-project-store",
    "backup-and-restore",
    "sync-bundle-tools",
    "documentation",
]
OPTIONAL_COMPONENTS = [
    "go-runner",
    "python-runtime",
    "r-runtime",
    "javascript-runtime",
    "rust-runtime",
    "example-projects",
]
ALLOWED_CHANNELS = {"stable", "preview", "manual"}
ALLOWED_CONFLICT_STRATEGIES = {"manual", "keep-local", "keep-incoming", "rename-incoming"}


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def normalize_version(value: str) -> tuple[int, ...]:
    match = re.findall(r"\d+", value or "")
    return tuple(int(part) for part in match[:3]) if match else (0,)


class InstallPlanRequest(BaseModel):
    platform: Literal["macos", "linux", "raspberry-pi"]
    architecture: str
    install_root: Optional[str] = None
    python_version: str = "3.12"
    components: List[str] = Field(default_factory=lambda: CORE_COMPONENTS + ["go-runner"])
    create_launcher: bool = True
    use_wheelhouse: bool = False


class RuntimeAuditRequest(BaseModel):
    platform: Literal["macos", "linux", "raspberry-pi"]
    architecture: str
    python_version: str
    disk_free_mb: int = 0
    memory_mb: int = 0
    writable_paths: List[str] = Field(default_factory=list)
    available_commands: List[str] = Field(default_factory=list)
    loopback_available: bool = True


class DependencyPlanRequest(BaseModel):
    platform: Literal["macos", "linux", "raspberry-pi"]
    requested_languages: List[str] = Field(default_factory=lambda: ["python", "javascript", "go"])
    available_commands: List[str] = Field(default_factory=list)
    wheelhouse_available: bool = False


class OfflinePackageRequest(BaseModel):
    package_name: str = "sustainable-catalyst-workbench"
    version: str = VERSION
    platforms: List[str] = Field(default_factory=lambda: list(SUPPORTED_PLATFORMS))
    components: List[str] = Field(default_factory=lambda: CORE_COMPONENTS + ["go-runner"])
    include_examples: bool = True
    files: List[Dict[str, Any]] = Field(default_factory=list)


class SyncExportRequest(BaseModel):
    project_id: str
    source_node: str = "browser-local"
    target: str = "portable"
    records: List[Dict[str, Any]] = Field(default_factory=list)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)


class SyncImportPlanRequest(BaseModel):
    bundle: Dict[str, Any]
    existing_record_hashes: Dict[str, str] = Field(default_factory=dict)
    conflict_strategy: str = "manual"
    create_backup: bool = True


class UpdatePlanRequest(BaseModel):
    current_version: str
    target_version: str
    channel: str = "stable"
    package_hash: str = ""
    backup_available: bool = False
    service_running: bool = False


class RecoveryPlanRequest(BaseModel):
    issue: str
    service_state: str = "stopped"
    latest_backup: Optional[str] = None
    database_integrity: str = "unknown"
    package_integrity: str = "unknown"


def build_install_plan(request: InstallPlanRequest) -> Dict[str, Any]:
    platform = SUPPORTED_PLATFORMS[request.platform]
    architecture = request.architecture.strip().lower()
    supported = architecture in platform["architectures"]
    components = list(dict.fromkeys(request.components))
    unknown = [item for item in components if item not in CORE_COMPONENTS + OPTIONAL_COMPONENTS]
    install_root = request.install_root or platform["installRoot"]
    steps = [
        "Verify package checksum before installation.",
        "Create a versioned backup of any existing local Workbench installation.",
        f"Install Workbench files under {install_root}.",
        "Create an isolated Python virtual environment.",
        "Install FastAPI, Pydantic, and Uvicorn from the bundled wheelhouse when available.",
        "Bind the local service to 127.0.0.1 only.",
        "Initialize browser-local and file-based project storage.",
    ]
    if "go-runner" in components:
        steps.append("Install or link the local Go runner without enabling remote command execution.")
    if request.create_launcher:
        steps.append(f"Create the local launcher at {platform['launcher']}.")
    steps.extend([
        "Run the local health and storage-integrity checks.",
        "Keep cloud synchronization disabled until explicitly configured.",
    ])
    plan = {
        "schema": f"{SCHEMA_PREFIX}-install-plan/1.0",
        "version": VERSION,
        "platform": request.platform,
        "platformLabel": platform["label"],
        "architecture": architecture,
        "architectureSupported": supported,
        "installRoot": install_root,
        "launcher": platform["launcher"] if request.create_launcher else None,
        "pythonVersion": request.python_version,
        "components": components,
        "unknownComponents": unknown,
        "wheelhouseMode": "offline" if request.use_wheelhouse else "online-or-prebuilt",
        "steps": steps,
        "loopbackOnly": True,
        "paidServiceRequired": False,
        "renderRequired": False,
        "humanReviewRequired": bool(unknown or not supported),
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": supported and not unknown, "plan": plan}


def audit_runtime(request: RuntimeAuditRequest) -> Dict[str, Any]:
    commands = {item.strip().lower() for item in request.available_commands}
    python_ok = normalize_version(request.python_version) >= (3, 11)
    disk_ok = request.disk_free_mb >= 2048
    memory_minimum = 2048 if request.platform == "raspberry-pi" else 4096
    memory_ok = request.memory_mb >= memory_minimum
    writable_ok = bool(request.writable_paths)
    required_commands = {"python3"}
    recommended_commands = {"git", "node", "go"}
    missing_required = sorted(required_commands - commands)
    missing_recommended = sorted(recommended_commands - commands)
    checks = {
        "pythonVersion": {"ok": python_ok, "observed": request.python_version, "minimum": "3.11"},
        "disk": {"ok": disk_ok, "observedMB": request.disk_free_mb, "minimumMB": 2048},
        "memory": {"ok": memory_ok, "observedMB": request.memory_mb, "minimumMB": memory_minimum},
        "writableStorage": {"ok": writable_ok, "paths": request.writable_paths},
        "loopback": {"ok": request.loopback_available, "required": True},
        "requiredCommands": {"ok": not missing_required, "missing": missing_required},
        "recommendedCommands": {"ok": not missing_recommended, "missing": missing_recommended},
    }
    blocking = [name for name, check in checks.items() if name != "recommendedCommands" and not check["ok"]]
    audit = {
        "schema": f"{SCHEMA_PREFIX}-runtime-audit/1.0",
        "version": VERSION,
        "platform": request.platform,
        "architecture": request.architecture,
        "checks": checks,
        "blockingChecks": blocking,
        "warnings": [f"Recommended command unavailable: {item}" for item in missing_recommended],
        "ready": not blocking,
        "cloudDependency": False,
    }
    audit["auditHash"] = stable_hash(audit)
    return {"ok": audit["ready"], "audit": audit}


def build_dependency_plan(request: DependencyPlanRequest) -> Dict[str, Any]:
    available = {item.strip().lower() for item in request.available_commands}
    mapping = {
        "python": {"command": "python3", "required": True},
        "javascript": {"command": "node", "required": False},
        "go": {"command": "go", "required": False},
        "r": {"command": "rscript", "required": False},
        "rust": {"command": "cargo", "required": False},
    }
    requested = list(dict.fromkeys(item.strip().lower() for item in request.requested_languages))
    unsupported = [item for item in requested if item not in mapping]
    runtimes = []
    for language in requested:
        if language not in mapping:
            continue
        spec = mapping[language]
        runtimes.append({
            "language": language,
            "command": spec["command"],
            "available": spec["command"] in available,
            "required": spec["required"],
            "installationMode": "system-runtime",
        })
    missing_required = [item["language"] for item in runtimes if item["required"] and not item["available"]]
    plan = {
        "schema": f"{SCHEMA_PREFIX}-dependency-plan/1.0",
        "version": VERSION,
        "platform": request.platform,
        "wheelhouseAvailable": request.wheelhouse_available,
        "pythonPackages": ["fastapi", "pydantic", "uvicorn"],
        "runtimes": runtimes,
        "unsupportedLanguages": unsupported,
        "missingRequired": missing_required,
        "offlineInstallReady": request.wheelhouse_available and not missing_required and not unsupported,
        "arbitraryPackageExecution": False,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": not missing_required and not unsupported, "plan": plan}


def build_offline_package(request: OfflinePackageRequest) -> Dict[str, Any]:
    unsupported_platforms = [item for item in request.platforms if item not in SUPPORTED_PLATFORMS]
    unknown_components = [item for item in request.components if item not in CORE_COMPONENTS + OPTIONAL_COMPONENTS]
    files = []
    for entry in request.files:
        path = str(entry.get("path", "")).strip()
        if not path:
            continue
        files.append({
            "path": path,
            "size": int(entry.get("size", 0) or 0),
            "sha256": str(entry.get("sha256", "")),
            "required": bool(entry.get("required", True)),
        })
    manifest = {
        "schema": f"{SCHEMA_PREFIX}-package-manifest/1.0",
        "package": request.package_name,
        "version": request.version,
        "platforms": request.platforms,
        "components": list(dict.fromkeys(request.components)),
        "includeExamples": request.include_examples,
        "files": files,
        "fileCount": len(files),
        "unsupportedPlatforms": unsupported_platforms,
        "unknownComponents": unknown_components,
        "installers": {
            "macos": "installers/macos/install_workbench_macos.command",
            "linux": "installers/linux/install_workbench_linux.sh",
            "raspberry-pi": "installers/raspberry-pi/install_workbench_raspberry_pi.sh",
        },
        "loopbackOnly": True,
        "signatureRequiredBeforeAutomaticUpdate": True,
    }
    manifest["manifestHash"] = stable_hash(manifest)
    return {"ok": not unsupported_platforms and not unknown_components, "manifest": manifest}


def build_sync_export(request: SyncExportRequest) -> Dict[str, Any]:
    if not request.project_id.strip():
        raise ValueError("project_id is required")
    records = []
    for index, record in enumerate(request.records):
        record_hash = stable_hash(record)
        records.append({
            "recordId": str(record.get("id") or record.get("recordId") or f"record-{index + 1}"),
            "recordHash": record_hash,
            "record": record,
        })
    attachments = []
    for index, attachment in enumerate(request.attachments):
        attachments.append({
            "attachmentId": str(attachment.get("id") or f"attachment-{index + 1}"),
            "name": str(attachment.get("name") or f"attachment-{index + 1}"),
            "sha256": str(attachment.get("sha256") or stable_hash(attachment)),
            "size": int(attachment.get("size", 0) or 0),
        })
    bundle = {
        "schema": f"{SCHEMA_PREFIX}-sync-bundle/1.0",
        "version": VERSION,
        "projectId": request.project_id,
        "sourceNode": request.source_node,
        "target": request.target,
        "records": records,
        "attachments": attachments,
        "recordCount": len(records),
        "attachmentCount": len(attachments),
        "requiresExplicitImport": True,
        "automaticCloudUpload": False,
    }
    bundle["bundleHash"] = stable_hash(bundle)
    return {"ok": True, "bundle": bundle}


def plan_sync_import(request: SyncImportPlanRequest) -> Dict[str, Any]:
    if request.conflict_strategy not in ALLOWED_CONFLICT_STRATEGIES:
        raise ValueError("unsupported conflict strategy")
    bundle = request.bundle
    supplied_hash = str(bundle.get("bundleHash", ""))
    unsigned = dict(bundle)
    unsigned.pop("bundleHash", None)
    calculated_hash = stable_hash(unsigned)
    integrity_ok = bool(supplied_hash) and supplied_hash == calculated_hash
    conflicts = []
    imports = []
    for item in bundle.get("records", []):
        record_id = str(item.get("recordId", ""))
        incoming_hash = str(item.get("recordHash", ""))
        current_hash = request.existing_record_hashes.get(record_id)
        if current_hash and current_hash != incoming_hash:
            conflicts.append({"recordId": record_id, "existingHash": current_hash, "incomingHash": incoming_hash})
        else:
            imports.append(record_id)
    action = "import"
    if not integrity_ok:
        action = "reject-integrity-failure"
    elif conflicts and request.conflict_strategy == "manual":
        action = "hold-for-review"
    elif conflicts:
        action = request.conflict_strategy
    plan = {
        "schema": f"{SCHEMA_PREFIX}-sync-import-plan/1.0",
        "version": VERSION,
        "integrityValid": integrity_ok,
        "conflictStrategy": request.conflict_strategy,
        "conflicts": conflicts,
        "importableRecordIds": imports,
        "backupRequired": request.create_backup or bool(conflicts),
        "action": action,
        "destructiveOverwrite": request.conflict_strategy == "keep-incoming" and bool(conflicts),
        "humanReviewRequired": bool(conflicts) or not integrity_ok,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": integrity_ok and action != "hold-for-review", "plan": plan}


def build_update_plan(request: UpdatePlanRequest) -> Dict[str, Any]:
    if request.channel not in ALLOWED_CHANNELS:
        raise ValueError("unsupported update channel")
    current = normalize_version(request.current_version)
    target = normalize_version(request.target_version)
    downgrade = target < current
    same = target == current
    blocking = []
    if not request.package_hash:
        blocking.append("missing-package-hash")
    if not request.backup_available and not same:
        blocking.append("backup-required")
    if downgrade:
        blocking.append("downgrade-requires-manual-review")
    actions = [
        "Verify the package hash against a trusted release manifest.",
        "Stop the loopback service before replacing application files.",
        "Create or verify a restorable project and configuration backup.",
        "Install into a versioned directory rather than overwriting the active copy.",
        "Run health, storage, and migration checks.",
        "Switch the active launcher only after validation passes.",
    ]
    if request.service_running:
        actions.insert(1, "Request a graceful local-service shutdown.")
    plan = {
        "schema": f"{SCHEMA_PREFIX}-update-plan/1.0",
        "version": VERSION,
        "currentVersion": request.current_version,
        "targetVersion": request.target_version,
        "channel": request.channel,
        "sameVersion": same,
        "downgrade": downgrade,
        "blockingIssues": blocking,
        "actions": actions,
        "automaticUpdateAuthorized": False,
        "rollbackPointRequired": not same,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": not blocking, "plan": plan}


def build_recovery_plan(request: RecoveryPlanRequest) -> Dict[str, Any]:
    issue = request.issue.strip().lower()
    steps = ["Keep the local service stopped while integrity is uncertain."]
    if request.latest_backup:
        steps.append(f"Preserve and verify backup {request.latest_backup} before making changes.")
    else:
        steps.append("Create a read-only copy of the current project store before repair.")
    if request.database_integrity != "valid":
        steps.extend(["Run the storage-integrity audit.", "Quarantine malformed records rather than deleting them."])
    if request.package_integrity != "valid":
        steps.extend(["Verify the installed package manifest.", "Reinstall application files without overwriting project data."])
    if "port" in issue or "service" in issue:
        steps.append("Check whether the configured loopback port is already in use.")
    if "sync" in issue or "conflict" in issue:
        steps.append("Restore the pre-import backup or hold conflicting records for manual review.")
    steps.extend([
        "Start the service on 127.0.0.1 and run the health endpoint.",
        "Validate one project before restoring normal access.",
    ])
    plan = {
        "schema": f"{SCHEMA_PREFIX}-recovery-plan/1.0",
        "version": VERSION,
        "issue": request.issue,
        "serviceState": request.service_state,
        "latestBackup": request.latest_backup,
        "databaseIntegrity": request.database_integrity,
        "packageIntegrity": request.package_integrity,
        "steps": steps,
        "automaticDeletion": False,
        "humanReviewRequired": True,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": True, "plan": plan}


@router.get("/status")
def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": f"{SCHEMA_PREFIX}-status/1.0",
        "version": VERSION,
        "platforms": SUPPORTED_PLATFORMS,
        "coreComponents": CORE_COMPONENTS,
        "optionalComponents": OPTIONAL_COMPONENTS,
        "localServiceHost": "127.0.0.1",
        "defaultPort": 8787,
        "renderRequired": False,
        "paidServiceRequired": False,
        "remoteShell": False,
        "automaticCloudUpload": False,
    }


@router.post("/install/plan")
def install_plan_endpoint(request: InstallPlanRequest) -> Dict[str, Any]:
    return build_install_plan(request)


@router.post("/runtime/audit")
def runtime_audit_endpoint(request: RuntimeAuditRequest) -> Dict[str, Any]:
    return audit_runtime(request)


@router.post("/dependency/plan")
def dependency_plan_endpoint(request: DependencyPlanRequest) -> Dict[str, Any]:
    return build_dependency_plan(request)


@router.post("/package/build")
def package_build_endpoint(request: OfflinePackageRequest) -> Dict[str, Any]:
    return build_offline_package(request)


@router.post("/sync/export")
def sync_export_endpoint(request: SyncExportRequest) -> Dict[str, Any]:
    try:
        return build_sync_export(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sync/import/plan")
def sync_import_endpoint(request: SyncImportPlanRequest) -> Dict[str, Any]:
    try:
        return plan_sync_import(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/update/plan")
def update_plan_endpoint(request: UpdatePlanRequest) -> Dict[str, Any]:
    try:
        return build_update_plan(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/recovery/plan")
def recovery_plan_endpoint(request: RecoveryPlanRequest) -> Dict[str, Any]:
    return build_recovery_plan(request)

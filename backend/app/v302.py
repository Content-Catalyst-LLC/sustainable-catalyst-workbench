"""Workbench v3.0.2 project migration, storage, and recovery routes."""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field, model_validator

VERSION = "3.0.2"
MIGRATION_SCHEMA = "sc-workbench-migration-plan/2.0"
BACKUP_SCHEMA = "sc-workbench-backup/2.0"
RESTORE_SCHEMA = "sc-workbench-restore-plan/2.0"
STORAGE_SCHEMA = "sc-workbench-storage-health/2.0"
CLEANUP_SCHEMA = "sc-workbench-cleanup-plan/2.0"
CANONICAL_PREFIX = "scwb:v3"
router = APIRouter(prefix="/v302", tags=["workbench-v302"])

LEGACY_PREFIXES: tuple[tuple[str, str], ...] = (
    ("scwb-v200", "research"),
    ("scwb-v210", "embedded"),
    ("scwb-v220", "electronics"),
    ("scwb-v230", "robotics"),
    ("scwb-v240", "instrumentation"),
    ("scwb-v250", "simulation"),
    ("scwb-v260", "runtime"),
    ("scwb-v270", "visualization"),
    ("scwb-v280", "experiments"),
    ("scwb-v290", "documentation"),
    ("scwb-v300", "unified"),
    ("scwb-v301", "unified"),
    ("sc-workbench", "legacy"),
    ("sustainable-catalyst-workbench", "legacy"),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip("-").lower()
    return value[:160] or "record"


def classify_legacy_key(key: str) -> tuple[str, str]:
    lower = key.lower()
    if lower.startswith(f"{CANONICAL_PREFIX}:"):
        parts = key.split(":")
        studio = parts[3] if len(parts) > 3 else "unified"
        return "canonical", studio
    for prefix, studio in LEGACY_PREFIXES:
        if lower.startswith(prefix):
            return prefix, studio
    return "unknown", "other"


class StorageRecord(BaseModel):
    key: str = Field(min_length=1, max_length=1000)
    value: Any = None
    size_bytes: int = Field(default=0, ge=0, le=2_000_000_000)
    content_hash: str = Field(default="", max_length=128)
    updated_at: str = Field(default="", max_length=120)
    protected: bool = False
    dependencies: list[str] = Field(default_factory=list, max_length=10000)
    category: str = Field(default="other", max_length=100)


class MigrationPreviewRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    source_version: str = Field(default="unknown", max_length=120)
    records: list[StorageRecord] = Field(default_factory=list, max_length=50000)
    preserve_unknown: bool = True


class StorageAuditRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    records: list[StorageRecord] = Field(default_factory=list, max_length=50000)
    quota_bytes: int = Field(default=5_242_880, ge=1, le=10_000_000_000)
    stale_after_days: int = Field(default=180, ge=1, le=36500)


class BackupBuildRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    revision: str = Field(default=VERSION, max_length=120)
    label: str = Field(default="Workbench recovery backup", max_length=300)
    records: list[StorageRecord] = Field(default_factory=list, max_length=50000)
    previous_backup_hash: str = Field(default="", max_length=128)


class BackupEnvelope(BaseModel):
    schema_name: str = Field(alias="schema", default=BACKUP_SCHEMA)
    version: str = Field(default=VERSION)
    project_id: str = Field(alias="projectId", default="default")
    revision: str = Field(default=VERSION)
    label: str = Field(default="Workbench recovery backup")
    generated_at: str = Field(alias="generatedAt", default="")
    previous_backup_hash: str = Field(alias="previousBackupHash", default="")
    records: list[StorageRecord] = Field(default_factory=list)
    record_count: int = Field(alias="recordCount", default=0)
    total_bytes: int = Field(alias="totalBytes", default=0)
    records_hash: str = Field(alias="recordsHash", default="")
    backup_hash: str = Field(alias="backupHash", default="")

    model_config = {"populate_by_name": True}


class RestorePlanRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    backup: dict[str, Any]
    existing_records: list[StorageRecord] = Field(default_factory=list, max_length=50000)
    strategy: Literal["skip", "overwrite", "rename"] = "skip"
    backup_before_restore: bool = True


class RollbackPlanRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    current_records: list[StorageRecord] = Field(default_factory=list, max_length=50000)
    restore_records: list[StorageRecord] = Field(default_factory=list, max_length=50000)
    confirmation_text: str = Field(default="", max_length=100)
    backup_confirmed: bool = False


class CleanupPlanRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    records: list[StorageRecord] = Field(default_factory=list, max_length=50000)
    duplicate_keys: list[str] = Field(default_factory=list, max_length=50000)
    orphan_keys: list[str] = Field(default_factory=list, max_length=50000)
    stale_keys: list[str] = Field(default_factory=list, max_length=50000)
    selected_keys: list[str] = Field(default_factory=list, max_length=50000)
    scope: Literal["selected", "duplicates", "orphans", "stale", "all-candidates"] = "selected"
    confirmation_text: str = Field(default="", max_length=100)
    backup_confirmed: bool = False


def _target_key(project_id: str, studio: str, legacy_key: str, index: int) -> str:
    suffix = _slug(legacy_key.rsplit(":", 1)[-1] or str(index))
    return f"{CANONICAL_PREFIX}:{_slug(project_id)}:{_slug(studio)}:{suffix}"


def preview_migration(request: MigrationPreviewRequest) -> dict[str, Any]:
    mappings: list[dict[str, Any]] = []
    unknown: list[str] = []
    canonical: list[str] = []
    target_counts: Counter[str] = Counter()
    studios: Counter[str] = Counter()

    for index, record in enumerate(request.records):
        source, studio = classify_legacy_key(record.key)
        if source == "canonical":
            canonical.append(record.key)
            target = record.key
            action = "keep"
        elif source == "unknown":
            unknown.append(record.key)
            studio = record.category if record.category != "other" else "legacy"
            target = _target_key(request.project_id, studio, record.key, index)
            action = "preserve" if request.preserve_unknown else "skip"
        else:
            target = _target_key(request.project_id, studio, record.key, index)
            action = "migrate"
        target_counts[target] += 1
        studios[studio] += 1
        mappings.append({
            "sourceKey": record.key,
            "targetKey": target,
            "sourceFamily": source,
            "studioId": studio,
            "category": record.category,
            "action": action,
            "sizeBytes": record.size_bytes,
            "protected": record.protected,
            "contentHash": record.content_hash or _sha256(record.value),
        })

    collisions = sorted(key for key, count in target_counts.items() if count > 1)
    manifest = {
        "project_id": request.project_id,
        "title": f"Migrated Workbench project: {request.project_id}",
        "revision": VERSION,
        "owner": "",
        "studios": [
            {
                "id": studio,
                "label": studio.replace("-", " ").title(),
                "version": VERSION,
                "status": "active",
                "record_count": count,
                "evidence_ids": [],
                "warnings": [],
            }
            for studio, count in sorted(studios.items())
        ],
        "artifacts": [],
        "evidence_ids": [],
        "assumptions": [],
        "limitations": ["Migrated records require studio-level validation before consequential reuse."],
        "metadata": {
            "sourceVersion": request.source_version,
            "migrationSchema": MIGRATION_SCHEMA,
            "legacyRecordCount": len(request.records),
        },
    }
    executable = bool(request.records) and not collisions
    plan_core = {
        "projectId": request.project_id,
        "sourceVersion": request.source_version,
        "mappings": mappings,
        "manifest": manifest,
    }
    return {
        "ok": executable,
        "schema": MIGRATION_SCHEMA,
        "version": VERSION,
        "generatedAt": _now(),
        "projectId": request.project_id,
        "sourceVersion": request.source_version,
        "targetVersion": VERSION,
        "recordCount": len(request.records),
        "mappedCount": sum(item["action"] == "migrate" for item in mappings),
        "preservedCount": sum(item["action"] in {"keep", "preserve"} for item in mappings),
        "skippedCount": sum(item["action"] == "skip" for item in mappings),
        "unknownKeys": unknown,
        "canonicalKeys": canonical,
        "targetCollisions": collisions,
        "studioCounts": dict(studios),
        "mappings": mappings,
        "projectManifest": manifest,
        "backupRequired": True,
        "destructiveActions": False,
        "executionAllowed": executable,
        "planHash": _sha256(plan_core),
        "warnings": (["Create and download a complete backup before applying migration."] + (["Resolve target-key collisions before migration."] if collisions else []) + (["Unknown keys will be preserved in the legacy studio."] if unknown and request.preserve_unknown else [])),
    }


def audit_storage(request: StorageAuditRequest) -> dict[str, Any]:
    key_counts = Counter(record.key for record in request.records)
    duplicates = sorted(key for key, count in key_counts.items() if count > 1)
    known_keys = set(key_counts)
    orphan_dependencies: dict[str, list[str]] = {}
    hash_mismatches: list[str] = []
    unhashed: list[str] = []
    invalid_values: list[str] = []
    project_manifests: list[str] = []
    categories = Counter()

    for record in request.records:
        categories[record.category] += 1
        if ":project" in record.key or record.category == "project":
            project_manifests.append(record.key)
        missing = sorted(set(record.dependencies) - known_keys)
        if missing:
            orphan_dependencies[record.key] = missing
        computed = _sha256(record.value)
        if not record.content_hash:
            unhashed.append(record.key)
        elif record.content_hash != computed:
            hash_mismatches.append(record.key)
        if isinstance(record.value, str):
            stripped = record.value.strip()
            if stripped.startswith(("{", "[")):
                try:
                    json.loads(stripped)
                except json.JSONDecodeError:
                    invalid_values.append(record.key)

    total_bytes = sum(record.size_bytes for record in request.records)
    quota_percent = total_bytes / request.quota_bytes * 100
    orphan_keys = sorted(orphan_dependencies)
    penalties = len(duplicates) * 12 + len(hash_mismatches) * 8 + len(orphan_keys) * 5 + len(invalid_values) * 4
    if not project_manifests and request.records:
        penalties += 10
    if quota_percent > 90:
        penalties += 15
    elif quota_percent > 75:
        penalties += 7
    score = max(0.0, 100.0 - penalties)
    candidates = sorted(set(duplicates + orphan_keys + invalid_values))
    return {
        "ok": not duplicates and not hash_mismatches and not orphan_keys and quota_percent < 90,
        "schema": STORAGE_SCHEMA,
        "version": VERSION,
        "generatedAt": _now(),
        "projectId": request.project_id,
        "recordCount": len(request.records),
        "totalBytes": total_bytes,
        "quotaBytes": request.quota_bytes,
        "quotaPercent": round(quota_percent, 4),
        "healthScore": round(score, 4),
        "categoryCounts": dict(categories),
        "projectManifestKeys": project_manifests,
        "duplicateKeys": duplicates,
        "orphanDependencies": orphan_dependencies,
        "orphanKeys": orphan_keys,
        "hashMismatches": sorted(set(hash_mismatches)),
        "recordsMissingHash": sorted(set(unhashed)),
        "invalidJsonRecords": sorted(set(invalid_values)),
        "cleanupCandidates": candidates,
        "backupRecommended": bool(candidates or quota_percent > 75),
        "workspaceHash": _sha256([record.model_dump() for record in sorted(request.records, key=lambda item: item.key)]),
    }


def build_backup(request: BackupBuildRequest) -> dict[str, Any]:
    ordered = sorted(request.records, key=lambda item: item.key)
    records_hash = _sha256([record.model_dump() for record in ordered])
    envelope = {
        "schema": BACKUP_SCHEMA,
        "version": VERSION,
        "projectId": request.project_id,
        "revision": request.revision,
        "label": request.label,
        "generatedAt": _now(),
        "previousBackupHash": request.previous_backup_hash,
        "records": [record.model_dump() for record in ordered],
        "recordCount": len(ordered),
        "totalBytes": sum(record.size_bytes for record in ordered),
        "recordsHash": records_hash,
    }
    envelope["backupHash"] = _sha256(envelope)
    return {
        "ok": bool(ordered),
        "schema": BACKUP_SCHEMA,
        "version": VERSION,
        "backup": envelope,
        "recordCount": len(ordered),
        "totalBytes": envelope["totalBytes"],
        "backupHash": envelope["backupHash"],
        "chainLinked": bool(request.previous_backup_hash),
        "downloadRequired": True,
        "warnings": [] if ordered else ["No records were supplied for backup."],
    }


def validate_backup(raw: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    warnings: list[str] = []
    data = dict(raw)
    claimed = str(data.pop("backupHash", ""))
    actual = _sha256(data)
    records = raw.get("records", [])
    records_hash = _sha256(records)
    valid = True
    if raw.get("schema") != BACKUP_SCHEMA:
        warnings.append("Backup schema is unsupported.")
        valid = False
    if not claimed or claimed != actual:
        warnings.append("Backup envelope hash does not match its content.")
        valid = False
    if raw.get("recordsHash") != records_hash:
        warnings.append("Backup record hash does not match the record set.")
        valid = False
    if raw.get("recordCount") != len(records):
        warnings.append("Backup record count is inconsistent.")
        valid = False
    return valid, warnings, {"claimedBackupHash": claimed, "calculatedBackupHash": actual, "calculatedRecordsHash": records_hash}


def plan_restore(request: RestorePlanRequest) -> dict[str, Any]:
    valid, warnings, validation = validate_backup(request.backup)
    backup_records = [StorageRecord.model_validate(item) for item in request.backup.get("records", [])]
    existing = {record.key: record for record in request.existing_records}
    conflicts = sorted(record.key for record in backup_records if record.key in existing)
    operations: list[dict[str, str]] = []
    for record in backup_records:
        if record.key not in existing:
            operations.append({"action": "create", "sourceKey": record.key, "targetKey": record.key})
        elif request.strategy == "overwrite":
            operations.append({"action": "overwrite", "sourceKey": record.key, "targetKey": record.key})
        elif request.strategy == "rename":
            operations.append({"action": "rename", "sourceKey": record.key, "targetKey": f"{record.key}:restored-{_slug(request.backup.get('backupHash', 'backup'))[:12]}"})
        else:
            operations.append({"action": "skip", "sourceKey": record.key, "targetKey": record.key})
    executable = valid and bool(backup_records) and (request.backup_before_restore or not conflicts)
    if conflicts and not request.backup_before_restore:
        warnings.append("Create a rollback backup before restoring over existing keys.")
    return {
        "ok": executable,
        "schema": RESTORE_SCHEMA,
        "version": VERSION,
        "generatedAt": _now(),
        "projectId": request.project_id,
        "backupProjectId": request.backup.get("projectId", ""),
        "strategy": request.strategy,
        "backupValid": valid,
        "backupValidation": validation,
        "recordCount": len(backup_records),
        "conflictKeys": conflicts,
        "operationCounts": dict(Counter(item["action"] for item in operations)),
        "operations": operations,
        "rollbackBackupRequired": bool(conflicts),
        "rollbackBackupConfirmed": request.backup_before_restore,
        "executionAllowed": executable,
        "warnings": warnings,
        "restorePlanHash": _sha256({"backupHash": request.backup.get("backupHash"), "strategy": request.strategy, "operations": operations}),
    }


def plan_rollback(request: RollbackPlanRequest) -> dict[str, Any]:
    current_keys = {record.key for record in request.current_records}
    restore_keys = {record.key for record in request.restore_records}
    creates = sorted(restore_keys - current_keys)
    overwrites = sorted(restore_keys & current_keys)
    removals = sorted(current_keys - restore_keys)
    confirmation_ok = request.confirmation_text.strip().upper() == "ROLLBACK WORKBENCH"
    executable = bool(request.restore_records) and request.backup_confirmed and confirmation_ok
    return {
        "ok": executable,
        "schema": "sc-workbench-rollback-plan/2.0",
        "version": VERSION,
        "generatedAt": _now(),
        "projectId": request.project_id,
        "createKeys": creates,
        "overwriteKeys": overwrites,
        "removeKeys": removals,
        "backupConfirmed": request.backup_confirmed,
        "confirmationValid": confirmation_ok,
        "executionAllowed": executable,
        "rollbackPlanHash": _sha256({"create": creates, "overwrite": overwrites, "remove": removals}),
        "warnings": ([] if request.backup_confirmed else ["A current-state backup is required before rollback."]) + ([] if confirmation_ok else ["Type ROLLBACK WORKBENCH to authorize rollback."]),
    }


def plan_cleanup(request: CleanupPlanRequest) -> dict[str, Any]:
    candidates: set[str]
    if request.scope == "duplicates":
        candidates = set(request.duplicate_keys)
    elif request.scope == "orphans":
        candidates = set(request.orphan_keys)
    elif request.scope == "stale":
        candidates = set(request.stale_keys)
    elif request.scope == "all-candidates":
        candidates = set(request.duplicate_keys) | set(request.orphan_keys) | set(request.stale_keys)
    else:
        candidates = set(request.selected_keys)
    by_key = defaultdict(list)
    for record in request.records:
        by_key[record.key].append(record)
    protected = sorted(key for key in candidates if any(record.protected for record in by_key.get(key, [])))
    existing = sorted(key for key in candidates if key in by_key)
    confirmation_ok = request.confirmation_text.strip().upper() == "CLEAN WORKSPACE"
    backup_required = bool(existing)
    executable = bool(existing) and request.backup_confirmed and confirmation_ok
    return {
        "ok": executable,
        "schema": CLEANUP_SCHEMA,
        "version": VERSION,
        "generatedAt": _now(),
        "projectId": request.project_id,
        "scope": request.scope,
        "selectedKeys": existing,
        "selectedCount": len(existing),
        "selectedBytes": sum(record.size_bytes for key in existing for record in by_key[key]),
        "protectedKeys": protected,
        "backupRequired": backup_required,
        "backupConfirmed": request.backup_confirmed,
        "confirmationValid": confirmation_ok,
        "executionAllowed": executable,
        "warnings": ([] if existing else ["No cleanup candidates matched the selected scope."]) + ([] if request.backup_confirmed else ["Create and download a backup before cleanup."]) + ([] if confirmation_ok else ["Type CLEAN WORKSPACE to authorize cleanup."]),
        "cleanupPlanHash": _sha256({"scope": request.scope, "keys": existing}),
    }


@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "generatedAt": _now(),
        "schemas": [MIGRATION_SCHEMA, STORAGE_SCHEMA, BACKUP_SCHEMA, RESTORE_SCHEMA, CLEANUP_SCHEMA],
        "legacyPrefixes": [prefix for prefix, _ in LEGACY_PREFIXES],
        "canonicalPrefix": CANONICAL_PREFIX,
        "destructiveActionsRequireBackup": True,
    }


@router.post("/migration/preview")
def migration_preview(request: MigrationPreviewRequest) -> dict[str, Any]:
    return preview_migration(request)


@router.post("/storage/audit")
def storage_audit(request: StorageAuditRequest) -> dict[str, Any]:
    return audit_storage(request)


@router.post("/backup/build")
def backup_build(request: BackupBuildRequest) -> dict[str, Any]:
    return build_backup(request)


@router.post("/restore/plan")
def restore_plan(request: RestorePlanRequest) -> dict[str, Any]:
    return plan_restore(request)


@router.post("/rollback/plan")
def rollback_plan(request: RollbackPlanRequest) -> dict[str, Any]:
    return plan_rollback(request)


@router.post("/cleanup/plan")
def cleanup_plan(request: CleanupPlanRequest) -> dict[str, Any]:
    return plan_cleanup(request)

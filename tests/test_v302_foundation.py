from app.v302 import (
    BackupBuildRequest,
    CleanupPlanRequest,
    MigrationPreviewRequest,
    RestorePlanRequest,
    RollbackPlanRequest,
    StorageAuditRequest,
    StorageRecord,
    audit_storage,
    build_backup,
    plan_cleanup,
    plan_restore,
    plan_rollback,
    preview_migration,
    status,
)


def record(key, value=None, **kwargs):
    return StorageRecord(key=key, value={} if value is None else value, size_bytes=kwargs.pop("size_bytes", 100), **kwargs)


def test_status_exposes_recovery_contracts():
    result = status()
    assert result["ok"] is True
    assert result["version"] == "3.0.2"
    assert result["canonicalPrefix"] == "scwb:v3"
    assert result["destructiveActionsRequireBackup"] is True


def test_migration_preview_maps_all_historical_studios():
    records = [
        record("scwb-v200:default:notebook"),
        record("scwb-v220:default:pcb"),
        record("scwb-v280:default:protocol"),
        record("scwb-v290:default:dossier"),
    ]
    result = preview_migration(MigrationPreviewRequest(project_id="alpha", source_version="2.9.0", records=records))
    assert result["ok"] is True
    assert result["mappedCount"] == 4
    assert result["targetCollisions"] == []
    assert result["projectManifest"]["revision"] == "3.0.2"
    assert {item["studioId"] for item in result["mappings"]} == {"research", "electronics", "experiments", "documentation"}


def test_migration_preview_detects_target_collisions():
    records = [record("scwb-v210:a:item"), record("scwb-v210:b:item")]
    result = preview_migration(MigrationPreviewRequest(project_id="alpha", records=records))
    assert result["ok"] is False
    assert result["targetCollisions"]
    assert result["executionAllowed"] is False


def test_storage_audit_detects_orphans_and_quota_pressure():
    records = [
        record("scwb:v3:alpha:project:manifest", dependencies=["missing-key"], category="project", size_bytes=900),
        record("scwb:v3:alpha:simulation:model", category="simulation", size_bytes=900),
    ]
    result = audit_storage(StorageAuditRequest(project_id="alpha", records=records, quota_bytes=2000))
    assert result["ok"] is False
    assert "scwb:v3:alpha:project:manifest" in result["orphanKeys"]
    assert result["quotaPercent"] == 90.0
    assert result["backupRecommended"] is True


def test_backup_hashes_and_restore_validation_pass():
    records = [record("scwb:v3:alpha:project:manifest", {"title": "Alpha"}, category="project")]
    backup_result = build_backup(BackupBuildRequest(project_id="alpha", records=records))
    assert backup_result["ok"] is True
    backup = backup_result["backup"]
    restore = plan_restore(RestorePlanRequest(project_id="alpha", backup=backup, existing_records=[], strategy="skip"))
    assert restore["ok"] is True
    assert restore["backupValid"] is True
    assert restore["operationCounts"] == {"create": 1}


def test_tampered_backup_is_rejected():
    records = [record("scwb:v3:alpha:project:manifest", {"title": "Alpha"}, category="project")]
    backup = build_backup(BackupBuildRequest(project_id="alpha", records=records))["backup"]
    backup["records"][0]["value"] = {"title": "Tampered"}
    restore = plan_restore(RestorePlanRequest(project_id="alpha", backup=backup, existing_records=[]))
    assert restore["ok"] is False
    assert restore["backupValid"] is False


def test_restore_conflicts_require_rollback_backup():
    records = [record("scwb:v3:alpha:project:manifest", {"title": "Alpha"}, category="project")]
    backup = build_backup(BackupBuildRequest(project_id="alpha", records=records))["backup"]
    result = plan_restore(RestorePlanRequest(project_id="alpha", backup=backup, existing_records=records, strategy="overwrite", backup_before_restore=False))
    assert result["ok"] is False
    assert result["rollbackBackupRequired"] is True
    assert result["conflictKeys"] == [records[0].key]


def test_cleanup_and_rollback_require_exact_confirmation():
    records = [record("scwb:v3:alpha:simulation:old", protected=True)]
    cleanup = plan_cleanup(CleanupPlanRequest(project_id="alpha", records=records, orphan_keys=[records[0].key], scope="orphans", backup_confirmed=True, confirmation_text="CLEAN WORKSPACE"))
    assert cleanup["ok"] is True
    rollback = plan_rollback(RollbackPlanRequest(project_id="alpha", current_records=records, restore_records=records, backup_confirmed=True, confirmation_text="ROLLBACK WORKBENCH"))
    assert rollback["ok"] is True

import copy
import pytest

from app.v380 import (
    InstallPlanRequest,
    RuntimeAuditRequest,
    DependencyPlanRequest,
    OfflinePackageRequest,
    SyncExportRequest,
    SyncImportPlanRequest,
    UpdatePlanRequest,
    RecoveryPlanRequest,
    status,
    build_install_plan,
    audit_runtime,
    build_dependency_plan,
    build_offline_package,
    build_sync_export,
    plan_sync_import,
    build_update_plan,
    build_recovery_plan,
)


def test_status_is_loopback_and_cloud_independent():
    result = status()
    assert result["version"] == "3.8.0"
    assert result["localServiceHost"] == "127.0.0.1"
    assert result["renderRequired"] is False
    assert result["paidServiceRequired"] is False
    assert result["remoteShell"] is False


def test_macos_install_plan_is_supported():
    result = build_install_plan(InstallPlanRequest(platform="macos", architecture="arm64", use_wheelhouse=True))
    assert result["ok"] is True
    assert result["plan"]["architectureSupported"] is True
    assert result["plan"]["wheelhouseMode"] == "offline"
    assert result["plan"]["loopbackOnly"] is True
    assert result["plan"]["planHash"]


def test_unknown_architecture_requires_review():
    result = build_install_plan(InstallPlanRequest(platform="linux", architecture="mips64"))
    assert result["ok"] is False
    assert result["plan"]["humanReviewRequired"] is True


def test_unknown_component_blocks_install_plan():
    result = build_install_plan(InstallPlanRequest(platform="linux", architecture="x86_64", components=["local-fastapi-service", "arbitrary-remote-shell"]))
    assert result["ok"] is False
    assert result["plan"]["unknownComponents"] == ["arbitrary-remote-shell"]


def test_runtime_audit_passes_ready_raspberry_pi():
    result = audit_runtime(RuntimeAuditRequest(
        platform="raspberry-pi",
        architecture="aarch64",
        python_version="3.12.2",
        disk_free_mb=4096,
        memory_mb=4096,
        writable_paths=["/home/pi/.local/share/sustainable-catalyst-workbench"],
        available_commands=["python3", "git", "node", "go"],
        loopback_available=True,
    ))
    assert result["ok"] is True
    assert result["audit"]["ready"] is True


def test_runtime_audit_blocks_old_python_and_low_disk():
    result = audit_runtime(RuntimeAuditRequest(
        platform="linux",
        architecture="x86_64",
        python_version="3.9",
        disk_free_mb=512,
        memory_mb=8192,
        writable_paths=["/tmp"],
        available_commands=["python3"],
    ))
    assert result["ok"] is False
    assert "pythonVersion" in result["audit"]["blockingChecks"]
    assert "disk" in result["audit"]["blockingChecks"]


def test_dependency_plan_reports_optional_runtimes_without_blocking():
    result = build_dependency_plan(DependencyPlanRequest(
        platform="macos",
        requested_languages=["python", "javascript", "go", "r", "rust"],
        available_commands=["python3", "node", "go"],
        wheelhouse_available=True,
    ))
    assert result["ok"] is True
    missing_optional = [item["language"] for item in result["plan"]["runtimes"] if not item["available"]]
    assert set(missing_optional) == {"r", "rust"}
    assert result["plan"]["arbitraryPackageExecution"] is False


def test_dependency_plan_rejects_unknown_language():
    result = build_dependency_plan(DependencyPlanRequest(platform="linux", requested_languages=["python", "brainfuck"], available_commands=["python3"]))
    assert result["ok"] is False
    assert result["plan"]["unsupportedLanguages"] == ["brainfuck"]


def test_offline_package_manifest_contains_all_installers():
    result = build_offline_package(OfflinePackageRequest(files=[{"path": "offline/start_local_workbench.py", "size": 100, "sha256": "abc"}]))
    assert result["ok"] is True
    assert set(result["manifest"]["installers"]) == {"macos", "linux", "raspberry-pi"}
    assert result["manifest"]["fileCount"] == 1
    assert result["manifest"]["manifestHash"]


def test_sync_bundle_hash_and_explicit_import():
    result = build_sync_export(SyncExportRequest(project_id="project-1", records=[{"id": "calc-1", "value": 42}]))
    bundle = result["bundle"]
    assert bundle["recordCount"] == 1
    assert bundle["requiresExplicitImport"] is True
    assert bundle["automaticCloudUpload"] is False
    assert bundle["bundleHash"]


def test_sync_import_accepts_valid_bundle():
    bundle = build_sync_export(SyncExportRequest(project_id="project-1", records=[{"id": "calc-1", "value": 42}]))["bundle"]
    result = plan_sync_import(SyncImportPlanRequest(bundle=bundle, existing_record_hashes={}, conflict_strategy="manual"))
    assert result["ok"] is True
    assert result["plan"]["integrityValid"] is True
    assert result["plan"]["action"] == "import"


def test_sync_import_holds_conflict_for_manual_review():
    bundle = build_sync_export(SyncExportRequest(project_id="project-1", records=[{"id": "calc-1", "value": 42}]))["bundle"]
    result = plan_sync_import(SyncImportPlanRequest(bundle=bundle, existing_record_hashes={"calc-1": "different"}, conflict_strategy="manual"))
    assert result["ok"] is False
    assert result["plan"]["action"] == "hold-for-review"
    assert result["plan"]["backupRequired"] is True
    assert result["plan"]["humanReviewRequired"] is True


def test_sync_import_rejects_tampered_bundle():
    bundle = build_sync_export(SyncExportRequest(project_id="project-1", records=[{"id": "calc-1", "value": 42}]))["bundle"]
    tampered = copy.deepcopy(bundle)
    tampered["records"][0]["record"]["value"] = 99
    result = plan_sync_import(SyncImportPlanRequest(bundle=tampered))
    assert result["ok"] is False
    assert result["plan"]["integrityValid"] is False
    assert result["plan"]["action"] == "reject-integrity-failure"


def test_update_requires_hash_and_backup():
    result = build_update_plan(UpdatePlanRequest(current_version="3.8.0", target_version="3.9.0"))
    assert result["ok"] is False
    assert set(result["plan"]["blockingIssues"]) == {"missing-package-hash", "backup-required"}
    assert result["plan"]["automaticUpdateAuthorized"] is False


def test_update_plan_passes_with_hash_and_backup():
    result = build_update_plan(UpdatePlanRequest(current_version="3.8.0", target_version="3.9.0", package_hash="abc123", backup_available=True, service_running=True))
    assert result["ok"] is True
    assert result["plan"]["rollbackPointRequired"] is True
    assert "Request a graceful local-service shutdown." in result["plan"]["actions"]


def test_downgrade_requires_manual_review():
    result = build_update_plan(UpdatePlanRequest(current_version="3.8.0", target_version="3.7.0", package_hash="abc", backup_available=True))
    assert result["ok"] is False
    assert result["plan"]["downgrade"] is True
    assert "downgrade-requires-manual-review" in result["plan"]["blockingIssues"]


def test_recovery_preserves_data_and_avoids_automatic_deletion():
    result = build_recovery_plan(RecoveryPlanRequest(issue="service port conflict", latest_backup="backup-1", database_integrity="unknown", package_integrity="invalid"))
    assert result["ok"] is True
    assert result["plan"]["automaticDeletion"] is False
    assert result["plan"]["humanReviewRequired"] is True
    assert any("loopback port" in step for step in result["plan"]["steps"])

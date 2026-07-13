from backend.app.v300 import (
    ArtifactRecord, DependencyEdge, HandoffRequest, MigrationRequest, PackageRequest,
    ProjectAuditRequest, ProjectManifest, ResetPlanRequest, StudioRecord,
    WorkspaceHealthRequest, WorkspaceRecord, audit_project, build_handoff,
    build_package, evaluate_workspace_health, plan_migration, plan_reset,
)


def manifest():
    return ProjectManifest(
        project_id="project-a", revision="3.0.0",
        studios=[
            StudioRecord(id="research", status="complete", record_count=2),
            StudioRecord(id="simulation", status="complete", record_count=3),
        ],
        artifacts=[ArtifactRecord(path="docs/report.md", kind="documentation", content_hash="abc", size_bytes=10, studio_id="research")],
        evidence_ids=["EV-1"],
    )


def test_project_audit_passes_connected_project():
    result = audit_project(ProjectAuditRequest(manifest=manifest(), dependencies=[DependencyEdge(source="research", target="simulation")]))
    assert result["ok"] is True
    assert result["healthScore"] > 90
    assert len(result["projectHash"]) == 64


def test_project_audit_detects_unknown_dependency():
    result = audit_project(ProjectAuditRequest(manifest=manifest(), dependencies=[DependencyEdge(source="missing", target="simulation")]))
    assert result["ok"] is False
    assert result["unknownDependencies"][0]["source"] == "missing"


def test_handoff_requires_records_and_summary():
    result = build_handoff(HandoffRequest(target="decision-studio", summary="Review", record_ids=["CALC-1"]))
    assert result["ok"] is True
    assert len(result["packetHash"]) == 64


def test_workspace_health_detects_duplicate_keys():
    record = WorkspaceRecord(key="same", category="project", content_hash="abc")
    result = evaluate_workspace_health(WorkspaceHealthRequest(records=[record, record]))
    assert result["ok"] is False
    assert result["duplicateKeys"] == ["same"]


def test_package_builds_hash_chain():
    result = build_package(PackageRequest(manifest=manifest(), files=[ArtifactRecord(path="docs/report.md", content_hash="abc")], previous_package_hash="prev"))
    assert result["ok"] is True
    assert result["chainLinked"] is True
    assert len(result["packageHash"]) == 64


def test_reset_requires_backup_for_protected_record():
    result = plan_reset(ResetPlanRequest(
        records=[WorkspaceRecord(key="project", category="project", content_hash="abc", protected=True)],
        selected_keys=["project"], confirmation_text="RESET WORKBENCH", backup_confirmed=False,
    ))
    assert result["ok"] is False
    assert result["backupRequired"] is True


def test_reset_allows_confirmed_backup():
    result = plan_reset(ResetPlanRequest(
        records=[WorkspaceRecord(key="project", category="project", content_hash="abc", protected=True)],
        scope="all", confirmation_text="RESET WORKBENCH", backup_confirmed=True,
    ))
    assert result["ok"] is True


def test_migration_maps_legacy_keys_without_destructive_action():
    result = plan_migration(MigrationRequest(project_id="p", source_version="2.9.0", storage_keys=["scwb-v290:default:documentation", "other-key"]))
    assert result["ok"] is True
    assert result["mappedKeys"][0]["studioId"] == "documentation"
    assert result["destructiveActions"] is False

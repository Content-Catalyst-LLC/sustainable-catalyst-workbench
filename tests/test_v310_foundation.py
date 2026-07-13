from app.v310 import (
    PROJECT_SCHEMA,
    REVISION_SCHEMA,
    PACKAGE_SCHEMA,
    ProjectRecord,
    ProjectValidationRequest,
    RevisionBuildRequest,
    SyncPlanRequest,
    WorkspacePackageRequest,
    validate_project,
    build_revision,
    plan_sync,
    build_workspace_package,
)


def sample(**overrides):
    data = dict(
        project_id="Water Sensor Pilot",
        title="Water Sensor Pilot",
        storage_mode="hybrid",
        owner_id="42",
        local_revision=2,
        server_revision=1,
        studio_records={"embedded": {"board": "Raspberry Pi 5"}},
        tags=["water", "pilot", "water"],
    )
    data.update(overrides)
    return ProjectRecord(**data)


def test_project_validation_normalizes_and_hashes():
    result = validate_project(sample())
    assert result["ok"] is True
    assert result["schema"] == PROJECT_SCHEMA
    assert result["project"]["project_id"] == "water-sensor-pilot"
    assert result["project"]["tags"] == ["pilot", "water"]
    assert len(result["projectHash"]) == 64
    assert result["studioCount"] == 1


def test_revision_build_is_content_hashed_and_incremented():
    result = build_revision(RevisionBuildRequest(project=sample(), reason="manual-save", changed_paths=["title", "title", "studio_records.embedded"]))
    assert result["ok"] is True
    assert result["schema"] == REVISION_SCHEMA
    assert result["revision"]["revision"] == 3
    assert result["revision"]["changedPaths"] == ["studio_records.embedded", "title"]
    assert len(result["revisionHash"]) == 64


def test_sync_uploads_when_only_local_exists():
    result = plan_sync(SyncPlanRequest(local=sample(), strategy="newest"))
    assert result["ok"] is True
    assert result["decision"] == "upload-local"
    assert result["conflict"] is False


def test_sync_manual_review_on_conflict():
    local = sample(title="Local", local_revision=4)
    remote = sample(title="Remote", local_revision=2, server_revision=4)
    result = plan_sync(SyncPlanRequest(local=local, remote=remote, strategy="manual"))
    assert result["ok"] is False
    assert result["decision"] == "manual-review"
    assert result["conflict"] is True


def test_sync_newest_prefers_remote_server_revision():
    local = sample(title="Local", local_revision=3, server_revision=1, updated_at="2026-07-13T10:00:00Z")
    remote = sample(title="Remote", local_revision=1, server_revision=8, updated_at="2026-07-13T11:00:00Z")
    result = plan_sync(SyncPlanRequest(local=local, remote=remote, strategy="newest"))
    assert result["decision"] == "download-remote"
    assert result["winner"]["title"] == "Remote"


def test_workspace_package_can_exclude_studio_records():
    result = build_workspace_package(WorkspacePackageRequest(project=sample(), revisions=[{"revision": 2}, {"revision": 1}], include_studio_records=False))
    assert result["ok"] is True
    assert result["schema"] == PACKAGE_SCHEMA
    assert result["package"]["project"]["studio_records"] == {}
    assert result["package"]["revisions"][0]["revision"] == 1
    assert len(result["packageHash"]) == 64

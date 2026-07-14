from datetime import datetime, timedelta, timezone
from app.v410 import (
    OrganizationRequest, TeamRequest, AccessRequest, InvitationRequest, InvitationAcceptRequest,
    ProjectSpaceRequest, MergePlanRequest, ActivityRequest, TeamExportRequest,
    build_organization, build_team, evaluate_project_access, build_invitation,
    build_invitation_acceptance_plan, build_project_space, build_revision_merge_plan,
    build_activity_record, build_team_export, status,
)


def test_status_declares_team_workspace_and_safety():
    result = status()
    assert result["version"] == "4.1.0"
    assert result["expectedStudioCount"] == 23
    assert result["automaticMembershipEscalationAuthorized"] is False
    assert result["automaticProjectDeletionAuthorized"] is False


def test_organization_requires_owner_and_is_private():
    blocked = build_organization(OrganizationRequest(name="Example", owner_user_ids=[]))
    assert blocked["ok"] is False
    result = build_organization(OrganizationRequest(name="Example", owner_user_ids=["u1"]))
    assert result["ok"] is True
    assert result["organization"]["private"] is True
    assert result["organization"]["organizationHash"]


def test_team_requires_admin_when_members_are_present():
    result = build_team(TeamRequest(organization_id="org", name="Science", members=[{"userId":"u1","role":"viewer"}]))
    assert result["ok"] is False
    assert "team-admin-required" in result["findings"]


def test_access_matrix_allows_editor_write_and_blocks_viewer():
    memberships=[{"userId":"u1","role":"editor","status":"active"},{"userId":"u2","role":"viewer","status":"active"}]
    assert evaluate_project_access(AccessRequest(user_id="u1", action="project:write", memberships=memberships))["ok"] is True
    assert evaluate_project_access(AccessRequest(user_id="u2", action="project:write", memberships=memberships))["ok"] is False


def test_project_owner_receives_owner_capabilities():
    result=evaluate_project_access(AccessRequest(user_id="u1", action="project:delete", project_owner_id="u1"))
    assert result["ok"] is True
    assert "owner" in result["report"]["roles"]


def test_invitation_persists_hash_not_raw_token():
    result=build_invitation(InvitationRequest(organization_id="org",team_id="team",email="user@example.org",role="editor",inviter_user_id="owner",inviter_role="owner",token="known-token"))
    invitation=result["invitation"]
    assert result["ok"] is True
    assert invitation["rawTokenPersisted"] is False
    assert invitation["tokenHash"] != "known-token"
    assert result["deliveryToken"] == "known-token"


def test_invitation_rejects_unauthorized_inviter():
    result=build_invitation(InvitationRequest(organization_id="org",team_id="team",email="user@example.org",inviter_user_id="viewer",inviter_role="viewer"))
    assert result["ok"] is False
    assert "inviter-not-authorized" in result["findings"]


def test_invitation_acceptance_verifies_token_and_expiration():
    expiry=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
    built=build_invitation(InvitationRequest(organization_id="org",team_id="team",email="user@example.org",inviter_user_id="owner",inviter_role="owner",token="abc",expires_at=expiry))["invitation"]
    result=build_invitation_acceptance_plan(InvitationAcceptRequest(invitation=built,token="abc",accepting_user_id="u2"))
    assert result["ok"] is True
    assert result["plan"]["automaticAcceptanceAuthorized"] is False


def test_invitation_acceptance_rejects_wrong_token():
    built=build_invitation(InvitationRequest(organization_id="org",team_id="team",email="user@example.org",inviter_user_id="owner",inviter_role="owner",token="abc"))["invitation"]
    result=build_invitation_acceptance_plan(InvitationAcceptRequest(invitation=built,token="wrong",accepting_user_id="u2"))
    assert result["ok"] is False
    assert "invitation-token-mismatch" in result["plan"]["findings"]


def test_team_project_space_is_private_and_hashed():
    result=build_project_space(ProjectSpaceRequest(organization_id="org",team_id="team",project_id="p1",title="Project",owner_user_id="u1",role_bindings=[{"userId":"u1","role":"owner"}],records=[{"id":"r1","value":1}]))
    assert result["ok"] is True
    assert result["project"]["private"] is True
    assert result["project"]["projectHash"]


def test_team_project_requires_bindings_for_team_visibility():
    result=build_project_space(ProjectSpaceRequest(organization_id="org",team_id="team",project_id="p1",title="Project",owner_user_id="u1",role_bindings=[]))
    assert result["ok"] is False
    assert "team-project-role-binding-required" in result["findings"]


def test_collaborative_revision_detects_conflict():
    result=build_revision_merge_plan(MergePlanRequest(base={"value":1},local={"value":2},remote={"value":3}))
    assert result["ok"] is False
    assert result["plan"]["conflictCount"] == 1
    assert result["plan"]["automaticConflictResolutionAuthorized"] is False


def test_collaborative_revision_detects_optimistic_concurrency_conflict():
    result=build_revision_merge_plan(MergePlanRequest(base={},local={},remote={},expected_revision=3,remote_revision=4))
    assert result["ok"] is False
    assert result["plan"]["conflicts"][0]["state"] == "optimistic-concurrency-conflict"


def test_activity_records_are_immutable_and_chained():
    result=build_activity_record(ActivityRequest(organization_id="org",team_id="team",project_id="p",actor_user_id="u1",action="project.updated",target_type="project",target_id="p",previous_activity_hash="previous"))
    assert result["ok"] is True
    assert result["activity"]["immutable"] is True
    assert result["activity"]["previousActivityHash"] == "previous"


def test_team_export_redacts_member_directory_and_secrets():
    result=build_team_export(TeamExportRequest(team={"members":[{"userId":"u1","role":"owner"}]},projects=[{"projectId":"p","token":"secret"}],include_member_directory=False))
    package=result["package"]
    assert package["secretsIncluded"] is False
    assert "userIdHash" in package["team"]["members"][0]
    assert "token" not in package["projects"][0]

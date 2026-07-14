"""Workbench v4.1.0 — Hosted Collaborative Workspace and Authenticated Team Projects."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
import secrets
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "4.1.0"
EXPECTED_STUDIOS = 23
router = APIRouter(prefix="/v410", tags=["workbench-v410"])

ROLE_CAPABILITIES: Dict[str, Set[str]] = {
    "owner": {"organization:manage", "team:manage", "member:manage", "project:create", "project:read", "project:write", "project:delete", "review:write", "export:create", "activity:read"},
    "admin": {"team:manage", "member:manage", "project:create", "project:read", "project:write", "project:delete", "review:write", "export:create", "activity:read"},
    "editor": {"project:create", "project:read", "project:write", "review:write", "export:create", "activity:read"},
    "reviewer": {"project:read", "review:write", "export:create", "activity:read"},
    "viewer": {"project:read", "activity:read"},
}
VALID_ROLES = set(ROLE_CAPABILITIES)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def slug(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned or fallback


def normalize_role(value: str) -> str:
    role = (value or "viewer").strip().lower()
    return role if role in VALID_ROLES else "viewer"


def normalize_members(members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: Dict[str, Dict[str, Any]] = {}
    for raw in members:
        user_id = str(raw.get("userId") or raw.get("user_id") or "").strip()
        if not user_id:
            continue
        item = {
            "userId": user_id,
            "role": normalize_role(str(raw.get("role", "viewer"))),
            "status": str(raw.get("status", "active")),
            "joinedAt": str(raw.get("joinedAt", "")),
        }
        existing = normalized.get(user_id)
        if not existing or list(ROLE_CAPABILITIES).index(item["role"]) < list(ROLE_CAPABILITIES).index(existing["role"]):
            normalized[user_id] = item
    return sorted(normalized.values(), key=lambda item: item["userId"])


class OrganizationRequest(BaseModel):
    name: str
    organization_id: str = ""
    owner_user_ids: List[str] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)


class TeamRequest(BaseModel):
    organization_id: str
    name: str
    team_id: str = ""
    members: List[Dict[str, Any]] = Field(default_factory=list)
    default_project_role: str = "editor"


class AccessRequest(BaseModel):
    user_id: str
    action: str
    memberships: List[Dict[str, Any]] = Field(default_factory=list)
    project_bindings: List[Dict[str, Any]] = Field(default_factory=list)
    project_owner_id: str = ""


class InvitationRequest(BaseModel):
    organization_id: str
    team_id: str
    email: str
    role: str = "viewer"
    inviter_user_id: str
    inviter_role: str = "admin"
    token: str = ""
    expires_at: str = ""


class InvitationAcceptRequest(BaseModel):
    invitation: Dict[str, Any] = Field(default_factory=dict)
    token: str
    accepting_user_id: str
    now: str = ""


class ProjectSpaceRequest(BaseModel):
    organization_id: str
    team_id: str
    project_id: str
    title: str
    owner_user_id: str
    visibility: Literal["private", "team"] = "team"
    role_bindings: List[Dict[str, Any]] = Field(default_factory=list)
    records: List[Dict[str, Any]] = Field(default_factory=list)
    revision: int = 1
    previous_project_hash: str = ""
    storage_mode: Literal["browser", "wordpress", "hybrid", "offline"] = "wordpress"


class MergePlanRequest(BaseModel):
    base: Dict[str, Any] = Field(default_factory=dict)
    local: Dict[str, Any] = Field(default_factory=dict)
    remote: Dict[str, Any] = Field(default_factory=dict)
    strategy: Literal["manual", "keep-local", "keep-remote"] = "manual"
    expected_revision: int = 0
    remote_revision: int = 0


class ActivityRequest(BaseModel):
    organization_id: str
    team_id: str
    project_id: str = ""
    actor_user_id: str
    action: str
    target_type: str
    target_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    previous_activity_hash: str = ""
    occurred_at: str = ""


class TeamExportRequest(BaseModel):
    organization: Dict[str, Any] = Field(default_factory=dict)
    team: Dict[str, Any] = Field(default_factory=dict)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    activities: List[Dict[str, Any]] = Field(default_factory=list)
    include_member_directory: bool = False


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "expectedStudioCount": EXPECTED_STUDIOS,
        "workspace": "hosted-collaborative",
        "authentication": ["wordpress-session", "browser-local-fallback", "offline-local"],
        "roles": sorted(VALID_ROLES),
        "privateByDefault": True,
        "paidExternalDatabaseRequired": False,
        "automaticInvitationAcceptanceAuthorized": False,
        "automaticMembershipEscalationAuthorized": False,
        "automaticProjectDeletionAuthorized": False,
        "remoteShell": False,
    }


def build_organization(request: OrganizationRequest) -> Dict[str, Any]:
    owners = sorted({str(item).strip() for item in request.owner_user_ids if str(item).strip()})
    findings = []
    if not request.name.strip():
        findings.append("organization-name-required")
    if not owners:
        findings.append("organization-owner-required")
    settings = {
        "defaultVisibility": "private",
        "allowExternalInvitations": bool(request.settings.get("allowExternalInvitations", False)),
        "dataResidency": str(request.settings.get("dataResidency", "wordpress-site")),
        "retentionDays": max(1, int(request.settings.get("retentionDays", 365))),
    }
    organization = {
        "schema": "sc-workbench-organization/1.0",
        "version": VERSION,
        "organizationId": slug(request.organization_id or request.name, "organization"),
        "name": request.name.strip(),
        "ownerUserIds": owners,
        "settings": settings,
        "private": True,
        "automaticMembershipEscalationAuthorized": False,
    }
    organization["organizationHash"] = stable_hash(organization)
    return {"ok": not findings, "organization": organization, "findings": findings}


def build_team(request: TeamRequest) -> Dict[str, Any]:
    members = normalize_members(request.members)
    findings = []
    if not request.organization_id.strip():
        findings.append("organization-id-required")
    if not request.name.strip():
        findings.append("team-name-required")
    if members and not any(item["role"] in {"owner", "admin"} for item in members):
        findings.append("team-admin-required")
    team = {
        "schema": "sc-workbench-team/1.0",
        "version": VERSION,
        "organizationId": slug(request.organization_id, "organization"),
        "teamId": slug(request.team_id or request.name, "team"),
        "name": request.name.strip(),
        "members": members,
        "memberCount": len(members),
        "defaultProjectRole": normalize_role(request.default_project_role),
        "private": True,
    }
    team["teamHash"] = stable_hash(team)
    return {"ok": not findings, "team": team, "findings": findings}


def evaluate_project_access(request: AccessRequest) -> Dict[str, Any]:
    user_id = request.user_id.strip()
    action = request.action.strip()
    roles: Set[str] = set()
    if user_id and user_id == request.project_owner_id.strip():
        roles.add("owner")
    for raw in request.memberships + request.project_bindings:
        if str(raw.get("userId") or raw.get("user_id") or "").strip() == user_id and str(raw.get("status", "active")) == "active":
            roles.add(normalize_role(str(raw.get("role", "viewer"))))
    capabilities = sorted({capability for role in roles for capability in ROLE_CAPABILITIES[role]})
    allowed = action in capabilities
    report = {
        "schema": "sc-workbench-team-access-report/1.0",
        "version": VERSION,
        "userId": user_id,
        "action": action,
        "roles": sorted(roles),
        "capabilities": capabilities,
        "allowed": allowed,
        "reason": "capability-granted" if allowed else "capability-not-granted",
        "automaticRoleEscalationAuthorized": False,
    }
    report["reportHash"] = stable_hash(report)
    return {"ok": allowed, "report": report}


def build_invitation(request: InvitationRequest) -> Dict[str, Any]:
    role = normalize_role(request.role)
    findings = []
    if normalize_role(request.inviter_role) not in {"owner", "admin"}:
        findings.append("inviter-not-authorized")
    if "@" not in request.email:
        findings.append("valid-email-required")
    token = request.token or secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = request.expires_at or ""
    invitation = {
        "schema": "sc-workbench-team-invitation/1.0",
        "version": VERSION,
        "organizationId": slug(request.organization_id, "organization"),
        "teamId": slug(request.team_id, "team"),
        "emailHash": hashlib.sha256(request.email.strip().lower().encode("utf-8")).hexdigest(),
        "role": role,
        "inviterUserId": request.inviter_user_id.strip(),
        "tokenHash": token_hash,
        "expiresAt": expires_at,
        "status": "pending",
        "rawTokenPersisted": False,
        "automaticAcceptanceAuthorized": False,
    }
    invitation["invitationHash"] = stable_hash(invitation)
    return {"ok": not findings, "invitation": invitation, "deliveryToken": token, "findings": findings}


def _parse_time(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_invitation_acceptance_plan(request: InvitationAcceptRequest) -> Dict[str, Any]:
    invitation = dict(request.invitation)
    findings = []
    supplied_hash = hashlib.sha256(request.token.encode("utf-8")).hexdigest()
    if supplied_hash != invitation.get("tokenHash"):
        findings.append("invitation-token-mismatch")
    if invitation.get("status") != "pending":
        findings.append("invitation-not-pending")
    now = _parse_time(request.now) or datetime.now(timezone.utc)
    expires = _parse_time(str(invitation.get("expiresAt", "")))
    if expires and now > expires:
        findings.append("invitation-expired")
    if not request.accepting_user_id.strip():
        findings.append("accepting-user-required")
    plan = {
        "schema": "sc-workbench-invitation-acceptance-plan/1.0",
        "version": VERSION,
        "organizationId": invitation.get("organizationId", ""),
        "teamId": invitation.get("teamId", ""),
        "userId": request.accepting_user_id.strip(),
        "role": normalize_role(str(invitation.get("role", "viewer"))),
        "ready": not findings,
        "findings": findings,
        "steps": ["verify-authenticated-user", "verify-token-hash", "create-membership-record", "revoke-invitation-token", "append-activity-record"],
        "automaticAcceptanceAuthorized": False,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": not findings, "plan": plan}


def build_project_space(request: ProjectSpaceRequest) -> Dict[str, Any]:
    bindings = normalize_members(request.role_bindings)
    findings = []
    if not request.owner_user_id.strip():
        findings.append("project-owner-required")
    if request.visibility == "team" and not bindings:
        findings.append("team-project-role-binding-required")
    records = []
    for index, raw in enumerate(request.records):
        record = dict(raw)
        record_id = str(record.get("id") or f"record-{index + 1}")
        records.append({"id": record_id, "type": str(record.get("type", "workbench-record")), "recordHash": stable_hash(record)})
    project = {
        "schema": "sc-workbench-team-project-space/1.0",
        "version": VERSION,
        "organizationId": slug(request.organization_id, "organization"),
        "teamId": slug(request.team_id, "team"),
        "projectId": slug(request.project_id, "project"),
        "title": request.title.strip() or "Team Workbench Project",
        "ownerUserId": request.owner_user_id.strip(),
        "visibility": request.visibility,
        "roleBindings": bindings,
        "records": records,
        "recordCount": len(records),
        "revision": max(1, request.revision),
        "previousProjectHash": request.previous_project_hash,
        "storageMode": request.storage_mode,
        "private": True,
        "automaticPublicationAuthorized": False,
        "automaticDeletionAuthorized": False,
    }
    project["projectHash"] = stable_hash(project)
    return {"ok": not findings, "project": project, "findings": findings}


def _flatten(value: Any, prefix: str = "") -> Dict[str, Any]:
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(child, path))
        return out
    return {prefix or "$": value}


def build_revision_merge_plan(request: MergePlanRequest) -> Dict[str, Any]:
    base, local, remote = _flatten(request.base), _flatten(request.local), _flatten(request.remote)
    paths = sorted(set(base) | set(local) | set(remote))
    changes, conflicts, merged = [], [], dict(request.base)
    for path in paths:
        b, l, r = base.get(path), local.get(path), remote.get(path)
        local_changed, remote_changed = l != b, r != b
        if local_changed or remote_changed:
            state = "local" if local_changed and not remote_changed else "remote" if remote_changed and not local_changed else "same" if l == r else "conflict"
            item = {"path": path, "base": b, "local": l, "remote": r, "state": state}
            changes.append(item)
            if state == "conflict": conflicts.append(item)
    revision_conflict = bool(request.expected_revision and request.remote_revision != request.expected_revision)
    if revision_conflict:
        conflicts.append({"path": "$revision", "expected": request.expected_revision, "remote": request.remote_revision, "state": "optimistic-concurrency-conflict"})
    actions = []
    if conflicts and request.strategy == "manual":
        actions.append({"action": "manual-merge-required", "conflictCount": len(conflicts)})
    elif request.strategy == "keep-local":
        actions.append({"action": "apply-local-with-new-revision", "requiresBackup": True})
        merged = dict(request.local)
    elif request.strategy == "keep-remote":
        actions.append({"action": "accept-remote", "requiresBackup": False})
        merged = dict(request.remote)
    else:
        merged = dict(request.remote)
        for item in changes:
            if item["state"] == "local":
                merged[item["path"]] = item["local"]
        actions.append({"action": "apply-non-conflicting-changes", "requiresBackup": False})
    plan = {
        "schema": "sc-workbench-collaborative-revision-merge-plan/1.0",
        "version": VERSION,
        "expectedRevision": request.expected_revision,
        "remoteRevision": request.remote_revision,
        "changes": changes,
        "conflicts": conflicts,
        "conflictCount": len(conflicts),
        "actions": actions,
        "mergedPreview": merged,
        "automaticConflictResolutionAuthorized": False,
        "automaticOverwriteAuthorized": False,
    }
    plan["planHash"] = stable_hash(plan)
    return {"ok": not conflicts, "plan": plan}


def build_activity_record(request: ActivityRequest) -> Dict[str, Any]:
    occurred_at = request.occurred_at or datetime.now(timezone.utc).isoformat()
    record = {
        "schema": "sc-workbench-team-activity/1.0",
        "version": VERSION,
        "organizationId": slug(request.organization_id, "organization"),
        "teamId": slug(request.team_id, "team"),
        "projectId": slug(request.project_id, "") if request.project_id else "",
        "actorUserId": request.actor_user_id.strip(),
        "action": request.action.strip(),
        "targetType": request.target_type.strip(),
        "targetId": request.target_id.strip(),
        "metadata": request.metadata,
        "occurredAt": occurred_at,
        "previousActivityHash": request.previous_activity_hash,
        "immutable": True,
    }
    record["activityHash"] = stable_hash(record)
    findings = [] if record["actorUserId"] and record["action"] and record["targetId"] else ["actor-action-target-required"]
    return {"ok": not findings, "activity": record, "findings": findings}


def build_team_export(request: TeamExportRequest) -> Dict[str, Any]:
    team = dict(request.team)
    if not request.include_member_directory:
        team["members"] = [{"userIdHash": stable_hash(str(item.get("userId", ""))), "role": item.get("role", "viewer")} for item in team.get("members", [])]
    projects = []
    for raw in request.projects:
        project = dict(raw)
        for key in list(project):
            if key.lower() in {"token", "tokenhash", "secret", "password", "nonce"}:
                project.pop(key, None)
        projects.append(project)
    package = {
        "schema": "sc-workbench-team-workspace-export/1.0",
        "version": VERSION,
        "organization": request.organization,
        "team": team,
        "projects": projects,
        "activities": request.activities,
        "projectCount": len(projects),
        "activityCount": len(request.activities),
        "memberDirectoryIncluded": request.include_member_directory,
        "secretsIncluded": False,
        "requiresExplicitImport": True,
        "automaticCloudUpload": False,
    }
    package["packageHash"] = stable_hash(package)
    return {"ok": True, "package": package}


@router.get("/status")
def status_route() -> Dict[str, Any]:
    return status()


@router.post("/organization/build")
def organization_route(request: OrganizationRequest) -> Dict[str, Any]:
    return build_organization(request)


@router.post("/team/build")
def team_route(request: TeamRequest) -> Dict[str, Any]:
    return build_team(request)


@router.post("/access/evaluate")
def access_route(request: AccessRequest) -> Dict[str, Any]:
    return evaluate_project_access(request)


@router.post("/invitation/build")
def invitation_route(request: InvitationRequest) -> Dict[str, Any]:
    return build_invitation(request)


@router.post("/invitation/accept-plan")
def invitation_accept_route(request: InvitationAcceptRequest) -> Dict[str, Any]:
    return build_invitation_acceptance_plan(request)


@router.post("/project-space/build")
def project_space_route(request: ProjectSpaceRequest) -> Dict[str, Any]:
    return build_project_space(request)


@router.post("/revision/merge-plan")
def revision_route(request: MergePlanRequest) -> Dict[str, Any]:
    return build_revision_merge_plan(request)


@router.post("/activity/build")
def activity_route(request: ActivityRequest) -> Dict[str, Any]:
    return build_activity_record(request)


@router.post("/export/build")
def export_route(request: TeamExportRequest) -> Dict[str, Any]:
    return build_team_export(request)

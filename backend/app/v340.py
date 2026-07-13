from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

VERSION = "3.4.0"
REVIEW_SCHEMA = "sc-workbench-technical-review/1.0"
COMMENT_SCHEMA = "sc-workbench-review-comment/1.0"
CHANGE_SCHEMA = "sc-workbench-change-request/1.0"
TRACE_SCHEMA = "sc-workbench-review-traceability/1.0"
DIFF_SCHEMA = "sc-workbench-revision-comparison/1.0"
SNAPSHOT_SCHEMA = "sc-workbench-review-snapshot/1.0"
SIGNOFF_SCHEMA = "sc-workbench-technical-signoff/1.0"
DOSSIER_SCHEMA = "sc-workbench-review-dossier/1.0"

router = APIRouter(prefix="/v340", tags=["workbench-v340"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _hash(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _slug(value: Any, fallback: str = "record") -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text[:120] or fallback


ReviewState = Literal["draft", "queued", "in-review", "changes-requested", "conditionally-approved", "approved", "rejected", "closed"]
ReviewRole = Literal["author", "reviewer", "approver", "observer"]
DecisionState = Literal["approved", "conditionally-approved", "rejected", "returned-for-changes"]
SignoffScope = Literal["internal-review", "qualified-professional-review"]


class Reviewer(BaseModel):
    reviewer_id: str = ""
    display_name: str = ""
    role: ReviewRole = "reviewer"
    organization: str = ""
    credential_reference: str = ""
    independent: bool = False


class ReviewItem(BaseModel):
    record_id: str
    record_type: str = "workbench-record"
    title: str = ""
    revision: str = "1"
    content_hash: str = ""
    criticality: Literal["low", "medium", "high", "critical"] = "medium"
    requirement_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewComment(BaseModel):
    comment_id: str = ""
    reviewer_id: str = ""
    target_record_id: str = ""
    target_path: str = ""
    body: str
    status: Literal["open", "resolved", "superseded"] = "open"
    parent_comment_id: str = ""


class ChangeRequest(BaseModel):
    change_id: str = ""
    title: str
    description: str = ""
    target_record_id: str = ""
    target_path: str = ""
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    status: Literal["open", "in-progress", "resolved", "accepted-risk", "closed"] = "open"
    requested_by: str = ""
    assigned_to: str = ""
    resolution: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


class ReviewBuildRequest(BaseModel):
    project_id: str = "default"
    title: str = "Technical review"
    review_id: str = ""
    revision: str = "1"
    state: ReviewState = "draft"
    owner_id: str = ""
    reviewers: list[Reviewer] = Field(default_factory=list)
    items: list[ReviewItem] = Field(default_factory=list)
    comments: list[ReviewComment] = Field(default_factory=list)
    change_requests: list[ChangeRequest] = Field(default_factory=list)
    requirement_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueueRequest(BaseModel):
    reviews: list[dict[str, Any]] = Field(default_factory=list)
    reviewer_id: str = ""
    states: list[ReviewState] = Field(default_factory=lambda: ["queued", "in-review", "changes-requested", "conditionally-approved"])


class CommentRequest(BaseModel):
    review_hash: str
    comment: ReviewComment


class ChangeBuildRequest(BaseModel):
    review_hash: str
    change: ChangeRequest


class RevisionCompareRequest(BaseModel):
    left: dict[str, Any]
    right: dict[str, Any]
    ignore_paths: list[str] = Field(default_factory=list)


class TraceabilityRequest(BaseModel):
    requirements: list[dict[str, Any]] = Field(default_factory=list)
    reviews: list[dict[str, Any]] = Field(default_factory=list)


class SnapshotRequest(BaseModel):
    review: ReviewBuildRequest
    previous_snapshot_hash: str = ""
    locked_by: str = ""


class SignoffRequest(BaseModel):
    snapshot_hash: str
    reviewer: Reviewer
    decision: DecisionState
    rationale: str
    conditions: list[str] = Field(default_factory=list)
    scope: SignoffScope = "internal-review"
    credential_reference: str = ""
    unresolved_critical_changes: int = 0


class DossierRequest(BaseModel):
    review: ReviewBuildRequest
    snapshots: list[dict[str, Any]] = Field(default_factory=list)
    signoffs: list[dict[str, Any]] = Field(default_factory=list)
    traceability: dict[str, Any] = Field(default_factory=dict)
    revision_comparisons: list[dict[str, Any]] = Field(default_factory=list)


def normalize_reviewer(reviewer: Reviewer) -> dict[str, Any]:
    data = reviewer.model_dump()
    data["reviewer_id"] = _slug(data.get("reviewer_id") or data.get("display_name"), "reviewer")
    data["display_name"] = data.get("display_name", "").strip()[:200]
    return data


def normalize_item(item: ReviewItem) -> dict[str, Any]:
    data = item.model_dump()
    data["record_id"] = _slug(data["record_id"], "record")
    data["record_type"] = _slug(data.get("record_type"), "workbench-record")
    data["requirement_ids"] = sorted({_slug(value, "requirement") for value in data.get("requirement_ids", []) if str(value).strip()})
    data["evidence_ids"] = sorted({_slug(value, "evidence") for value in data.get("evidence_ids", []) if str(value).strip()})
    if not data.get("content_hash"):
        data["content_hash"] = _hash({k: v for k, v in data.items() if k != "content_hash"})
    return data


def normalize_comment(comment: ReviewComment) -> dict[str, Any]:
    data = comment.model_dump()
    data["comment_id"] = _slug(data.get("comment_id") or f"{data.get('reviewer_id')}-{data.get('target_record_id')}-{data.get('body')[:30]}", "comment")
    data["reviewer_id"] = _slug(data.get("reviewer_id"), "reviewer")
    data["target_record_id"] = _slug(data.get("target_record_id"), "record") if data.get("target_record_id") else ""
    data["created_at"] = _now()
    data["comment_hash"] = _hash({k: v for k, v in data.items() if k not in {"comment_hash"}})
    return data


def normalize_change(change: ChangeRequest) -> dict[str, Any]:
    data = change.model_dump()
    data["change_id"] = _slug(data.get("change_id") or data.get("title"), "change")
    data["target_record_id"] = _slug(data.get("target_record_id"), "record") if data.get("target_record_id") else ""
    data["evidence_ids"] = sorted({_slug(value, "evidence") for value in data.get("evidence_ids", []) if str(value).strip()})
    data["updated_at"] = _now()
    data["change_hash"] = _hash({k: v for k, v in data.items() if k != "change_hash"})
    return data


def build_review_record(request: ReviewBuildRequest) -> dict[str, Any]:
    reviewers = [normalize_reviewer(item) for item in request.reviewers]
    reviewer_ids = [item["reviewer_id"] for item in reviewers]
    if len(reviewer_ids) != len(set(reviewer_ids)):
        raise ValueError("reviewer_id values must be unique")
    items = [normalize_item(item) for item in request.items]
    item_ids = [item["record_id"] for item in items]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("record_id values must be unique")
    comments = [normalize_comment(item) for item in request.comments]
    changes = [normalize_change(item) for item in request.change_requests]
    unresolved = [item for item in changes if item["status"] not in {"resolved", "accepted-risk", "closed"}]
    critical = [item for item in unresolved if item["priority"] == "critical"]
    record = {
        "schema": REVIEW_SCHEMA,
        "version": VERSION,
        "reviewId": _slug(request.review_id or f"{request.project_id}-{request.title}", "review"),
        "projectId": _slug(request.project_id, "default"),
        "title": request.title.strip()[:300],
        "revision": request.revision.strip()[:80],
        "state": request.state,
        "ownerId": _slug(request.owner_id, "owner") if request.owner_id else "",
        "reviewers": reviewers,
        "items": items,
        "comments": comments,
        "changeRequests": changes,
        "requirementIds": sorted({_slug(value, "requirement") for value in request.requirement_ids if str(value).strip()}),
        "metadata": request.metadata,
        "metrics": {
            "reviewerCount": len(reviewers),
            "itemCount": len(items),
            "openCommentCount": sum(1 for item in comments if item["status"] == "open"),
            "openChangeCount": len(unresolved),
            "criticalOpenChangeCount": len(critical),
        },
        "professionalCertification": False,
        "scopeBoundary": "Workbench review records document internal or qualified review activity but do not themselves create a license, certification, seal, or regulatory approval.",
        "updatedAt": _now(),
    }
    record["reviewHash"] = _hash(record)
    return {"ok": True, "schema": REVIEW_SCHEMA, "version": VERSION, "review": record, "reviewHash": record["reviewHash"]}


def build_review_queue(request: QueueRequest) -> dict[str, Any]:
    allowed = set(request.states)
    reviewer = _slug(request.reviewer_id, "") if request.reviewer_id else ""
    rows = []
    for raw in request.reviews:
        state = str(raw.get("state", "draft"))
        if state not in allowed:
            continue
        reviewers = raw.get("reviewers", []) or []
        ids = {_slug(item.get("reviewer_id") or item.get("reviewerId") or item.get("display_name"), "reviewer") for item in reviewers if isinstance(item, dict)}
        if reviewer and reviewer not in ids:
            continue
        rows.append({
            "reviewId": raw.get("reviewId") or raw.get("review_id") or "",
            "projectId": raw.get("projectId") or raw.get("project_id") or "default",
            "title": raw.get("title", "Technical review"),
            "state": state,
            "revision": str(raw.get("revision", "1")),
            "criticalOpenChangeCount": int((raw.get("metrics") or {}).get("criticalOpenChangeCount", 0)),
            "updatedAt": raw.get("updatedAt", ""),
        })
    priority = {"changes-requested": 0, "in-review": 1, "conditionally-approved": 2, "queued": 3}
    rows.sort(key=lambda row: (priority.get(row["state"], 9), -row["criticalOpenChangeCount"], row["title"].lower()))
    result = {"schema": "sc-workbench-review-queue/1.0", "version": VERSION, "reviewerId": reviewer, "count": len(rows), "reviews": rows, "generatedAt": _now()}
    result["queueHash"] = _hash(result)
    return result


def attach_comment(request: CommentRequest) -> dict[str, Any]:
    comment = normalize_comment(request.comment)
    record = {"schema": COMMENT_SCHEMA, "version": VERSION, "reviewHash": request.review_hash, "comment": comment, "attachedAt": _now()}
    record["attachmentHash"] = _hash(record)
    return record


def build_change_request(request: ChangeBuildRequest) -> dict[str, Any]:
    change = normalize_change(request.change)
    record = {"schema": CHANGE_SCHEMA, "version": VERSION, "reviewHash": request.review_hash, "changeRequest": change, "createdAt": _now()}
    record["requestHash"] = _hash(record)
    return record


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten(value[key], path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]"
            result.update(_flatten(item, path))
    else:
        result[prefix or "$root"] = value
    return result


def compare_revisions(request: RevisionCompareRequest) -> dict[str, Any]:
    ignored = set(request.ignore_paths)
    left = _flatten(request.left)
    right = _flatten(request.right)
    paths = sorted((set(left) | set(right)) - ignored)
    changes = []
    for path in paths:
        if path not in left:
            changes.append({"path": path, "change": "added", "left": None, "right": right[path]})
        elif path not in right:
            changes.append({"path": path, "change": "removed", "left": left[path], "right": None})
        elif left[path] != right[path]:
            changes.append({"path": path, "change": "modified", "left": left[path], "right": right[path]})
    result = {"schema": DIFF_SCHEMA, "version": VERSION, "leftHash": _hash(request.left), "rightHash": _hash(request.right), "changeCount": len(changes), "changes": changes, "comparedAt": _now()}
    result["comparisonHash"] = _hash(result)
    return result


def build_traceability_matrix(request: TraceabilityRequest) -> dict[str, Any]:
    requirements = []
    covered = set()
    for review in request.reviews:
        for item in review.get("items", []) or []:
            for requirement_id in item.get("requirement_ids", item.get("requirementIds", [])) or []:
                covered.add(_slug(requirement_id, "requirement"))
    for raw in request.requirements:
        requirement_id = _slug(raw.get("requirement_id") or raw.get("requirementId") or raw.get("id") or raw.get("title"), "requirement")
        requirements.append({
            "requirementId": requirement_id,
            "title": raw.get("title", requirement_id),
            "critical": bool(raw.get("critical", False)),
            "reviewCovered": requirement_id in covered,
        })
    uncovered = [item for item in requirements if not item["reviewCovered"]]
    critical_uncovered = [item for item in uncovered if item["critical"]]
    result = {"schema": TRACE_SCHEMA, "version": VERSION, "requirements": requirements, "coveragePercent": round((len(requirements) - len(uncovered)) * 100 / len(requirements), 2) if requirements else 100.0, "uncoveredRequirementIds": [item["requirementId"] for item in uncovered], "criticalUncoveredRequirementIds": [item["requirementId"] for item in critical_uncovered], "complete": not uncovered, "generatedAt": _now()}
    result["traceabilityHash"] = _hash(result)
    return result


def build_review_snapshot(request: SnapshotRequest) -> dict[str, Any]:
    review = build_review_record(request.review)["review"]
    snapshot = {
        "schema": SNAPSHOT_SCHEMA,
        "version": VERSION,
        "snapshotId": _slug(f"{review['reviewId']}-{review['revision']}-{review['reviewHash'][:12]}", "snapshot"),
        "review": review,
        "reviewHash": review["reviewHash"],
        "previousSnapshotHash": request.previous_snapshot_hash.strip(),
        "lockedBy": _slug(request.locked_by, "reviewer") if request.locked_by else "",
        "lockedAt": _now(),
        "immutable": True,
    }
    snapshot["snapshotHash"] = _hash(snapshot)
    return {"ok": True, "schema": SNAPSHOT_SCHEMA, "version": VERSION, "snapshot": snapshot, "snapshotHash": snapshot["snapshotHash"]}


def build_signoff(request: SignoffRequest) -> dict[str, Any]:
    reviewer = normalize_reviewer(request.reviewer)
    credential = request.credential_reference.strip() or reviewer.get("credential_reference", "").strip()
    if request.scope == "qualified-professional-review" and not credential:
        raise ValueError("qualified-professional-review requires a credential_reference")
    if request.decision in {"approved", "conditionally-approved"} and request.unresolved_critical_changes > 0:
        raise ValueError("critical change requests must be resolved before approval")
    signoff = {
        "schema": SIGNOFF_SCHEMA,
        "version": VERSION,
        "snapshotHash": request.snapshot_hash,
        "reviewer": reviewer,
        "decision": request.decision,
        "rationale": request.rationale.strip(),
        "conditions": [str(item).strip() for item in request.conditions if str(item).strip()],
        "scope": request.scope,
        "credentialReference": credential,
        "professionalCertification": request.scope == "qualified-professional-review",
        "signedAt": _now(),
        "scopeBoundary": "This record documents a review decision. Regulatory certification, engineering seals, legal approvals, and other licensed acts remain governed by applicable law and professional authority.",
    }
    signoff["signoffHash"] = _hash(signoff)
    return {"ok": True, "schema": SIGNOFF_SCHEMA, "version": VERSION, "signoff": signoff, "signoffHash": signoff["signoffHash"]}


def build_review_dossier(request: DossierRequest) -> dict[str, Any]:
    review = build_review_record(request.review)["review"]
    dossier = {
        "schema": DOSSIER_SCHEMA,
        "version": VERSION,
        "dossierId": _slug(f"{review['reviewId']}-{review['revision']}-dossier", "review-dossier"),
        "createdAt": _now(),
        "review": review,
        "snapshots": request.snapshots,
        "signoffs": request.signoffs,
        "traceability": request.traceability,
        "revisionComparisons": request.revision_comparisons,
        "summary": {
            "reviewState": review["state"],
            "reviewerCount": len(review["reviewers"]),
            "itemCount": len(review["items"]),
            "openChangeCount": review["metrics"]["openChangeCount"],
            "criticalOpenChangeCount": review["metrics"]["criticalOpenChangeCount"],
            "snapshotCount": len(request.snapshots),
            "signoffCount": len(request.signoffs),
        },
        "scopeBoundary": review["scopeBoundary"],
    }
    dossier["dossierHash"] = _hash(dossier)
    return {"ok": True, "schema": DOSSIER_SCHEMA, "version": VERSION, "dossier": dossier, "dossierHash": dossier["dossierHash"]}


@router.get("/status")
def status() -> dict[str, Any]:
    return {"ok": True, "version": VERSION, "schema": "sc-workbench-review-status/1.0", "capabilities": ["review-queues", "record-comments", "change-requests", "revision-comparison", "traceability", "immutable-snapshots", "technical-signoff", "review-dossiers"]}


@router.post("/review/build")
def review_build(request: ReviewBuildRequest) -> dict[str, Any]:
    try:
        return build_review_record(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/review/queue")
def review_queue(request: QueueRequest) -> dict[str, Any]:
    return build_review_queue(request)


@router.post("/comment/attach")
def comment_attach(request: CommentRequest) -> dict[str, Any]:
    return attach_comment(request)


@router.post("/change/build")
def change_build(request: ChangeBuildRequest) -> dict[str, Any]:
    return build_change_request(request)


@router.post("/revision/compare")
def revision_compare(request: RevisionCompareRequest) -> dict[str, Any]:
    return compare_revisions(request)


@router.post("/traceability/build")
def traceability_build(request: TraceabilityRequest) -> dict[str, Any]:
    return build_traceability_matrix(request)


@router.post("/snapshot/build")
def snapshot_build(request: SnapshotRequest) -> dict[str, Any]:
    return build_review_snapshot(request)


@router.post("/signoff/build")
def signoff_build(request: SignoffRequest) -> dict[str, Any]:
    try:
        return build_signoff(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/dossier/build")
def dossier_build(request: DossierRequest) -> dict[str, Any]:
    return build_review_dossier(request)

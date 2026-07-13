"""Workbench v2.9.0 technical documentation and product dossier routes."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "2.9.0"
router = APIRouter(prefix="/v290", tags=["workbench-v290"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class Requirement(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    source: str = Field(default="", max_length=300)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    status: Literal["draft", "approved", "implemented", "verified", "retired"] = "draft"
    verification_method: Literal["inspection", "analysis", "demonstration", "test", "review"] = "test"


class VerificationRecord(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(default="", max_length=300)
    requirement_ids: list[str] = Field(default_factory=list, max_length=500)
    evidence_ids: list[str] = Field(default_factory=list, max_length=500)
    status: Literal["not-run", "pass", "fail", "blocked", "waived"] = "not-run"
    revision: str = Field(default="", max_length=120)


class TraceabilityRequest(BaseModel):
    requirements: list[Requirement] = Field(min_length=1, max_length=5000)
    verifications: list[VerificationRecord] = Field(default_factory=list, max_length=5000)


class DossierSection(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(default="", max_length=200000)
    source_records: list[str] = Field(default_factory=list, max_length=2000)
    status: Literal["draft", "review", "approved", "superseded"] = "draft"


class DossierRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    title: str = Field(default="Technical dossier", max_length=300)
    product_name: str = Field(default="", max_length=300)
    revision: str = Field(default="0.1.0", max_length=120)
    owner: str = Field(default="", max_length=300)
    sections: list[DossierSection] = Field(min_length=1, max_length=500)
    assumptions: list[str] = Field(default_factory=list, max_length=2000)
    limitations: list[str] = Field(default_factory=list, max_length=2000)
    risks: list[str] = Field(default_factory=list, max_length=2000)


class RevisionRecord(BaseModel):
    revision: str = Field(min_length=1, max_length=120)
    date: str = Field(default="", max_length=80)
    author: str = Field(default="", max_length=300)
    summary: str = Field(default="", max_length=3000)
    artifact_hash: str = Field(default="", max_length=128)
    approved: bool = False


class ChangeRecord(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    reason: str = Field(default="", max_length=5000)
    affected_items: list[str] = Field(default_factory=list, max_length=1000)
    status: Literal["proposed", "approved", "implemented", "verified", "rejected"] = "proposed"
    target_revision: str = Field(default="", max_length=120)


class RevisionAuditRequest(BaseModel):
    revisions: list[RevisionRecord] = Field(min_length=1, max_length=5000)
    changes: list[ChangeRecord] = Field(default_factory=list, max_length=5000)


class EvidenceRecord(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=300)
    kind: Literal["calculation", "test", "inspection", "simulation", "measurement", "source", "image", "report", "other"] = "other"
    source_uri: str = Field(default="", max_length=2000)
    revision: str = Field(default="", max_length=120)
    content_hash: str = Field(default="", max_length=128)
    generated_at: str = Field(default="", max_length=80)
    approved: bool = False


class EvidenceRegisterRequest(BaseModel):
    records: list[EvidenceRecord] = Field(min_length=1, max_length=10000)


class ReadinessItem(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    category: Literal["requirements", "design", "software", "hardware", "verification", "manufacturing", "quality", "safety", "compliance", "documentation"]
    title: str = Field(min_length=1, max_length=300)
    status: Literal["not-started", "in-progress", "complete", "blocked", "not-applicable"] = "not-started"
    critical: bool = False
    evidence_ids: list[str] = Field(default_factory=list, max_length=500)


class ReadinessRequest(BaseModel):
    items: list[ReadinessItem] = Field(min_length=1, max_length=5000)


class SnapshotFile(BaseModel):
    path: str = Field(min_length=1, max_length=1000)
    content_hash: str = Field(min_length=1, max_length=128)
    size_bytes: int = Field(default=0, ge=0, le=10_000_000_000)
    media_type: str = Field(default="application/octet-stream", max_length=200)


class SnapshotRequest(BaseModel):
    project_id: str = Field(default="default", max_length=160)
    revision: str = Field(default="0.1.0", max_length=120)
    previous_snapshot_hash: str = Field(default="", max_length=128)
    files: list[SnapshotFile] = Field(min_length=1, max_length=20000)
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/traceability/evaluate")
def evaluate_traceability(request: TraceabilityRequest) -> dict[str, Any]:
    requirement_ids = [record.id for record in request.requirements]
    duplicate_requirements = sorted([key for key, count in Counter(requirement_ids).items() if count > 1])
    known = set(requirement_ids)
    verification_ids = [record.id for record in request.verifications]
    duplicate_verifications = sorted([key for key, count in Counter(verification_ids).items() if count > 1])
    linked: dict[str, list[str]] = defaultdict(list)
    unknown_links: list[dict[str, str]] = []
    for record in request.verifications:
        for requirement_id in record.requirement_ids:
            if requirement_id in known:
                linked[requirement_id].append(record.id)
            else:
                unknown_links.append({"verificationId": record.id, "requirementId": requirement_id})
    uncovered = sorted([record.id for record in request.requirements if not linked.get(record.id)])
    failed_critical = sorted({requirement_id for record in request.verifications if record.status == "fail" for requirement_id in record.requirement_ids if requirement_id in known and next((r.priority for r in request.requirements if r.id == requirement_id), "") == "critical"})
    covered = len(known) - len(uncovered)
    coverage = covered / len(known) if known else 0.0
    return {
        "ok": not duplicate_requirements and not duplicate_verifications and not unknown_links and not failed_critical,
        "schema": "sc-workbench-requirements-traceability/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "requirementCount": len(request.requirements),
        "verificationCount": len(request.verifications),
        "coveredRequirements": covered,
        "coveragePercent": round(coverage * 100, 4),
        "uncoveredRequirements": uncovered,
        "failedCriticalRequirements": failed_critical,
        "duplicateRequirementIds": duplicate_requirements,
        "duplicateVerificationIds": duplicate_verifications,
        "unknownRequirementLinks": unknown_links,
        "traceability": [{"requirementId": record.id, "verificationIds": sorted(linked.get(record.id, []))} for record in request.requirements],
        "recordHash": _sha256(request.model_dump()),
    }


@router.post("/dossier/build")
def build_dossier(request: DossierRequest) -> dict[str, Any]:
    section_ids = [section.id for section in request.sections]
    duplicates = sorted([key for key, count in Counter(section_ids).items() if count > 1])
    empty_sections = sorted([section.id for section in request.sections if not section.content.strip()])
    approved = sum(section.status == "approved" for section in request.sections)
    complete = len(request.sections) - len(empty_sections)
    dossier = {
        "projectId": request.project_id,
        "title": request.title,
        "productName": request.product_name,
        "revision": request.revision,
        "owner": request.owner,
        "generatedAt": _now(),
        "tableOfContents": [{"number": index + 1, "id": section.id, "title": section.title, "status": section.status} for index, section in enumerate(request.sections)],
        "sections": [section.model_dump() for section in request.sections],
        "assumptions": request.assumptions,
        "limitations": request.limitations,
        "risks": request.risks,
    }
    return {
        "ok": not duplicates and not empty_sections,
        "schema": "sc-workbench-technical-dossier/1.0",
        "version": VERSION,
        "dossier": dossier,
        "completeness": {
            "sectionCount": len(request.sections),
            "completeSections": complete,
            "approvedSections": approved,
            "emptySections": empty_sections,
            "percent": round((complete / len(request.sections)) * 100, 4),
        },
        "duplicateSectionIds": duplicates,
        "dossierHash": _sha256(dossier),
    }


@router.post("/revision/audit")
def audit_revisions(request: RevisionAuditRequest) -> dict[str, Any]:
    revision_ids = [record.revision for record in request.revisions]
    duplicates = sorted([key for key, count in Counter(revision_ids).items() if count > 1])
    unapproved = [record.revision for record in request.revisions if not record.approved]
    missing_hashes = [record.revision for record in request.revisions if not record.artifact_hash]
    open_changes = [record.id for record in request.changes if record.status in {"proposed", "approved", "implemented"}]
    unlinked_changes = [record.id for record in request.changes if record.target_revision and record.target_revision not in set(revision_ids)]
    return {
        "ok": not duplicates and not unlinked_changes,
        "schema": "sc-workbench-revision-change-audit/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "revisionCount": len(request.revisions),
        "changeCount": len(request.changes),
        "duplicateRevisions": duplicates,
        "unapprovedRevisions": unapproved,
        "revisionsMissingArtifactHash": missing_hashes,
        "openChanges": open_changes,
        "changesWithUnknownTargetRevision": unlinked_changes,
        "latestRevision": request.revisions[-1].revision,
        "auditHash": _sha256(request.model_dump()),
    }


@router.post("/evidence/register")
def register_evidence(request: EvidenceRegisterRequest) -> dict[str, Any]:
    ids = [record.id for record in request.records]
    duplicates = sorted([key for key, count in Counter(ids).items() if count > 1])
    missing_hashes = [record.id for record in request.records if not record.content_hash]
    missing_sources = [record.id for record in request.records if not record.source_uri]
    unapproved = [record.id for record in request.records if not record.approved]
    hash_groups: dict[str, list[str]] = defaultdict(list)
    for record in request.records:
        if record.content_hash:
            hash_groups[record.content_hash].append(record.id)
    duplicate_content = [{"contentHash": value, "evidenceIds": sorted(keys)} for value, keys in hash_groups.items() if len(keys) > 1]
    return {
        "ok": not duplicates and not missing_hashes,
        "schema": "sc-workbench-evidence-register/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "recordCount": len(request.records),
        "duplicateIds": duplicates,
        "recordsMissingHash": missing_hashes,
        "recordsMissingSource": missing_sources,
        "unapprovedRecords": unapproved,
        "duplicateContent": duplicate_content,
        "kindCounts": dict(Counter(record.kind for record in request.records)),
        "registerHash": _sha256(request.model_dump()),
    }


@router.post("/readiness/evaluate")
def evaluate_readiness(request: ReadinessRequest) -> dict[str, Any]:
    score_weight = {"not-started": 0.0, "in-progress": 0.5, "complete": 1.0, "blocked": 0.0, "not-applicable": 1.0}
    category_totals: dict[str, list[float]] = defaultdict(list)
    blockers: list[str] = []
    critical_incomplete: list[str] = []
    missing_evidence: list[str] = []
    for item in request.items:
        category_totals[item.category].append(score_weight[item.status])
        if item.status == "blocked":
            blockers.append(item.id)
        if item.critical and item.status not in {"complete", "not-applicable"}:
            critical_incomplete.append(item.id)
        if item.status == "complete" and not item.evidence_ids:
            missing_evidence.append(item.id)
    category_scores = {category: round(sum(values) / len(values) * 100, 4) for category, values in sorted(category_totals.items())}
    overall = sum(score_weight[item.status] for item in request.items) / len(request.items) * 100
    gate = "ready" if not blockers and not critical_incomplete and overall >= 90 else "not-ready"
    return {
        "ok": gate == "ready",
        "schema": "sc-workbench-product-readiness/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "gate": gate,
        "overallPercent": round(overall, 4),
        "categoryScores": category_scores,
        "blockers": blockers,
        "criticalIncompleteItems": critical_incomplete,
        "completeItemsMissingEvidence": missing_evidence,
        "statusCounts": dict(Counter(item.status for item in request.items)),
        "readinessHash": _sha256(request.model_dump()),
    }


@router.post("/snapshot/create")
def create_snapshot(request: SnapshotRequest) -> dict[str, Any]:
    paths = [record.path for record in request.files]
    duplicates = sorted([key for key, count in Counter(paths).items() if count > 1])
    manifest = {
        "projectId": request.project_id,
        "revision": request.revision,
        "previousSnapshotHash": request.previous_snapshot_hash,
        "generatedAt": _now(),
        "files": [record.model_dump() for record in sorted(request.files, key=lambda value: value.path)],
        "metadata": request.metadata,
    }
    return {
        "ok": not duplicates,
        "schema": "sc-workbench-versioned-documentation-snapshot/1.0",
        "version": VERSION,
        "manifest": manifest,
        "duplicatePaths": duplicates,
        "fileCount": len(request.files),
        "totalBytes": sum(record.size_bytes for record in request.files),
        "snapshotHash": _sha256(manifest),
        "chainLinked": bool(request.previous_snapshot_hash),
    }

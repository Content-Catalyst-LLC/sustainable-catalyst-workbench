from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

VERSION = "3.3.0"
EVIDENCE_SCHEMA = "sc-workbench-shared-evidence/1.0"
HANDOFF_SCHEMA = "sc-workbench-platform-handoff/1.0"
COMPATIBILITY_SCHEMA = "sc-workbench-handoff-compatibility/1.0"
BUNDLE_SCHEMA = "sc-workbench-portable-handoff-bundle/1.0"
RECEIPT_SCHEMA = "sc-workbench-handoff-receipt/1.0"
LINK_SCHEMA = "sc-workbench-cross-application-link/1.0"

AppName = Literal[
    "workbench", "site-intelligence", "decision-studio", "research-librarian",
    "knowledge-library", "lab", "external"
]

router = APIRouter(prefix="/v330", tags=["workbench-v330"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _hash(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _slug(value: Any, fallback: str = "record") -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text[:120] or fallback


APP_CAPABILITIES: dict[str, set[str]] = {
    "workbench": {"evidence", "calculations", "models", "datasets", "visualizations", "experiments", "documentation", "project-links"},
    "site-intelligence": {"evidence", "indicators", "maps", "events", "datasets", "sources", "briefs", "project-links"},
    "decision-studio": {"evidence", "decisions", "alternatives", "scenarios", "assumptions", "tradeoffs", "briefs", "project-links"},
    "research-librarian": {"evidence", "questions", "routes", "citations", "sources", "article-links", "project-links"},
    "knowledge-library": {"evidence", "articles", "citations", "formulas", "sources", "article-links", "project-links"},
    "lab": {"evidence", "experiments", "measurements", "datasets", "methods", "documentation", "project-links"},
    "external": {"evidence", "datasets", "sources"},
}

HANDOFF_REQUIRED: dict[str, set[str]] = {
    "site-intelligence-to-workbench": {"evidence", "datasets"},
    "decision-studio-to-workbench": {"evidence", "scenarios"},
    "workbench-to-decision-studio": {"evidence", "calculations"},
    "research-librarian-to-workbench": {"evidence", "routes"},
    "workbench-to-research-librarian": {"evidence", "citations"},
    "workbench-to-site-intelligence": {"evidence", "datasets"},
    "workbench-to-lab": {"evidence", "experiments"},
    "lab-to-workbench": {"evidence", "measurements"},
    "generic": {"evidence"},
}


class EvidenceRecord(BaseModel):
    evidence_id: str = ""
    title: str = ""
    summary: str = ""
    originating_app: AppName = "workbench"
    source_type: str = "record"
    source_url: str = ""
    source_record_id: str = ""
    project_id: str = "default"
    claims: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    data_quality: str = "unreviewed"
    uncertainty: str = "not-recorded"
    freshness: str = "unknown"
    license: str = "not-specified"
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: list[dict[str, Any]] = Field(default_factory=list)


class EvidenceNormalizeRequest(BaseModel):
    evidence: EvidenceRecord


class HandoffRequest(BaseModel):
    source_app: AppName
    target_app: AppName
    project_id: str = "default"
    source_project_id: str = ""
    target_project_id: str = ""
    handoff_type: str = "generic"
    title: str = "Platform handoff"
    objective: str = ""
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    required_capabilities: list[str] = Field(default_factory=list)
    schema_versions: dict[str, str] = Field(default_factory=dict)
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    offline: bool = False


class CompatibilityRequest(BaseModel):
    handoff: HandoffRequest


class BundleRequest(BaseModel):
    handoff: HandoffRequest
    include_evidence: bool = True
    include_payload: bool = True
    include_attachments_manifest: bool = True
    previous_bundle_hash: str = ""


class EvidenceMergeRequest(BaseModel):
    existing: list[EvidenceRecord] = Field(default_factory=list)
    incoming: list[EvidenceRecord] = Field(default_factory=list)


class ReceiptRequest(BaseModel):
    packet_hash: str
    target_app: AppName
    target_record_id: str = ""
    status: Literal["accepted", "accepted-with-warnings", "rejected", "queued"] = "accepted"
    accepted_evidence_ids: list[str] = Field(default_factory=list)
    rejected_evidence_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: str = ""


class ProjectLinkRequest(BaseModel):
    source_app: AppName
    target_app: AppName
    source_project_id: str
    target_project_id: str = ""
    relationship: str = "handoff"
    packet_hash: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


def normalize_evidence(record: EvidenceRecord) -> dict[str, Any]:
    data = record.model_dump()
    data["schema"] = EVIDENCE_SCHEMA
    data["version"] = VERSION
    data["evidence_id"] = _slug(data.get("evidence_id") or data.get("source_record_id") or data.get("title"), "evidence")
    data["project_id"] = _slug(data.get("project_id"), "default")
    data["source_type"] = _slug(data.get("source_type"), "record")
    data["methods"] = sorted({str(item).strip()[:160] for item in data.get("methods", []) if str(item).strip()})
    data["artifact_ids"] = sorted({_slug(item, "artifact") for item in data.get("artifact_ids", []) if str(item).strip()})
    data["citations"] = [dict(item) for item in data.get("citations", [])]
    data["claims"] = [dict(item) for item in data.get("claims", [])]
    provenance = [dict(item) for item in data.get("provenance", [])]
    provenance.append({
        "event": "normalized",
        "application": data["originating_app"],
        "sourceRecordId": data.get("source_record_id", ""),
        "timestamp": _now(),
    })
    data["provenance"] = provenance
    data["normalized_at"] = _now()
    unhashed = dict(data)
    data["evidence_hash"] = _hash(unhashed)
    return data


def compatibility_report(request: CompatibilityRequest) -> dict[str, Any]:
    handoff = request.handoff
    source_caps = APP_CAPABILITIES.get(handoff.source_app, set())
    target_caps = APP_CAPABILITIES.get(handoff.target_app, set())
    required = set(HANDOFF_REQUIRED.get(handoff.handoff_type, HANDOFF_REQUIRED["generic"]))
    required.update(str(item).strip() for item in handoff.required_capabilities if str(item).strip())
    payload_caps = set(str(item).strip() for item in handoff.payload.get("capabilities", []) if str(item).strip())
    supplied = source_caps | payload_caps
    missing_source = sorted(required - supplied)
    missing_target = sorted(required - target_caps)
    warnings: list[str] = []
    if handoff.source_app == handoff.target_app:
        warnings.append("Source and target applications are identical.")
    if not handoff.evidence:
        warnings.append("The handoff contains no shared evidence records.")
    if handoff.offline:
        warnings.append("Live delivery is disabled; export a portable handoff bundle.")
    compatible = not missing_source and not missing_target and handoff.source_app != handoff.target_app
    report = {
        "schema": COMPATIBILITY_SCHEMA,
        "version": VERSION,
        "sourceApp": handoff.source_app,
        "targetApp": handoff.target_app,
        "handoffType": handoff.handoff_type,
        "requiredCapabilities": sorted(required),
        "sourceCapabilities": sorted(source_caps),
        "targetCapabilities": sorted(target_caps),
        "missingFromSource": missing_source,
        "missingFromTarget": missing_target,
        "warnings": warnings,
        "compatible": compatible,
        "recommendedMode": "portable-bundle" if handoff.offline or not compatible else "live-or-portable",
        "checkedAt": _now(),
    }
    report["compatibilityHash"] = _hash(report)
    return report


def build_handoff_packet(request: HandoffRequest) -> dict[str, Any]:
    if request.source_app == request.target_app:
        raise ValueError("source_app and target_app must differ")
    normalized = [normalize_evidence(item) for item in request.evidence]
    evidence_ids = [item["evidence_id"] for item in normalized]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("duplicate evidence_id values are not allowed in one handoff")
    compatibility = compatibility_report(CompatibilityRequest(handoff=request))
    packet = {
        "schema": HANDOFF_SCHEMA,
        "version": VERSION,
        "packetId": _slug(f"{request.source_app}-{request.target_app}-{request.project_id}-{request.title}", "handoff"),
        "createdAt": _now(),
        "sourceApp": request.source_app,
        "targetApp": request.target_app,
        "sourceProjectId": _slug(request.source_project_id or request.project_id, "default"),
        "targetProjectId": _slug(request.target_project_id, "unassigned") if request.target_project_id else "",
        "handoffType": _slug(request.handoff_type, "generic"),
        "title": request.title.strip()[:300],
        "objective": request.objective.strip(),
        "evidence": normalized,
        "evidenceIds": evidence_ids,
        "payload": request.payload,
        "schemaVersions": dict(sorted(request.schema_versions.items())),
        "attachments": [dict(item) for item in request.attachments],
        "deliveryMode": "portable-bundle" if request.offline else "live-or-portable",
        "compatibility": compatibility,
        "reviewState": "human-review-required",
        "scopeBoundary": "Receiving applications must preserve evidence identifiers, provenance, uncertainty, and citations.",
    }
    packet["packetHash"] = _hash(packet)
    return {"ok": True, "schema": HANDOFF_SCHEMA, "version": VERSION, "packet": packet, "packetHash": packet["packetHash"]}


def build_portable_bundle(request: BundleRequest) -> dict[str, Any]:
    packet_result = build_handoff_packet(request.handoff)
    packet = packet_result["packet"]
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "version": VERSION,
        "createdAt": _now(),
        "packetHash": packet["packetHash"],
        "sourceApp": packet["sourceApp"],
        "targetApp": packet["targetApp"],
        "handoffType": packet["handoffType"],
        "previousBundleHash": request.previous_bundle_hash.strip(),
        "files": [
            {"path": "handoff.json", "mediaType": "application/json", "contentHash": packet["packetHash"]},
        ],
        "evidenceCount": len(packet["evidence"]),
        "attachmentCount": len(packet["attachments"]),
        "instructions": [
            "Import handoff.json into a compatible Sustainable Catalyst application.",
            "Verify packetHash before accepting evidence or creating target records.",
            "Preserve evidence IDs and provenance when generating derivative records.",
        ],
    }
    if request.include_evidence:
        manifest["files"].append({"path": "evidence.json", "mediaType": "application/json", "contentHash": _hash(packet["evidence"])})
    if request.include_payload:
        manifest["files"].append({"path": "payload.json", "mediaType": "application/json", "contentHash": _hash(packet["payload"])})
    if request.include_attachments_manifest and packet["attachments"]:
        manifest["files"].append({"path": "attachments-manifest.json", "mediaType": "application/json", "contentHash": _hash(packet["attachments"])})
    manifest["manifestHash"] = _hash(manifest)
    bundle = {"manifest": manifest, "handoff": packet}
    if request.include_evidence:
        bundle["evidence"] = packet["evidence"]
    if request.include_payload:
        bundle["payload"] = packet["payload"]
    if request.include_attachments_manifest:
        bundle["attachments"] = packet["attachments"]
    bundle["bundleHash"] = _hash(bundle)
    return {"ok": True, "schema": BUNDLE_SCHEMA, "version": VERSION, "bundle": bundle, "bundleHash": bundle["bundleHash"]}


def merge_evidence(request: EvidenceMergeRequest) -> dict[str, Any]:
    merged: dict[str, dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    duplicates: list[str] = []
    for origin, records in (("existing", request.existing), ("incoming", request.incoming)):
        for raw in records:
            item = normalize_evidence(raw)
            evidence_id = item["evidence_id"]
            if evidence_id not in merged:
                item["mergeOrigin"] = origin
                merged[evidence_id] = item
                continue
            if merged[evidence_id]["evidence_hash"] == item["evidence_hash"]:
                duplicates.append(evidence_id)
            else:
                conflicts.append({
                    "evidenceId": evidence_id,
                    "existingHash": merged[evidence_id]["evidence_hash"],
                    "incomingHash": item["evidence_hash"],
                    "resolution": "manual-review-required",
                })
    result = {
        "schema": "sc-workbench-evidence-merge/1.0",
        "version": VERSION,
        "merged": list(merged.values()),
        "duplicates": sorted(set(duplicates)),
        "conflicts": conflicts,
        "manualReviewRequired": bool(conflicts),
    }
    result["mergeHash"] = _hash(result)
    return result


def build_receipt(request: ReceiptRequest) -> dict[str, Any]:
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "version": VERSION,
        "receivedAt": _now(),
        "packetHash": request.packet_hash.strip(),
        "targetApp": request.target_app,
        "targetRecordId": request.target_record_id.strip(),
        "status": request.status,
        "acceptedEvidenceIds": sorted(set(request.accepted_evidence_ids)),
        "rejectedEvidenceIds": sorted(set(request.rejected_evidence_ids)),
        "warnings": [str(item).strip() for item in request.warnings if str(item).strip()],
        "notes": request.notes.strip(),
    }
    if not receipt["packetHash"]:
        raise ValueError("packet_hash is required")
    receipt["receiptHash"] = _hash(receipt)
    return {"ok": True, "schema": RECEIPT_SCHEMA, "version": VERSION, "receipt": receipt, "receiptHash": receipt["receiptHash"]}


def build_project_link(request: ProjectLinkRequest) -> dict[str, Any]:
    if request.source_app == request.target_app:
        raise ValueError("source_app and target_app must differ")
    link = {
        "schema": LINK_SCHEMA,
        "version": VERSION,
        "createdAt": _now(),
        "sourceApp": request.source_app,
        "targetApp": request.target_app,
        "sourceProjectId": _slug(request.source_project_id, "default"),
        "targetProjectId": _slug(request.target_project_id, "unassigned") if request.target_project_id else "",
        "relationship": _slug(request.relationship, "handoff"),
        "packetHash": request.packet_hash.strip(),
        "metadata": request.metadata,
    }
    link["linkId"] = _slug(f"{link['sourceApp']}-{link['sourceProjectId']}-{link['targetApp']}-{link['targetProjectId'] or 'unassigned'}", "link")
    link["linkHash"] = _hash(link)
    return {"ok": True, "schema": LINK_SCHEMA, "version": VERSION, "link": link, "linkHash": link["linkHash"]}


@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "schema": HANDOFF_SCHEMA,
        "applications": sorted(APP_CAPABILITIES),
        "capabilities": [
            "shared-evidence-normalization", "platform-handoff-packets", "compatibility-reports",
            "portable-handoff-bundles", "evidence-merge-conflicts", "target-receipts", "cross-application-links",
        ],
    }


@router.post("/evidence/normalize")
def evidence_normalize(request: EvidenceNormalizeRequest) -> dict[str, Any]:
    try:
        evidence = normalize_evidence(request.evidence)
        return {"ok": True, "schema": EVIDENCE_SCHEMA, "version": VERSION, "evidence": evidence, "evidenceHash": evidence["evidence_hash"]}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/handoff/build")
def handoff_build(request: HandoffRequest) -> dict[str, Any]:
    try:
        return build_handoff_packet(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/handoff/validate")
def handoff_validate(request: CompatibilityRequest) -> dict[str, Any]:
    return {"ok": True, "schema": COMPATIBILITY_SCHEMA, "version": VERSION, "report": compatibility_report(request)}


@router.post("/bundle/build")
def bundle_build(request: BundleRequest) -> dict[str, Any]:
    try:
        return build_portable_bundle(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/evidence/merge")
def evidence_merge(request: EvidenceMergeRequest) -> dict[str, Any]:
    return {"ok": True, **merge_evidence(request)}


@router.post("/receipt/build")
def receipt_build(request: ReceiptRequest) -> dict[str, Any]:
    try:
        return build_receipt(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/project-link/build")
def project_link_build(request: ProjectLinkRequest) -> dict[str, Any]:
    try:
        return build_project_link(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

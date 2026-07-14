"""Workbench v4.3.0 — Live Data Connectors and Reproducible Dataset Pipelines."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "4.3.0"
EXPECTED_STUDIOS = 25
router = APIRouter(prefix="/v430", tags=["workbench-v430"])

ConnectorType = Literal["https-json", "https-csv", "wordpress-rest", "site-intelligence", "local-file", "manual-snapshot"]
PipelineOperation = Literal["select", "rename", "filter", "derive", "deduplicate", "sort", "aggregate", "join", "unit-convert"]


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def slug(value: str, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned or fallback


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SourceInput(BaseModel):
    sourceId: str = ""
    title: str
    connectorType: ConnectorType
    url: Optional[str] = None
    license: str = "unknown"
    citation: str = ""
    refreshMinutes: int = Field(default=1440, ge=1, le=525600)
    allowedHosts: List[str] = Field(default_factory=list)
    containsSecrets: bool = False


class ConnectorPlanInput(BaseModel):
    source: SourceInput
    requestedFields: List[str] = Field(default_factory=list)
    query: Dict[str, Any] = Field(default_factory=dict)
    previousEtag: Optional[str] = None
    previousLastModified: Optional[str] = None


class ConnectorHealthInput(BaseModel):
    sourceId: str
    checkedAt: str = ""
    statusCode: Optional[int] = None
    latencyMs: Optional[float] = None
    recordsReceived: int = Field(default=0, ge=0)
    error: str = ""
    etag: str = ""
    lastModified: str = ""


class DatasetManifestInput(BaseModel):
    datasetId: str = ""
    title: str
    sourceIds: List[str]
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    rowCount: int = Field(default=0, ge=0)
    generatedAt: str = ""
    observedAt: str = ""
    license: str = "unknown"
    recordsHash: str = ""
    notes: List[str] = Field(default_factory=list)


class PipelineStep(BaseModel):
    stepId: str
    operation: PipelineOperation
    params: Dict[str, Any] = Field(default_factory=dict)
    dependsOn: List[str] = Field(default_factory=list)


class PipelineInput(BaseModel):
    pipelineId: str = ""
    datasetId: str
    steps: List[PipelineStep]
    language: Literal["python", "r", "javascript", "rust", "sql", "declarative"] = "declarative"


class ValidationInput(BaseModel):
    records: List[Dict[str, Any]]
    schemaFields: List[Dict[str, Any]] = Field(default_factory=list)
    primaryKey: str = ""
    allowAdditionalFields: bool = True


class FreshnessInput(BaseModel):
    observedAt: str
    evaluatedAt: str = ""
    maxAgeSeconds: int = Field(default=86400, ge=1)


class CacheInput(BaseModel):
    sourceId: str
    ttlSeconds: int = Field(default=3600, ge=60)
    etag: str = ""
    lastModified: str = ""
    offlineSnapshot: bool = True
    staleWhileRevalidateSeconds: int = Field(default=86400, ge=0)


class RefreshInput(BaseModel):
    sourceIds: List[str]
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    requestedAt: str = ""
    force: bool = False


class SnapshotInput(BaseModel):
    manifest: Dict[str, Any]
    records: List[Dict[str, Any]]
    createdAt: str = ""


class ProvenanceInput(BaseModel):
    datasetId: str
    sourceRecords: List[Dict[str, Any]]
    transformationRecords: List[Dict[str, Any]] = Field(default_factory=list)
    validationRecords: List[Dict[str, Any]] = Field(default_factory=list)
    outputRecords: List[Dict[str, Any]] = Field(default_factory=list)


class PackageInput(BaseModel):
    manifest: Dict[str, Any]
    pipeline: Dict[str, Any]
    provenance: Dict[str, Any]
    validation: Dict[str, Any]
    snapshots: List[Dict[str, Any]] = Field(default_factory=list)


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-live-data-status/1.0",
        "version": VERSION,
        "expectedStudioCount": EXPECTED_STUDIOS,
        "connectorTypes": ["https-json", "https-csv", "wordpress-rest", "site-intelligence", "local-file", "manual-snapshot"],
        "pipelineOperations": ["select", "rename", "filter", "derive", "deduplicate", "sort", "aggregate", "join", "unit-convert"],
        "browserFallback": True,
        "offlineSnapshots": True,
        "privateByDefault": True,
        "paidExternalDatabaseRequired": False,
        "automaticNetworkFetchAuthorized": False,
        "automaticCredentialStorageAuthorized": False,
        "automaticCloudUploadAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticDeletionAuthorized": False,
    }


def normalize_source(source: SourceInput) -> Dict[str, Any]:
    data = source.model_dump()
    source_id = slug(source.sourceId or source.title, "data-source")
    findings: List[Dict[str, str]] = []
    parsed = urlparse(source.url or "")
    network_type = source.connectorType in {"https-json", "https-csv", "wordpress-rest", "site-intelligence"}
    if network_type:
        if parsed.scheme != "https":
            findings.append({"level": "block", "code": "https-required", "message": "Network connectors require an HTTPS URL."})
        if not parsed.hostname:
            findings.append({"level": "block", "code": "host-required", "message": "Network connectors require a valid hostname."})
        allowed = {h.lower().strip() for h in source.allowedHosts if h.strip()}
        if allowed and parsed.hostname and parsed.hostname.lower() not in allowed:
            findings.append({"level": "block", "code": "host-not-allowlisted", "message": "Connector hostname is not in the source allowlist."})
    if source.containsSecrets:
        findings.append({"level": "block", "code": "embedded-secret", "message": "Connector definitions must not contain credentials or secrets."})
    if source.license.lower() == "unknown":
        findings.append({"level": "review", "code": "license-unknown", "message": "Confirm dataset license and reuse terms before publication."})
    record = {
        "schema": "sc-workbench-data-source/1.0",
        "version": VERSION,
        "sourceId": source_id,
        "title": source.title.strip(),
        "connectorType": source.connectorType,
        "url": source.url,
        "license": source.license,
        "citation": source.citation,
        "refreshMinutes": source.refreshMinutes,
        "allowedHosts": sorted(set(source.allowedHosts)),
        "findings": findings,
        "ready": not any(item["level"] == "block" for item in findings),
        "privateByDefault": True,
        "automaticNetworkFetchAuthorized": False,
        "automaticCredentialStorageAuthorized": False,
    }
    record["sourceHash"] = content_hash({k: v for k, v in record.items() if k != "sourceHash"})
    return record


def connector_plan(payload: ConnectorPlanInput) -> Dict[str, Any]:
    source = normalize_source(payload.source)
    conditional_headers = {}
    if payload.previousEtag:
        conditional_headers["If-None-Match"] = payload.previousEtag
    if payload.previousLastModified:
        conditional_headers["If-Modified-Since"] = payload.previousLastModified
    plan = {
        "schema": "sc-workbench-connector-plan/1.0",
        "version": VERSION,
        "source": source,
        "requestedFields": sorted(set(payload.requestedFields)),
        "query": payload.query,
        "conditionalHeaders": conditional_headers,
        "networkMethod": "GET" if source["connectorType"] not in {"local-file", "manual-snapshot"} else "LOCAL_READ",
        "requiresExplicitExecution": True,
        "requiresHostAllowlist": source["connectorType"] not in {"local-file", "manual-snapshot"},
        "automaticNetworkFetchAuthorized": False,
        "automaticCredentialStorageAuthorized": False,
        "ready": source["ready"],
    }
    plan["planHash"] = content_hash({k: v for k, v in plan.items() if k != "planHash"})
    return plan


def connector_health(payload: ConnectorHealthInput) -> Dict[str, Any]:
    checked = payload.checkedAt or utc_now()
    status = "unknown"
    if payload.error:
        status = "unavailable"
    elif payload.statusCode == 304:
        status = "not-modified"
    elif payload.statusCode is not None and 200 <= payload.statusCode < 300:
        status = "healthy"
    elif payload.statusCode is not None:
        status = "degraded"
    findings = []
    if payload.latencyMs is not None and payload.latencyMs > 5000:
        findings.append({"level": "review", "code": "high-latency", "message": "Connector latency exceeds five seconds."})
    if status in {"unavailable", "degraded"}:
        findings.append({"level": "block", "code": "connector-failure", "message": payload.error or f"Connector returned HTTP {payload.statusCode}."})
    record = {
        "schema": "sc-workbench-connector-health/1.0",
        "version": VERSION,
        "sourceId": slug(payload.sourceId, "data-source"),
        "checkedAt": checked,
        "status": status,
        "statusCode": payload.statusCode,
        "latencyMs": payload.latencyMs,
        "recordsReceived": payload.recordsReceived,
        "etag": payload.etag,
        "lastModified": payload.lastModified,
        "findings": findings,
    }
    record["healthHash"] = content_hash({k: v for k, v in record.items() if k != "healthHash"})
    return record


def dataset_manifest(payload: DatasetManifestInput) -> Dict[str, Any]:
    dataset_id = slug(payload.datasetId or payload.title, "dataset")
    generated = payload.generatedAt or utc_now()
    columns = sorted(payload.columns, key=lambda item: str(item.get("name", "")))
    record = {
        "schema": "sc-workbench-dataset-manifest/1.0",
        "version": VERSION,
        "datasetId": dataset_id,
        "title": payload.title.strip(),
        "sourceIds": sorted(set(payload.sourceIds)),
        "columns": columns,
        "rowCount": payload.rowCount,
        "generatedAt": generated,
        "observedAt": payload.observedAt or generated,
        "license": payload.license,
        "recordsHash": payload.recordsHash,
        "notes": payload.notes,
        "reproducible": bool(payload.sourceIds and columns),
        "automaticPublicationAuthorized": False,
    }
    record["manifestHash"] = content_hash({k: v for k, v in record.items() if k != "manifestHash"})
    return record


def pipeline_plan(payload: PipelineInput) -> Dict[str, Any]:
    ids = [step.stepId for step in payload.steps]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    known = set(ids)
    missing_dependencies = sorted({dep for step in payload.steps for dep in step.dependsOn if dep not in known})
    cycle = False
    graph = {step.stepId: list(step.dependsOn) for step in payload.steps}
    visiting, visited = set(), set()
    def visit(node: str) -> None:
        nonlocal cycle
        if node in visiting:
            cycle = True
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in graph.get(node, []):
            visit(dep)
        visiting.remove(node)
        visited.add(node)
    for node in graph:
        visit(node)
    findings = []
    if duplicates:
        findings.append({"level": "block", "code": "duplicate-step", "items": duplicates})
    if missing_dependencies:
        findings.append({"level": "block", "code": "missing-dependency", "items": missing_dependencies})
    if cycle:
        findings.append({"level": "block", "code": "dependency-cycle"})
    steps = [step.model_dump() for step in payload.steps]
    record = {
        "schema": "sc-workbench-dataset-pipeline/1.0",
        "version": VERSION,
        "pipelineId": slug(payload.pipelineId or f"{payload.datasetId}-pipeline", "dataset-pipeline"),
        "datasetId": slug(payload.datasetId, "dataset"),
        "language": payload.language,
        "steps": steps,
        "findings": findings,
        "ready": not findings,
        "requiresExplicitExecution": True,
        "automaticExecutionAuthorized": False,
        "automaticOverwriteAuthorized": False,
    }
    record["pipelineHash"] = content_hash({k: v for k, v in record.items() if k != "pipelineHash"})
    return record


def validate_dataset(payload: ValidationInput) -> Dict[str, Any]:
    required = [str(item.get("name")) for item in payload.schemaFields if item.get("required") and item.get("name")]
    allowed = {str(item.get("name")) for item in payload.schemaFields if item.get("name")}
    errors: List[Dict[str, Any]] = []
    seen = set()
    duplicate_keys = []
    for index, row in enumerate(payload.records):
        missing = [name for name in required if name not in row or row.get(name) in (None, "")]
        if missing:
            errors.append({"row": index, "code": "missing-required", "fields": missing})
        if not payload.allowAdditionalFields and allowed:
            extra = sorted(set(row) - allowed)
            if extra:
                errors.append({"row": index, "code": "unexpected-fields", "fields": extra})
        if payload.primaryKey:
            value = row.get(payload.primaryKey)
            if value in seen:
                duplicate_keys.append(value)
            seen.add(value)
    if duplicate_keys:
        errors.append({"code": "duplicate-primary-key", "values": sorted(set(map(str, duplicate_keys)))})
    report = {
        "schema": "sc-workbench-dataset-validation/1.0",
        "version": VERSION,
        "rowCount": len(payload.records),
        "errorCount": len(errors),
        "errors": errors,
        "valid": not errors,
        "automaticRecordDeletionAuthorized": False,
        "automaticCorrectionAuthorized": False,
    }
    report["validationHash"] = content_hash({k: v for k, v in report.items() if k != "validationHash"})
    return report


def freshness_report(payload: FreshnessInput) -> Dict[str, Any]:
    evaluated = datetime.fromisoformat((payload.evaluatedAt or utc_now()).replace("Z", "+00:00"))
    observed = datetime.fromisoformat(payload.observedAt.replace("Z", "+00:00"))
    age = max(0, int((evaluated - observed).total_seconds()))
    if age <= payload.maxAgeSeconds:
        state = "fresh"
    elif age <= payload.maxAgeSeconds * 2:
        state = "stale"
    else:
        state = "expired"
    return {
        "schema": "sc-workbench-dataset-freshness/1.0",
        "version": VERSION,
        "observedAt": payload.observedAt,
        "evaluatedAt": evaluated.isoformat(),
        "ageSeconds": age,
        "maxAgeSeconds": payload.maxAgeSeconds,
        "state": state,
        "refreshRecommended": state != "fresh",
        "automaticRefreshAuthorized": False,
    }


def cache_plan(payload: CacheInput) -> Dict[str, Any]:
    record = {
        "schema": "sc-workbench-dataset-cache-plan/1.0",
        "version": VERSION,
        "sourceId": slug(payload.sourceId, "data-source"),
        "ttlSeconds": payload.ttlSeconds,
        "staleWhileRevalidateSeconds": payload.staleWhileRevalidateSeconds,
        "etag": payload.etag,
        "lastModified": payload.lastModified,
        "offlineSnapshot": payload.offlineSnapshot,
        "conditionalRequest": bool(payload.etag or payload.lastModified),
        "automaticCacheDeletionAuthorized": False,
        "automaticNetworkRefreshAuthorized": False,
    }
    record["cachePlanHash"] = content_hash({k: v for k, v in record.items() if k != "cachePlanHash"})
    return record


def refresh_plan(payload: RefreshInput) -> Dict[str, Any]:
    source_ids = list(dict.fromkeys(slug(item, "data-source") for item in payload.sourceIds))
    dependencies = {slug(k, "data-source"): [slug(v, "data-source") for v in values] for k, values in payload.dependencies.items()}
    order: List[str] = []
    temporary, permanent = set(), set()
    cycle = False
    def visit(node: str) -> None:
        nonlocal cycle
        if node in permanent:
            return
        if node in temporary:
            cycle = True
            return
        temporary.add(node)
        for dep in dependencies.get(node, []):
            if dep in source_ids:
                visit(dep)
        temporary.remove(node)
        permanent.add(node)
        order.append(node)
    for source_id in source_ids:
        visit(source_id)
    record = {
        "schema": "sc-workbench-dataset-refresh-plan/1.0",
        "version": VERSION,
        "requestedAt": payload.requestedAt or utc_now(),
        "sourceIds": source_ids,
        "dependencies": dependencies,
        "refreshOrder": order,
        "force": payload.force,
        "dependencyCycle": cycle,
        "ready": not cycle,
        "requiresExplicitExecution": True,
        "automaticNetworkFetchAuthorized": False,
    }
    record["refreshPlanHash"] = content_hash({k: v for k, v in record.items() if k != "refreshPlanHash"})
    return record


def build_snapshot(payload: SnapshotInput) -> Dict[str, Any]:
    record_hashes = [content_hash(item) for item in payload.records]
    snapshot = {
        "schema": "sc-workbench-offline-dataset-snapshot/1.0",
        "version": VERSION,
        "createdAt": payload.createdAt or utc_now(),
        "manifest": payload.manifest,
        "recordCount": len(payload.records),
        "recordHashes": record_hashes,
        "recordsHash": content_hash(record_hashes),
        "records": payload.records,
        "portable": True,
        "requiresExplicitImport": True,
        "automaticCloudUploadAuthorized": False,
    }
    snapshot["snapshotHash"] = content_hash({k: v for k, v in snapshot.items() if k != "snapshotHash"})
    return snapshot


def build_provenance(payload: ProvenanceInput) -> Dict[str, Any]:
    record = {
        "schema": "sc-workbench-data-provenance/1.0",
        "version": VERSION,
        "datasetId": slug(payload.datasetId, "dataset"),
        "sources": payload.sourceRecords,
        "transformations": payload.transformationRecords,
        "validations": payload.validationRecords,
        "outputs": payload.outputRecords,
        "sourceCount": len(payload.sourceRecords),
        "transformationCount": len(payload.transformationRecords),
        "validationCount": len(payload.validationRecords),
        "complete": bool(payload.sourceRecords and payload.outputRecords),
        "humanReviewRequired": True,
        "automaticClaimApprovalAuthorized": False,
    }
    record["provenanceHash"] = content_hash({k: v for k, v in record.items() if k != "provenanceHash"})
    return record


def build_package(payload: PackageInput) -> Dict[str, Any]:
    components = {
        "manifest": payload.manifest,
        "pipeline": payload.pipeline,
        "provenance": payload.provenance,
        "validation": payload.validation,
        "snapshots": payload.snapshots,
    }
    record = {
        "schema": "sc-workbench-reproducible-dataset-package/1.0",
        "version": VERSION,
        "createdAt": utc_now(),
        "components": components,
        "componentHashes": {key: content_hash(value) for key, value in components.items()},
        "portable": True,
        "requiresExplicitImport": True,
        "requiresHumanReview": True,
        "secretsIncluded": False,
        "automaticPublicationAuthorized": False,
        "automaticCloudUploadAuthorized": False,
        "automaticExecutionAuthorized": False,
    }
    record["packageHash"] = content_hash({k: v for k, v in record.items() if k != "packageHash"})
    return record


@router.get("/status")
def status_route() -> Dict[str, Any]:
    return status_record()

@router.post("/source/normalize")
def source_route(payload: SourceInput) -> Dict[str, Any]:
    return normalize_source(payload)

@router.post("/connector/plan")
def connector_plan_route(payload: ConnectorPlanInput) -> Dict[str, Any]:
    return connector_plan(payload)

@router.post("/connector/health")
def connector_health_route(payload: ConnectorHealthInput) -> Dict[str, Any]:
    return connector_health(payload)

@router.post("/dataset/manifest")
def manifest_route(payload: DatasetManifestInput) -> Dict[str, Any]:
    return dataset_manifest(payload)

@router.post("/pipeline/plan")
def pipeline_route(payload: PipelineInput) -> Dict[str, Any]:
    return pipeline_plan(payload)

@router.post("/dataset/validate")
def validation_route(payload: ValidationInput) -> Dict[str, Any]:
    return validate_dataset(payload)

@router.post("/freshness/evaluate")
def freshness_route(payload: FreshnessInput) -> Dict[str, Any]:
    return freshness_report(payload)

@router.post("/cache/plan")
def cache_route(payload: CacheInput) -> Dict[str, Any]:
    return cache_plan(payload)

@router.post("/refresh/plan")
def refresh_route(payload: RefreshInput) -> Dict[str, Any]:
    return refresh_plan(payload)

@router.post("/snapshot/build")
def snapshot_route(payload: SnapshotInput) -> Dict[str, Any]:
    return build_snapshot(payload)

@router.post("/provenance/build")
def provenance_route(payload: ProvenanceInput) -> Dict[str, Any]:
    return build_provenance(payload)

@router.post("/package/build")
def package_route(payload: PackageInput) -> Dict[str, Any]:
    return build_package(payload)

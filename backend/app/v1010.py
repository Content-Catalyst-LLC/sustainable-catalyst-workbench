"""Workbench v10.1.0 — Model & Dataset Registry.

Immutable, content-addressed model and dataset version records for AI engineering.
The registry captures artifact/data hashes, licenses, provenance, compatibility metadata,
evaluation state, searchable catalogs, and explicit immutable bindings to v10 AI
engineering experiments.

The registry does not download models or datasets, launch training/inference, mutate
existing v10.0 experiments, select preferred models/datasets, infer scientific validity,
or automatically create governed Platform Core objects.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v1000 import AIProvider, AITask, DatasetRole, load_experiment

VERSION = APP_VERSION
SCHEMA = "sc-workbench-model-dataset-registry/1.0"
MODEL_SCHEMA = "sc-workbench-model-registry-record/1.0"
DATASET_SCHEMA = "sc-workbench-dataset-registry-record/1.0"
SEARCH_SCHEMA = "sc-workbench-ai-registry-search/1.0"
BINDING_SCHEMA = "sc-workbench-ai-experiment-registry-binding/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-ai-registry-core-plan/1.0"
router = APIRouter(tags=["workbench-v1010-model-dataset-registry"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
RegistryKind = Literal["model", "dataset", "experiment-binding"]
EvaluationStatus = Literal["not-evaluated", "evaluation-planned", "evaluated", "reviewed"]
DatasetFormat = Literal[
    "json", "jsonl", "csv", "parquet", "arrow", "sqlite", "numpy", "image-folder",
    "text", "binary", "remote-reference", "custom"
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


def _project_root(project_key: str) -> Path:
    return _store_root() / "ai-model-dataset-registry" / _stable_id(project_key)


def _kind_dir(project_key: str, kind: RegistryKind) -> Path:
    name = {"model": "models", "dataset": "datasets", "experiment-binding": "experiment-bindings"}[kind]
    return _project_root(project_key) / name


def _record_path(project_key: str, kind: RegistryKind, record_hash: str) -> Path:
    return _kind_dir(project_key, kind) / f"{record_hash}.json"


class RegistryCompatibility(BaseModel):
    runtimeKinds: List[str] = Field(default_factory=list, max_length=32)
    frameworks: List[str] = Field(default_factory=list, max_length=32)
    acceleratorKinds: List[str] = Field(default_factory=list, max_length=32)
    dataFormats: List[str] = Field(default_factory=list, max_length=32)
    pythonSpec: str = Field(default="", max_length=160)
    architecture: str = Field(default="", max_length=160)
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("runtimeKinds", "frameworks", "acceleratorKinds", "dataFormats"):
            setattr(self, attr, sorted({str(x).strip() for x in getattr(self, attr) if str(x).strip()}))
        self.pythonSpec = self.pythonSpec.strip()
        self.architecture = self.architecture.strip()
        return self


class EvaluationState(BaseModel):
    status: EvaluationStatus = "not-evaluated"
    evaluationRefs: List[str] = Field(default_factory=list, max_length=100)
    metrics: Dict[str, float] = Field(default_factory=dict)
    notes: str = Field(default="", max_length=6000)

    @model_validator(mode="after")
    def normalize(self):
        self.evaluationRefs = sorted({x.strip() for x in self.evaluationRefs if x.strip()})
        if self.status in {"evaluated", "reviewed"} and not (self.evaluationRefs or self.metrics):
            raise ValueError("evaluated/reviewed status requires evaluationRefs or metrics")
        return self


class ModelRegistryRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    modelKey: str = Field(min_length=1, max_length=160)
    versionLabel: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    provider: AIProvider = "local"
    modelId: str = Field(min_length=1, max_length=500)
    task: AITask = "custom"
    artifactHash: str = Field(default="", max_length=64)
    sourceRevision: str = Field(default="", max_length=255)
    sourceUri: str = Field(default="", max_length=1000)
    license: str = Field(default="", max_length=500)
    licenseUri: str = Field(default="", max_length=1000)
    compatibility: RegistryCompatibility = Field(default_factory=RegistryCompatibility)
    evaluation: EvaluationState = Field(default_factory=EvaluationState)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list, max_length=64)
    notes: str = Field(default="", max_length=12000)
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("projectKey", "modelKey", "versionLabel", "title", "modelId", "sourceRevision", "sourceUri", "license", "licenseUri"):
            setattr(self, attr, getattr(self, attr).strip())
        self.artifactHash = self.artifactHash.strip().lower()
        if self.artifactHash and not _is_hash(self.artifactHash):
            raise ValueError("artifactHash must be a 64-character hexadecimal SHA-256 hash")
        if not self.artifactHash and not (self.sourceRevision or self.sourceUri):
            raise ValueError("model record requires artifactHash or a sourceRevision/sourceUri")
        self.tags = sorted({x.strip() for x in self.tags if x.strip()})
        return self


class DatasetRegistryRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    datasetKey: str = Field(min_length=1, max_length=160)
    versionLabel: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    datasetHash: str = Field(min_length=64, max_length=64)
    datasetRef: str = Field(min_length=1, max_length=1000)
    format: DatasetFormat = "custom"
    schemaRef: str = Field(default="", max_length=1000)
    rowCount: Optional[int] = Field(default=None, ge=0)
    columnCount: Optional[int] = Field(default=None, ge=0)
    splitDefinitions: Dict[str, Any] = Field(default_factory=dict)
    license: str = Field(default="", max_length=500)
    licenseUri: str = Field(default="", max_length=1000)
    compatibility: RegistryCompatibility = Field(default_factory=RegistryCompatibility)
    evaluation: EvaluationState = Field(default_factory=EvaluationState)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list, max_length=64)
    notes: str = Field(default="", max_length=12000)
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("projectKey", "datasetKey", "versionLabel", "title", "datasetRef", "schemaRef", "license", "licenseUri"):
            setattr(self, attr, getattr(self, attr).strip())
        self.datasetHash = self.datasetHash.strip().lower()
        if not _is_hash(self.datasetHash):
            raise ValueError("datasetHash must be a 64-character hexadecimal SHA-256 hash")
        self.tags = sorted({x.strip() for x in self.tags if x.strip()})
        return self


class RegistrySearchRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    query: str = Field(default="", max_length=500)
    kinds: List[Literal["model", "dataset"]] = Field(default_factory=lambda: ["model", "dataset"], max_length=2)
    tags: List[str] = Field(default_factory=list, max_length=32)
    provider: str = Field(default="", max_length=160)
    task: str = Field(default="", max_length=160)
    license: str = Field(default="", max_length=500)
    evaluationStatus: str = Field(default="", max_length=80)
    limit: int = Field(default=100, ge=1, le=500)


class DatasetRegistryBinding(BaseModel):
    role: DatasetRole
    datasetRecordHash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_hash(self):
        self.datasetRecordHash = self.datasetRecordHash.lower()
        if not _is_hash(self.datasetRecordHash):
            raise ValueError("datasetRecordHash must be a SHA-256 hash")
        return self


class ExperimentBindingRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    experimentHash: str = Field(min_length=64, max_length=64)
    modelRecordHash: str = Field(min_length=64, max_length=64)
    datasets: List[DatasetRegistryBinding] = Field(default_factory=list, max_length=100)
    createdBy: str = Field(default="workbench", max_length=160)
    notes: str = Field(default="", max_length=8000)

    @model_validator(mode="after")
    def validate_hashes(self):
        self.experimentHash = self.experimentHash.lower()
        self.modelRecordHash = self.modelRecordHash.lower()
        if not _is_hash(self.experimentHash) or not _is_hash(self.modelRecordHash):
            raise ValueError("experimentHash and modelRecordHash must be SHA-256 hashes")
        keys = [(x.role, x.datasetRecordHash) for x in self.datasets]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate dataset registry binding")
        return self


class RegistryCorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    kind: RegistryKind
    recordHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def validate_hash(self):
        self.recordHash = self.recordHash.lower()
        if not _is_hash(self.recordHash):
            raise ValueError("recordHash must be a SHA-256 hash")
        return self


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Model & Dataset Registry",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "modelSchema": MODEL_SCHEMA,
        "datasetSchema": DATASET_SCHEMA,
        "bindingSchema": BINDING_SCHEMA,
        "capabilities": {
            "modelDatasetRegistry": True,
            "immutableVersionedModelRecords": True,
            "immutableVersionedDatasetRecords": True,
            "contentAddressedRegistryRecords": True,
            "artifactAndDatasetHashTracking": True,
            "licenseAndProvenanceMetadata": True,
            "compatibilityMetadata": True,
            "neutralEvaluationState": True,
            "registrySearchAndListing": True,
            "immutableAIExperimentRegistryBindings": True,
            "versionCollisionProtection": True,
            "platformCoreRegistryPlanning": True,
        },
        "boundaries": {
            "automaticModelDownload": False,
            "automaticDatasetDownload": False,
            "automaticTrainingExecution": False,
            "automaticInferenceExecution": False,
            "automaticRegistryReplacement": False,
            "automaticLatestVersionSelection": False,
            "automaticPreferredModelSelection": False,
            "automaticPreferredDatasetSelection": False,
            "automaticScientificInterpretation": False,
            "scientificValidityInferred": False,
            "automaticExperimentMutation": False,
            "automaticCoreDispatch": False,
            "automaticCorePersistence": False,
            "governedCoreObjectCreated": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _canonical_model(req: ModelRegistryRequest) -> Dict[str, Any]:
    p = req.model_dump(mode="json")
    p.pop("createdBy", None)
    p["tags"] = sorted(set(p.get("tags") or []))
    return p


def _canonical_dataset(req: DatasetRegistryRequest) -> Dict[str, Any]:
    p = req.model_dump(mode="json")
    p.pop("createdBy", None)
    p["tags"] = sorted(set(p.get("tags") or []))
    return p


def _find_version_collision(project_key: str, kind: Literal["model", "dataset"], key: str, version_label: str, record_hash: str) -> Optional[Dict[str, Any]]:
    root = _kind_dir(project_key, kind)
    if not root.exists():
        return None
    key_field = "modelKey" if kind == "model" else "datasetKey"
    for path in root.glob("*.json"):
        try:
            row = _json_read(path)
            if row.get(key_field) == key and row.get("versionLabel") == version_label and row.get("recordHash") != record_hash:
                return row
        except Exception:
            continue
    return None


def _save_versioned_record(project_key: str, kind: Literal["model", "dataset"], schema: str, canonical: Dict[str, Any], created_by: str) -> Dict[str, Any]:
    record_hash = content_hash({"schema": schema, "record": canonical})
    key_field = "modelKey" if kind == "model" else "datasetKey"
    collision = _find_version_collision(project_key, kind, canonical[key_field], canonical["versionLabel"], record_hash)
    if collision:
        raise HTTPException(status_code=409, detail=f"{kind} key/version already exists with different immutable content")
    path = _record_path(project_key, kind, record_hash)
    idempotent = path.exists()
    if not idempotent:
        record = {
            "ok": True, "schema": schema, "version": VERSION, "recordKind": kind,
            "recordHash": record_hash, "recordRef": f"sc://workbench/ai-registry/{kind}/{record_hash}",
            **canonical, "createdAt": _now(), "createdBy": created_by,
            "immutability": {"contentAddressed": True, "replacementAllowed": False, "versionCollisionProtected": True},
            "scientificValidityInferred": False,
        }
        _atomic_json_write(path, record)
    else:
        record = _load_record(project_key, kind, record_hash)
    return {**record, "idempotent": idempotent}


def save_model(req: ModelRegistryRequest) -> Dict[str, Any]:
    return _save_versioned_record(req.projectKey, "model", MODEL_SCHEMA, _canonical_model(req), req.createdBy)


def save_dataset(req: DatasetRegistryRequest) -> Dict[str, Any]:
    return _save_versioned_record(req.projectKey, "dataset", DATASET_SCHEMA, _canonical_dataset(req), req.createdBy)


def _load_record(project_key: str, kind: RegistryKind, record_hash: str) -> Dict[str, Any]:
    if not _is_hash(record_hash):
        raise HTTPException(status_code=422, detail="invalid registry record hash")
    path = _record_path(project_key, kind, record_hash.lower())
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{kind} registry record not found")
    row = _json_read(path)
    if kind == "model":
        canonical = {k: row.get(k) for k in ModelRegistryRequest.model_fields if k != "createdBy"}
        expected = content_hash({"schema": MODEL_SCHEMA, "record": canonical})
    elif kind == "dataset":
        canonical = {k: row.get(k) for k in DatasetRegistryRequest.model_fields if k != "createdBy"}
        expected = content_hash({"schema": DATASET_SCHEMA, "record": canonical})
    else:
        canonical = row.get("binding") or {}
        expected = content_hash({"schema": BINDING_SCHEMA, "binding": canonical})
    if row.get("recordHash") != expected:
        raise HTTPException(status_code=409, detail=f"{kind} registry record integrity failure")
    return row


def _list_records(project_key: str, kind: Literal["model", "dataset"]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    root = _kind_dir(project_key, kind)
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                r = _load_record(project_key, kind, path.stem)
                rows.append({
                    "recordHash": r["recordHash"], "recordRef": r["recordRef"],
                    "key": r.get("modelKey") if kind == "model" else r.get("datasetKey"),
                    "versionLabel": r.get("versionLabel"), "title": r.get("title"),
                    "provider": r.get("provider"), "task": r.get("task"), "format": r.get("format"),
                    "license": r.get("license"), "evaluationStatus": (r.get("evaluation") or {}).get("status"),
                    "tags": r.get("tags") or [], "createdAt": r.get("createdAt"),
                })
            except Exception:
                rows.append({"recordHash": path.stem, "integrityError": True})
    rows.sort(key=lambda x: (str(x.get("key") or ""), str(x.get("versionLabel") or ""), str(x.get("recordHash") or "")))
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key,
            "kind": kind, "recordCount": len(rows), "records": rows}


def search_registry(req: RegistrySearchRequest) -> Dict[str, Any]:
    q = req.query.strip().lower()
    required_tags = {x.strip().lower() for x in req.tags if x.strip()}
    results: List[Dict[str, Any]] = []
    for kind in req.kinds:
        listing = _list_records(req.projectKey, kind)
        for item in listing["records"]:
            if item.get("integrityError"):
                continue
            full = _load_record(req.projectKey, kind, item["recordHash"])
            haystack = " ".join(str(x) for x in [full.get("title"), full.get("modelKey"), full.get("datasetKey"), full.get("modelId"), full.get("versionLabel"), full.get("notes"), " ".join(full.get("tags") or [])]).lower()
            if q and q not in haystack:
                continue
            tags = {str(x).lower() for x in full.get("tags") or []}
            if required_tags and not required_tags.issubset(tags):
                continue
            if req.provider and str(full.get("provider") or "").lower() != req.provider.lower():
                continue
            if req.task and str(full.get("task") or "").lower() != req.task.lower():
                continue
            if req.license and req.license.lower() not in str(full.get("license") or "").lower():
                continue
            if req.evaluationStatus and str((full.get("evaluation") or {}).get("status") or "").lower() != req.evaluationStatus.lower():
                continue
            results.append({"kind": kind, **item})
            if len(results) >= req.limit:
                break
        if len(results) >= req.limit:
            break
    out = {"ok": True, "schema": SEARCH_SCHEMA, "version": VERSION, "projectKey": req.projectKey,
           "query": req.query, "resultCount": len(results), "results": results}
    out["searchHash"] = content_hash(out)
    return out


def compose_experiment_binding(req: ExperimentBindingRequest) -> Dict[str, Any]:
    exp = load_experiment(req.projectKey, req.experimentHash)
    model = _load_record(req.projectKey, "model", req.modelRecordHash)
    issues: List[Dict[str, Any]] = []
    em = exp.get("experiment", {}).get("model", {})
    if em.get("provider") != model.get("provider"):
        issues.append({"code": "model-provider-mismatch", "experiment": em.get("provider"), "registry": model.get("provider")})
    if em.get("modelId") != model.get("modelId"):
        issues.append({"code": "model-id-mismatch", "experiment": em.get("modelId"), "registry": model.get("modelId")})
    if em.get("artifactHash") and model.get("artifactHash") and em.get("artifactHash") != model.get("artifactHash"):
        issues.append({"code": "model-artifact-hash-mismatch"})

    dataset_links: List[Dict[str, Any]] = []
    exp_datasets = exp.get("experiment", {}).get("datasets", [])
    for link in sorted(req.datasets, key=lambda x: (x.role, x.datasetRecordHash)):
        ds = _load_record(req.projectKey, "dataset", link.datasetRecordHash)
        candidates = [x for x in exp_datasets if x.get("role") == link.role]
        matched = False
        for x in candidates:
            if x.get("datasetHash") and x.get("datasetHash") == ds.get("datasetHash"):
                matched = True; break
            if not x.get("datasetHash") and x.get("datasetRef") == ds.get("datasetRef"):
                matched = True; break
        if not matched:
            issues.append({"code": "dataset-binding-mismatch", "role": link.role, "datasetRecordHash": link.datasetRecordHash})
        dataset_links.append({
            "role": link.role, "datasetRecordHash": ds["recordHash"], "datasetRecordRef": ds["recordRef"],
            "datasetHash": ds.get("datasetHash"), "datasetKey": ds.get("datasetKey"), "versionLabel": ds.get("versionLabel"),
        })

    binding = {
        "projectKey": req.projectKey, "experimentHash": req.experimentHash, "experimentRef": exp.get("experimentRef"),
        "modelRecordHash": model["recordHash"], "modelRecordRef": model["recordRef"],
        "modelKey": model.get("modelKey"), "modelVersionLabel": model.get("versionLabel"),
        "datasets": dataset_links, "notes": req.notes,
    }
    record_hash = content_hash({"schema": BINDING_SCHEMA, "binding": binding})
    return {
        "ok": True, "schema": BINDING_SCHEMA, "version": VERSION, "recordKind": "experiment-binding",
        "recordHash": record_hash, "recordRef": f"sc://workbench/ai-registry/experiment-binding/{record_hash}",
        "binding": binding, "bindingReady": not issues, "issues": issues,
        "boundaries": {"experimentMutated": False, "automaticExecution": False, "scientificValidityInferred": False},
    }


def save_experiment_binding(req: ExperimentBindingRequest) -> Dict[str, Any]:
    record = compose_experiment_binding(req)
    if not record["bindingReady"]:
        raise HTTPException(status_code=409, detail={"message": "registry binding is not ready", "issues": record["issues"]})
    path = _record_path(req.projectKey, "experiment-binding", record["recordHash"])
    idempotent = path.exists()
    if not idempotent:
        stored = {**record, "createdAt": _now(), "createdBy": req.createdBy,
                  "immutability": {"contentAddressed": True, "experimentMutationAllowed": False}}
        _atomic_json_write(path, stored)
    else:
        stored = _load_record(req.projectKey, "experiment-binding", record["recordHash"])
    return {**stored, "idempotent": idempotent}


def list_bindings(project_key: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    root = _kind_dir(project_key, "experiment-binding")
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                r = _load_record(project_key, "experiment-binding", path.stem)
                b = r.get("binding") or {}
                rows.append({"recordHash": r["recordHash"], "recordRef": r["recordRef"], "experimentHash": b.get("experimentHash"),
                             "modelRecordHash": b.get("modelRecordHash"), "datasetCount": len(b.get("datasets") or []), "createdAt": r.get("createdAt")})
            except Exception:
                rows.append({"recordHash": path.stem, "integrityError": True})
    return {"ok": True, "schema": BINDING_SCHEMA, "version": VERSION, "projectKey": project_key,
            "bindingCount": len(rows), "bindings": rows}


def core_plan(req: RegistryCorePlanRequest) -> Dict[str, Any]:
    record = _load_record(req.projectKey, req.kind, req.recordHash)
    cfg = core_config()
    object_type = {
        "model": "workbench.ai-model-registry-record",
        "dataset": "workbench.ai-dataset-registry-record",
        "experiment-binding": "workbench.ai-experiment-registry-binding",
    }[req.kind]
    out = {
        "ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION,
        "bindingPlan": {
            "objectType": object_type, "sourceRef": record.get("recordRef"), "sourceHash": record.get("recordHash"),
            "projectKey": req.projectKey, "coreProjectEntityId": req.coreProjectEntityId,
            "coreSessionId": req.coreSessionId, "visibility": req.visibility, "createdBy": req.createdBy,
        },
        "coreConfiguration": {"enabled": cfg.get("enabled"), "required": cfg.get("required"),
                              "outboundDispatchEnabled": cfg.get("outboundDispatchEnabled")},
        "boundaries": {"automaticCoreDispatch": False, "automaticCorePersistence": False,
                       "governedCoreObjectCreated": False, "scientificValidityInferred": False,
                       "automaticPreferredModelSelection": False, "automaticPreferredDatasetSelection": False},
    }
    out["planHash"] = content_hash(out)
    return out


@router.get("/ai-registry/manifest")
def registry_manifest() -> Dict[str, Any]: return manifest()

@router.post("/ai-registry/models")
def registry_save_model(req: ModelRegistryRequest) -> Dict[str, Any]: return save_model(req)

@router.get("/ai-registry/models/{project_key}")
def registry_list_models(project_key: str) -> Dict[str, Any]: return _list_records(project_key, "model")

@router.get("/ai-registry/models/{project_key}/{record_hash}")
def registry_get_model(project_key: str, record_hash: str) -> Dict[str, Any]: return _load_record(project_key, "model", record_hash)

@router.post("/ai-registry/datasets")
def registry_save_dataset(req: DatasetRegistryRequest) -> Dict[str, Any]: return save_dataset(req)

@router.get("/ai-registry/datasets/{project_key}")
def registry_list_datasets(project_key: str) -> Dict[str, Any]: return _list_records(project_key, "dataset")

@router.get("/ai-registry/datasets/{project_key}/{record_hash}")
def registry_get_dataset(project_key: str, record_hash: str) -> Dict[str, Any]: return _load_record(project_key, "dataset", record_hash)

@router.post("/ai-registry/search")
def registry_search(req: RegistrySearchRequest) -> Dict[str, Any]: return search_registry(req)

@router.post("/ai-registry/experiment-binding-plan")
def registry_binding_plan(req: ExperimentBindingRequest) -> Dict[str, Any]: return compose_experiment_binding(req)

@router.post("/ai-registry/experiment-bindings")
def registry_save_binding(req: ExperimentBindingRequest) -> Dict[str, Any]: return save_experiment_binding(req)

@router.get("/ai-registry/experiment-bindings/{project_key}")
def registry_list_bindings(project_key: str) -> Dict[str, Any]: return list_bindings(project_key)

@router.get("/ai-registry/experiment-bindings/{project_key}/{record_hash}")
def registry_get_binding(project_key: str, record_hash: str) -> Dict[str, Any]: return _load_record(project_key, "experiment-binding", record_hash)

@router.post("/integration/core/ai-registry/plan")
def registry_core_plan(req: RegistryCorePlanRequest) -> Dict[str, Any]: return core_plan(req)

@router.get("/v1010/status")
def status() -> Dict[str, Any]:
    m = manifest()
    return {
        "ok": True, "schema": SCHEMA, "version": VERSION, "release": m["release"],
        "modelDatasetRegistry": True, "immutableVersionedRecords": True,
        "registrySearchAndListing": True, "immutableExperimentBindings": True,
        "automaticModelDownload": False, "automaticDatasetDownload": False,
        "automaticExperimentMutation": False, "scientificValidityInferred": False,
        "automaticCoreDispatch": False, "manifestHash": m["manifestHash"],
    }

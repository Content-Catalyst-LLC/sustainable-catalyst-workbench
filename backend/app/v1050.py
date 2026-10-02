"""Workbench v10.5.0 — Feature Engineering & Representation Workspace.

Defines content-addressed feature/representation specifications with explicit source bindings,
ordered transformations, split/leakage controls, fit-state lineage, materialization plans,
neutral diagnostics, and Platform Core promotion plans.

This release is intentionally declarative. It does not download datasets, fit transformers,
materialize feature matrices, train models, select a preferred representation, or dispatch
objects to Platform Core automatically.
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
from .v810 import _atomic_json_write, _json_read, _store_root

VERSION = APP_VERSION
SCHEMA = "sc-workbench-feature-engineering-representation-workspace/1.0"
REPRESENTATION_SCHEMA = "sc-workbench-ai-feature-representation/1.0"
MATERIALIZATION_PLAN_SCHEMA = "sc-workbench-ai-feature-materialization-plan/1.0"
FIT_STATE_SCHEMA = "sc-workbench-ai-feature-fit-state/1.0"
DIAGNOSTIC_SCHEMA = "sc-workbench-ai-feature-diagnostic/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-ai-feature-core-plan/1.0"
router = APIRouter(tags=["workbench-v1050-feature-engineering-representation-workspace"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
FieldRole = Literal["feature", "target", "identifier", "group", "weight", "time", "ignore"]
FieldKind = Literal["numeric", "integer", "categorical", "boolean", "text", "datetime", "vector"]
TransformKind = Literal[
    "passthrough", "impute-mean", "impute-median", "impute-constant", "missing-indicator",
    "standardize", "minmax", "robust-scale", "log1p", "clip", "bucketize", "one-hot",
    "ordinal", "hash-encode", "polynomial", "interaction", "datetime-parts",
    "text-tfidf-contract", "embedding-contract",
]
FitScope = Literal["train-only", "pre-fitted", "stateless"]
OutputKind = Literal["dense", "sparse", "vector", "mixed"]
CoreFeatureKind = Literal["representation", "fit-state", "diagnostic"]

_FITTED_TRANSFORMS = {
    "impute-mean", "impute-median", "standardize", "minmax", "robust-scale",
    "bucketize", "one-hot", "ordinal", "text-tfidf-contract",
}
_EXTERNAL_TRANSFORMS = {"embedding-contract"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


def _project_root(project_key: str) -> Path:
    return _store_root() / "ai-feature-representations" / _stable_id(project_key)


def _representation_dir(project_key: str) -> Path:
    return _project_root(project_key) / "representations"


def _representation_path(project_key: str, representation_hash: str) -> Path:
    return _representation_dir(project_key) / f"{representation_hash}.json"


def _fit_state_dir(project_key: str, representation_hash: str) -> Path:
    return _project_root(project_key) / "fit-states" / representation_hash


def _fit_state_path(project_key: str, representation_hash: str, fit_state_hash: str) -> Path:
    return _fit_state_dir(project_key, representation_hash) / f"{fit_state_hash}.json"


class FeatureField(BaseModel):
    fieldKey: str = Field(min_length=1, max_length=200)
    sourcePath: str = Field(min_length=1, max_length=500)
    kind: FieldKind
    role: FieldRole = "feature"
    unit: str = Field(default="", max_length=120)
    nullable: bool = True
    categories: List[str] = Field(default_factory=list, max_length=10000)
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def normalize(self):
        self.fieldKey = self.fieldKey.strip()
        self.sourcePath = self.sourcePath.strip()
        self.unit = self.unit.strip()
        self.categories = sorted({x.strip() for x in self.categories if x.strip()})
        if self.kind != "categorical" and self.categories:
            raise ValueError("categories are only valid for categorical fields")
        return self


class TransformStep(BaseModel):
    stepKey: str = Field(min_length=1, max_length=200)
    kind: TransformKind
    inputs: List[str] = Field(min_length=1, max_length=128)
    outputKey: str = Field(min_length=1, max_length=200)
    fitScope: FitScope = "stateless"
    parameters: Dict[str, Any] = Field(default_factory=dict, max_length=128)
    externalAdapterRef: str = Field(default="", max_length=1000)
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def normalize(self):
        self.stepKey = self.stepKey.strip()
        self.inputs = [x.strip() for x in self.inputs if x.strip()]
        self.outputKey = self.outputKey.strip()
        self.externalAdapterRef = self.externalAdapterRef.strip()
        if len(self.inputs) != len(set(self.inputs)):
            raise ValueError("transform inputs must be unique")
        if self.kind in _FITTED_TRANSFORMS and self.fitScope == "stateless":
            raise ValueError(f"{self.kind} requires fitScope=train-only or pre-fitted")
        if self.kind in _EXTERNAL_TRANSFORMS and not self.externalAdapterRef:
            raise ValueError(f"{self.kind} requires externalAdapterRef")
        if self.fitScope == "pre-fitted" and not self.parameters.get("fitStateHash"):
            raise ValueError("pre-fitted transforms require parameters.fitStateHash")
        return self


class SplitBinding(BaseModel):
    splitKey: str = Field(default="train", min_length=1, max_length=120)
    splitManifestHash: str = Field(default="", max_length=64)
    fitOn: Literal["train", "train-validation"] = "train"
    evaluationSplits: List[str] = Field(default_factory=lambda: ["validation", "test"], max_length=32)
    groupFieldKey: str = Field(default="", max_length=200)
    timeFieldKey: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def normalize(self):
        self.splitManifestHash = self.splitManifestHash.strip().lower()
        if self.splitManifestHash and not _is_hash(self.splitManifestHash):
            raise ValueError("splitManifestHash must be a SHA-256 hash")
        self.evaluationSplits = list(dict.fromkeys(x.strip() for x in self.evaluationSplits if x.strip()))
        return self


class RepresentationRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    representationKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    datasetRecordHash: str = Field(min_length=64, max_length=64)
    datasetVersionRef: str = Field(default="", max_length=1000)
    baseTrainingRunHash: str = Field(default="", max_length=64)
    fields: List[FeatureField] = Field(min_length=1, max_length=2000)
    transforms: List[TransformStep] = Field(default_factory=list, max_length=2000)
    split: SplitBinding = Field(default_factory=SplitBinding)
    outputKind: OutputKind = "mixed"
    outputKeys: List[str] = Field(default_factory=list, max_length=20000)
    randomSeed: int = Field(default=0, ge=0, le=2**31 - 1)
    tags: List[str] = Field(default_factory=list, max_length=64)
    notes: str = Field(default="", max_length=12000)
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("projectKey", "representationKey", "title"):
            setattr(self, attr, getattr(self, attr).strip())
        self.datasetRecordHash = self.datasetRecordHash.strip().lower()
        if not _is_hash(self.datasetRecordHash):
            raise ValueError("datasetRecordHash must be a SHA-256 hash")
        self.baseTrainingRunHash = self.baseTrainingRunHash.strip().lower()
        if self.baseTrainingRunHash and not _is_hash(self.baseTrainingRunHash):
            raise ValueError("baseTrainingRunHash must be a SHA-256 hash")
        field_keys = [f.fieldKey for f in self.fields]
        if len(field_keys) != len(set(field_keys)):
            raise ValueError("fieldKey values must be unique")
        step_keys = [s.stepKey for s in self.transforms]
        if len(step_keys) != len(set(step_keys)):
            raise ValueError("stepKey values must be unique")
        produced = set(field_keys)
        for step in self.transforms:
            missing = [x for x in step.inputs if x not in produced]
            if missing:
                raise ValueError(f"transform {step.stepKey} references unavailable inputs: {missing}")
            if step.outputKey in produced:
                raise ValueError(f"transform outputKey already exists: {step.outputKey}")
            produced.add(step.outputKey)
        if self.outputKeys:
            missing = [x for x in self.outputKeys if x not in produced]
            if missing:
                raise ValueError(f"outputKeys are unavailable: {missing}")
            self.outputKeys = list(dict.fromkeys(self.outputKeys))
        self.tags = sorted({x.strip() for x in self.tags if x.strip()})
        return self


class MaterializationPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    representationHash: str = Field(min_length=64, max_length=64)
    splitName: str = Field(default="train", min_length=1, max_length=120)
    requestedRuntime: Literal["python", "r", "julia", "external"] = "python"
    requestedBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        self.representationHash = self.representationHash.lower()
        if not _is_hash(self.representationHash):
            raise ValueError("representationHash must be a SHA-256 hash")
        return self


class FitStateRecordRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    representationHash: str = Field(min_length=64, max_length=64)
    splitManifestHash: str = Field(default="", max_length=64)
    fittedOnSplit: str = Field(default="train", min_length=1, max_length=120)
    transformStates: Dict[str, Dict[str, Any]] = Field(default_factory=dict, max_length=2000)
    runtimeRef: str = Field(default="", max_length=1000)
    environmentHash: str = Field(default="", max_length=64)
    recordedBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("representationHash", "splitManifestHash", "environmentHash"):
            value = getattr(self, attr).strip().lower()
            if value and not _is_hash(value):
                raise ValueError(f"{attr} must be a SHA-256 hash")
            setattr(self, attr, value)
        return self


class DiagnosticRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    representationHash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def normalize(self):
        self.representationHash = self.representationHash.lower()
        if not _is_hash(self.representationHash):
            raise ValueError("representationHash must be a SHA-256 hash")
        return self


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    kind: CoreFeatureKind
    sourceHash: str = Field(min_length=64, max_length=64)
    representationHash: str = Field(default="", max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("sourceHash", "representationHash"):
            value = getattr(self, attr).strip().lower()
            if value and not _is_hash(value):
                raise ValueError(f"{attr} must be a SHA-256 hash")
            setattr(self, attr, value)
        return self


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION,
        "release": "Feature Engineering & Representation Workspace",
        "product": PRODUCT_KEY, "runtime": RUNTIME_KIND,
        "representationSchema": REPRESENTATION_SCHEMA,
        "fitStateSchema": FIT_STATE_SCHEMA,
        "capabilities": {
            "typedFeatureFields": True,
            "orderedTransformationGraphs": True,
            "contentAddressedRepresentations": True,
            "splitAwareFitContracts": True,
            "dataLeakageDiagnostics": True,
            "fitStateLineage": True,
            "sparseDenseVectorContracts": True,
            "externalEmbeddingContracts": True,
            "materializationPlanning": True,
            "platformCorePromotionPlanning": True,
        },
        "boundaries": {
            "automaticDatasetDownload": False,
            "automaticTransformFitting": False,
            "automaticFeatureMaterialization": False,
            "automaticTrainingExecution": False,
            "automaticRepresentationSelection": False,
            "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
        },
        "transformKinds": sorted(TransformKind.__args__),
    }
    out["manifestHash"] = content_hash(out)
    return out


def _load_representation(project_key: str, representation_hash: str) -> Dict[str, Any]:
    p = _representation_path(project_key, representation_hash.lower())
    if not p.exists():
        raise HTTPException(status_code=404, detail="feature representation not found")
    row = _json_read(p)
    expected = content_hash({"schema": REPRESENTATION_SCHEMA, "representation": row.get("representation") or {}})
    if row.get("representationHash") != expected:
        raise HTTPException(status_code=409, detail="feature representation integrity failure")
    return row


def _diagnostic_issues(rep: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    fields = rep.get("fields") or []
    transforms = rep.get("transforms") or []
    split = rep.get("split") or {}
    roles = {f.get("fieldKey"): f.get("role") for f in fields}
    target_keys = {k for k, role in roles.items() if role == "target"}
    time_keys = {k for k, role in roles.items() if role == "time"}
    group_keys = {k for k, role in roles.items() if role == "group"}
    for step in transforms:
        if any(x in target_keys for x in step.get("inputs") or []):
            issues.append({"severity": "warning", "code": "target-used-as-feature-input", "stepKey": step.get("stepKey")})
        if step.get("kind") in _FITTED_TRANSFORMS and step.get("fitScope") != "train-only" and step.get("fitScope") != "pre-fitted":
            issues.append({"severity": "error", "code": "fitted-transform-not-train-scoped", "stepKey": step.get("stepKey")})
    if split.get("fitOn") == "train-validation":
        issues.append({"severity": "warning", "code": "validation-data-in-fit-scope"})
    if time_keys and not split.get("timeFieldKey"):
        issues.append({"severity": "warning", "code": "time-field-present-without-temporal-split-binding", "fields": sorted(time_keys)})
    if group_keys and not split.get("groupFieldKey"):
        issues.append({"severity": "warning", "code": "group-field-present-without-group-split-binding", "fields": sorted(group_keys)})
    external = [s.get("stepKey") for s in transforms if s.get("kind") in _EXTERNAL_TRANSFORMS]
    if external:
        issues.append({"severity": "info", "code": "external-representation-adapter-required", "steps": external})
    return issues


def compose_representation(req: RepresentationRequest) -> Dict[str, Any]:
    rep = {
        "projectKey": req.projectKey,
        "representationKey": req.representationKey,
        "title": req.title,
        "datasetRecordHash": req.datasetRecordHash,
        "datasetVersionRef": req.datasetVersionRef.strip(),
        "baseTrainingRunHash": req.baseTrainingRunHash,
        "fields": [x.model_dump(mode="json") for x in req.fields],
        "transforms": [x.model_dump(mode="json") for x in req.transforms],
        "split": req.split.model_dump(mode="json"),
        "outputKind": req.outputKind,
        "outputKeys": req.outputKeys,
        "randomSeed": req.randomSeed,
        "tags": req.tags,
        "notes": req.notes,
    }
    h = content_hash({"schema": REPRESENTATION_SCHEMA, "representation": rep})
    issues = _diagnostic_issues(rep)
    blocking = [x for x in issues if x.get("severity") == "error"]
    return {
        "ok": True, "schema": REPRESENTATION_SCHEMA, "version": VERSION,
        "representationHash": h,
        "representationRef": f"sc://workbench/ai-features/representation/{h}",
        "representation": rep,
        "representationReady": not blocking,
        "issues": issues,
    }


def save_representation(req: RepresentationRequest) -> Dict[str, Any]:
    row = compose_representation(req)
    if not row["representationReady"]:
        raise HTTPException(status_code=409, detail={"message": "representation is not ready", "issues": row["issues"]})
    p = _representation_path(req.projectKey, row["representationHash"])
    idem = p.exists()
    if not idem:
        _atomic_json_write(p, {**row, "createdAt": _now(), "createdBy": req.createdBy,
                               "immutability": {"contentAddressed": True, "replacementAllowed": False}})
    return {**_load_representation(req.projectKey, row["representationHash"]), "idempotent": idem}


def list_representations(project_key: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    root = _representation_dir(project_key)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r = _load_representation(project_key, p.stem)
                rep = r["representation"]
                rows.append({
                    "representationHash": r["representationHash"], "representationRef": r["representationRef"],
                    "representationKey": rep.get("representationKey"), "title": rep.get("title"),
                    "datasetRecordHash": rep.get("datasetRecordHash"),
                    "fieldCount": len(rep.get("fields") or []), "transformCount": len(rep.get("transforms") or []),
                    "outputKind": rep.get("outputKind"), "createdAt": r.get("createdAt"),
                })
            except Exception:
                rows.append({"representationHash": p.stem, "integrityError": True})
    return {"ok": True, "schema": REPRESENTATION_SCHEMA, "version": VERSION,
            "projectKey": project_key, "representationCount": len(rows), "representations": rows}


def materialization_plan(req: MaterializationPlanRequest) -> Dict[str, Any]:
    row = _load_representation(req.projectKey, req.representationHash)
    rep = row["representation"]
    fitted = [s for s in rep.get("transforms") or [] if s.get("kind") in _FITTED_TRANSFORMS]
    external = [s for s in rep.get("transforms") or [] if s.get("kind") in _EXTERNAL_TRANSFORMS]
    plan = {
        "representationHash": req.representationHash,
        "datasetRecordHash": rep.get("datasetRecordHash"),
        "splitName": req.splitName,
        "requestedRuntime": req.requestedRuntime,
        "fitRequired": bool([s for s in fitted if s.get("fitScope") == "train-only"]),
        "fittedStepKeys": [s.get("stepKey") for s in fitted],
        "externalStepKeys": [s.get("stepKey") for s in external],
        "orderedSteps": [{"index": i, "stepKey": s.get("stepKey"), "kind": s.get("kind"),
                          "inputs": s.get("inputs"), "outputKey": s.get("outputKey")} for i, s in enumerate(rep.get("transforms") or [])],
        "outputKeys": rep.get("outputKeys") or [],
    }
    h = content_hash({"schema": MATERIALIZATION_PLAN_SCHEMA, "plan": plan})
    return {"ok": True, "schema": MATERIALIZATION_PLAN_SCHEMA, "version": VERSION,
            "planHash": h, "plan": plan,
            "executionBoundary": "plan-only; no dataset read, fit, transform, or feature matrix materialization performed"}


def record_fit_state(req: FitStateRecordRequest) -> Dict[str, Any]:
    row = _load_representation(req.projectKey, req.representationHash)
    rep = row["representation"]
    expected = {s.get("stepKey") for s in rep.get("transforms") or [] if s.get("kind") in _FITTED_TRANSFORMS}
    unknown = sorted(set(req.transformStates) - {s.get("stepKey") for s in rep.get("transforms") or []})
    if unknown:
        raise HTTPException(status_code=422, detail={"message": "fit state contains unknown transform steps", "stepKeys": unknown})
    missing = sorted(expected - set(req.transformStates))
    state = {
        "representationHash": req.representationHash,
        "splitManifestHash": req.splitManifestHash,
        "fittedOnSplit": req.fittedOnSplit,
        "transformStates": req.transformStates,
        "runtimeRef": req.runtimeRef.strip(),
        "environmentHash": req.environmentHash,
    }
    h = content_hash({"schema": FIT_STATE_SCHEMA, "fitState": state})
    p = _fit_state_path(req.projectKey, req.representationHash, h)
    idem = p.exists()
    if not idem:
        _atomic_json_write(p, {"ok": True, "schema": FIT_STATE_SCHEMA, "version": VERSION,
                               "fitStateHash": h, "fitStateRef": f"sc://workbench/ai-features/fit-state/{h}",
                               "fitState": state, "missingExpectedStates": missing,
                               "createdAt": _now(), "recordedBy": req.recordedBy,
                               "immutability": {"contentAddressed": True, "replacementAllowed": False}})
    out = _json_read(p)
    return {**out, "idempotent": idem}


def diagnose(req: DiagnosticRequest) -> Dict[str, Any]:
    row = _load_representation(req.projectKey, req.representationHash)
    issues = _diagnostic_issues(row["representation"])
    summary = {k: len([x for x in issues if x.get("severity") == k]) for k in ("error", "warning", "info")}
    payload = {"representationHash": req.representationHash, "issues": issues, "summary": summary}
    h = content_hash({"schema": DIAGNOSTIC_SCHEMA, "diagnostic": payload})
    return {"ok": True, "schema": DIAGNOSTIC_SCHEMA, "version": VERSION,
            "diagnosticHash": h, "diagnostic": payload,
            "interpretationBoundary": "diagnostics identify structural risks; they do not establish scientific validity or model quality"}


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    plan = {
        "kind": req.kind, "sourceHash": req.sourceHash, "representationHash": req.representationHash,
        "coreProjectEntityId": req.coreProjectEntityId.strip(), "coreSessionId": req.coreSessionId.strip(),
        "visibility": req.visibility, "createdBy": req.createdBy,
        "sourceProduct": PRODUCT_KEY, "sourceVersion": VERSION,
    }
    h = content_hash({"schema": CORE_PLAN_SCHEMA, "plan": plan})
    return {"ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION, "planHash": h, "plan": plan,
            "dispatch": {"automatic": False, "governedCoreObjectCreated": False}}


@router.get("/v1050/status")
def status():
    return manifest()


@router.post("/ai-features/representations/compose")
def compose_route(req: RepresentationRequest):
    return compose_representation(req)


@router.post("/ai-features/representations")
def save_route(req: RepresentationRequest):
    return save_representation(req)


@router.get("/ai-features/representations/{project_key}")
def list_route(project_key: str):
    return list_representations(project_key)


@router.post("/ai-features/materialization-plan")
def materialization_plan_route(req: MaterializationPlanRequest):
    return materialization_plan(req)


@router.post("/ai-features/fit-state/record")
def fit_state_route(req: FitStateRecordRequest):
    return record_fit_state(req)


@router.post("/ai-features/diagnose")
def diagnose_route(req: DiagnosticRequest):
    return diagnose(req)


@router.post("/ai-features/core-plan")
def core_plan_route(req: CorePlanRequest):
    return core_plan(req)

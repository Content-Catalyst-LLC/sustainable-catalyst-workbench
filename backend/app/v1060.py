"""Workbench v10.6.0 — Explainability Workspace.

Declarative, content-addressed explanation specifications and result records.
No automatic retraining, explainer execution/selection, model ranking, causal inference,
or Platform Core dispatch.
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
SCHEMA = "sc-workbench-explainability-workspace/1.0"
EXPLANATION_SCHEMA = "sc-workbench-ai-explanation-spec/1.0"
RESULT_SCHEMA = "sc-workbench-ai-explanation-result/1.0"
COMPARISON_SCHEMA = "sc-workbench-ai-explanation-comparison/1.0"
DIAGNOSTIC_SCHEMA = "sc-workbench-ai-explanation-diagnostic/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-ai-explanation-core-plan/1.0"
router = APIRouter(tags=["workbench-v1060-explainability-workspace"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ExplanationScope = Literal["global", "local", "cohort"]
ExplainerKind = Literal[
    "permutation-importance", "shap-compatible", "partial-dependence", "ice",
    "coefficient", "tree-native", "gradient-attribution", "counterfactual-contract",
]
OutputKind = Literal["scalar", "class", "probability", "vector"]
ResultStatus = Literal["planned", "external", "recorded", "verified"]
CoreObjectKind = Literal["explanation-spec", "explanation-result", "comparison", "diagnostic"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


def _project_root(project_key: str) -> Path:
    return _store_root() / "ai-explainability" / _stable_id(project_key)


def _spec_dir(project_key: str) -> Path:
    return _project_root(project_key) / "specs"


def _spec_path(project_key: str, explanation_hash: str) -> Path:
    return _spec_dir(project_key) / f"{explanation_hash}.json"


def _result_dir(project_key: str, explanation_hash: str) -> Path:
    return _project_root(project_key) / "results" / explanation_hash


def _result_path(project_key: str, explanation_hash: str, result_hash: str) -> Path:
    return _result_dir(project_key, explanation_hash) / f"{result_hash}.json"


class TargetBinding(BaseModel):
    outputKey: str = Field(min_length=1, max_length=200)
    outputKind: OutputKind = "scalar"
    classLabel: Optional[str] = Field(default=None, max_length=500)
    outputIndex: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_class_target(self):
        if self.outputKind == "class" and not self.classLabel:
            raise ValueError("classLabel is required when outputKind='class'")
        return self


class BackgroundBinding(BaseModel):
    datasetRecordHash: str
    splitName: Optional[str] = Field(default=None, max_length=200)
    sampleCount: Optional[int] = Field(default=None, ge=1)
    selectionMethod: Literal["full", "random", "stratified", "user-selected", "external"] = "user-selected"
    selectionSeed: Optional[int] = None

    @model_validator(mode="after")
    def validate_hash(self):
        if not _is_hash(self.datasetRecordHash):
            raise ValueError("datasetRecordHash must be a SHA-256 digest")
        return self


class ExplainerParameters(BaseModel):
    repeats: Optional[int] = Field(default=None, ge=1, le=100000)
    randomSeed: Optional[int] = None
    gridResolution: Optional[int] = Field(default=None, ge=2, le=10000)
    featureKeys: List[str] = Field(default_factory=list, max_length=5000)
    interactionOrder: Optional[int] = Field(default=None, ge=1, le=10)
    externalRuntime: Optional[str] = Field(default=None, max_length=200)
    externalLibrary: Optional[str] = Field(default=None, max_length=200)
    externalLibraryVersion: Optional[str] = Field(default=None, max_length=200)
    notes: str = Field(default="", max_length=10000)


class ExplanationRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    explanationKey: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=500)
    modelRecordHash: str
    datasetRecordHash: str
    representationHash: Optional[str] = None
    benchmarkRecordHash: Optional[str] = None
    trainingRunHash: Optional[str] = None
    explainerKind: ExplainerKind
    scope: ExplanationScope
    target: TargetBinding
    background: Optional[BackgroundBinding] = None
    instanceRecordHashes: List[str] = Field(default_factory=list, max_length=10000)
    cohortFilter: Optional[Dict[str, Any]] = None
    parameters: ExplainerParameters = Field(default_factory=ExplainerParameters)
    createdBy: str = Field(default="user", max_length=200)
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_contract(self):
        for name in ("modelRecordHash", "datasetRecordHash", "representationHash",
                     "benchmarkRecordHash", "trainingRunHash"):
            value = getattr(self, name)
            if value is not None and not _is_hash(value):
                raise ValueError(f"{name} must be a SHA-256 digest")
        if any(not _is_hash(v) for v in self.instanceRecordHashes):
            raise ValueError("instanceRecordHashes must contain SHA-256 digests")
        if self.scope == "local" and not self.instanceRecordHashes:
            raise ValueError("local explanations require instanceRecordHashes")
        if self.scope == "cohort" and not self.cohortFilter:
            raise ValueError("cohort explanations require cohortFilter")
        if self.explainerKind in {"shap-compatible", "partial-dependence", "ice"} and self.background is None:
            raise ValueError(f"{self.explainerKind} requires an explicit background binding")
        return self


class FeatureAttribution(BaseModel):
    featureKey: str = Field(min_length=1, max_length=300)
    value: float
    direction: Optional[Literal["positive", "negative", "neutral"]] = None
    rank: Optional[int] = Field(default=None, ge=1)
    featureValue: Optional[Any] = None
    uncertainty: Optional[Dict[str, Any]] = None


class ExplanationResultRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    explanationHash: str
    status: ResultStatus = "recorded"
    runtime: str = Field(min_length=1, max_length=300)
    runtimeVersion: Optional[str] = Field(default=None, max_length=300)
    library: Optional[str] = Field(default=None, max_length=300)
    libraryVersion: Optional[str] = Field(default=None, max_length=300)
    executionRecordHash: Optional[str] = None
    outputRecordHash: Optional[str] = None
    attributions: List[FeatureAttribution] = Field(default_factory=list, max_length=100000)
    curves: List[Dict[str, Any]] = Field(default_factory=list, max_length=10000)
    counterfactuals: List[Dict[str, Any]] = Field(default_factory=list, max_length=10000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list, max_length=1000)
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_hashes(self):
        for name in ("explanationHash", "executionRecordHash", "outputRecordHash"):
            value = getattr(self, name)
            if value is not None and not _is_hash(value):
                raise ValueError(f"{name} must be a SHA-256 digest")
        return self


class ComparisonRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    resultHashes: List[str] = Field(min_length=2, max_length=100)
    comparisonKey: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=500)
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_hashes(self):
        if len(set(self.resultHashes)) != len(self.resultHashes):
            raise ValueError("resultHashes must be unique")
        if not all(_is_hash(v) for v in self.resultHashes):
            raise ValueError("resultHashes must contain SHA-256 digests")
        return self


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    objectKind: CoreObjectKind
    objectHash: str
    requestedBy: str = Field(default="user", max_length=200)

    @model_validator(mode="after")
    def validate_hash(self):
        if not _is_hash(self.objectHash):
            raise ValueError("objectHash must be a SHA-256 digest")
        return self


def _issues_for(req: ExplanationRequest) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    if req.explainerKind in {"coefficient", "tree-native", "gradient-attribution"}:
        issues.append({"severity": "info", "code": "model-specific-explainer",
                       "message": "Compatibility must be verified by the execution runtime."})
    if req.explainerKind == "shap-compatible":
        issues.append({"severity": "info", "code": "external-shap-contract",
                       "message": "Workbench records SHAP-compatible contracts/results but does not execute SHAP automatically."})
    if req.explainerKind in {"partial-dependence", "ice"}:
        issues.append({"severity": "warning", "code": "feature-dependence-assumption",
                       "message": "Dependence plots can mislead when features are strongly dependent."})
    issues.append({"severity": "warning", "code": "explanation-not-causation",
                   "message": "Model explanations and feature attribution do not establish causal effects."})
    return issues


def _spec_payload(req: ExplanationRequest) -> Dict[str, Any]:
    payload = req.model_dump(mode="json")
    payload.update({"schema": EXPLANATION_SCHEMA, "version": VERSION, "product": PRODUCT_KEY,
                    "runtime": RUNTIME_KIND, "issues": _issues_for(req), "causalInterpretationAllowed": False})
    return payload


def compose_explanation(req: ExplanationRequest) -> Dict[str, Any]:
    payload = _spec_payload(req)
    explanation_hash = content_hash(payload)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "explanationHash": explanation_hash,
            "explanation": payload, "issues": payload["issues"], "explanationReady": True}


def save_explanation(req: ExplanationRequest) -> Dict[str, Any]:
    row = compose_explanation(req)
    path = _spec_path(req.projectKey, row["explanationHash"])
    existing = _json_read(path) if path.exists() else None
    if existing is not None:
        return {**row, "saved": True, "idempotent": True}
    record = {**row["explanation"], "explanationHash": row["explanationHash"], "createdAt": _now()}
    _atomic_json_write(path, record)
    return {**row, "saved": True, "idempotent": False}


def list_explanations(project_key: str) -> Dict[str, Any]:
    rows = []
    directory = _spec_dir(project_key)
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            row = _json_read(path)
            if isinstance(row, dict):
                rows.append(row)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key, "explanations": rows}


def get_explanation(project_key: str, explanation_hash: str) -> Dict[str, Any]:
    row = _json_read(_spec_path(project_key, explanation_hash))
    if not isinstance(row, dict):
        raise HTTPException(status_code=404, detail="Explanation specification not found")
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "explanation": row}


def record_result(req: ExplanationResultRequest) -> Dict[str, Any]:
    spec = _json_read(_spec_path(req.projectKey, req.explanationHash))
    if not isinstance(spec, dict):
        raise HTTPException(status_code=404, detail="Explanation specification not found")
    payload = req.model_dump(mode="json")
    payload.update({"schema": RESULT_SCHEMA, "version": VERSION, "product": PRODUCT_KEY,
                    "modelRecordHash": spec["modelRecordHash"], "datasetRecordHash": spec["datasetRecordHash"],
                    "explainerKind": spec["explainerKind"], "scope": spec["scope"],
                    "causalInterpretationAllowed": False})
    result_hash = content_hash(payload)
    path = _result_path(req.projectKey, req.explanationHash, result_hash)
    existing = _json_read(path) if path.exists() else None
    if existing is None:
        payload.update({"resultHash": result_hash, "recordedAt": _now()})
        _atomic_json_write(path, payload)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "resultHash": result_hash,
            "result": existing or payload, "idempotent": existing is not None}


def list_results(project_key: str, explanation_hash: str) -> Dict[str, Any]:
    rows = []
    directory = _result_dir(project_key, explanation_hash)
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            row = _json_read(path)
            if isinstance(row, dict):
                rows.append(row)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key,
            "explanationHash": explanation_hash, "results": rows}


def _find_result(project_key: str, result_hash: str) -> Optional[Dict[str, Any]]:
    root = _project_root(project_key) / "results"
    if not root.exists():
        return None
    for path in root.glob(f"*/{result_hash}.json"):
        row = _json_read(path)
        if isinstance(row, dict):
            return row
    return None


def compare_results(req: ComparisonRequest) -> Dict[str, Any]:
    rows = []
    for result_hash in req.resultHashes:
        row = _find_result(req.projectKey, result_hash)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Explanation result not found: {result_hash}")
        rows.append(row)
    feature_maps = [{x["featureKey"]: x["value"] for x in row.get("attributions", [])} for row in rows]
    all_features = sorted(set().union(*(set(m) for m in feature_maps)))
    feature_comparison = []
    for feature in all_features:
        values = [m.get(feature) for m in feature_maps]
        present = [v for v in values if v is not None]
        feature_comparison.append({"featureKey": feature, "values": values,
                                   "min": min(present) if present else None,
                                   "max": max(present) if present else None,
                                   "range": (max(present)-min(present)) if present else None})
    payload = {"schema": COMPARISON_SCHEMA, "version": VERSION, "projectKey": req.projectKey,
               "comparisonKey": req.comparisonKey, "title": req.title, "resultHashes": req.resultHashes,
               "featureComparison": feature_comparison, "notes": req.notes,
               "causalInterpretationAllowed": False,
               "interpretationBoundary": "Differences describe explanation outputs, not causal effects or model quality rankings."}
    comparison_hash = content_hash(payload)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "comparisonHash": comparison_hash,
            "comparison": payload}


def diagnose(req: ExplanationRequest) -> Dict[str, Any]:
    issues = _issues_for(req)
    return {"ok": True, "schema": DIAGNOSTIC_SCHEMA, "version": VERSION, "issues": issues,
            "blocking": any(i["severity"] == "error" for i in issues), "causalInterpretationAllowed": False}


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    return {"ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION,
            "plan": {"objectKind": req.objectKind, "objectHash": req.objectHash, "requestedBy": req.requestedBy,
                     "governedCoreObjectCreated": False, "automaticDispatch": False,
                     "requiredAction": "Submit through a governed Platform Core handoff after explicit review."}}


def manifest() -> Dict[str, Any]:
    body = {
        "ok": True, "schema": SCHEMA, "version": VERSION, "release": "Explainability Workspace",
        "product": PRODUCT_KEY, "runtime": RUNTIME_KIND, "explanationSchema": EXPLANATION_SCHEMA,
        "resultSchema": RESULT_SCHEMA,
        "capabilities": {
            "contentAddressedExplanationSpecs": True, "globalExplanations": True, "localExplanations": True,
            "cohortExplanations": True, "permutationImportanceContracts": True, "shapCompatibleContracts": True,
            "partialDependencePlanning": True, "icePlanning": True, "modelSpecificExplainerContracts": True,
            "explanationResultProvenance": True, "crossExplanationComparison": True,
            "causalityGuardrails": True, "platformCorePromotionPlanning": True,
        },
        "boundaries": {
            "automaticModelTraining": False, "automaticExplainerExecution": False,
            "automaticExplainerSelection": False, "automaticModelRanking": False,
            "causalInferenceFromAttribution": False, "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
        },
        "explainerKinds": ["permutation-importance", "shap-compatible", "partial-dependence", "ice",
                           "coefficient", "tree-native", "gradient-attribution", "counterfactual-contract"],
    }
    body["manifestHash"] = content_hash({k: v for k, v in body.items() if k not in {"ok", "manifestHash"}})
    return body


@router.get("/v1060/status")
def status_route(): return manifest()

@router.post("/ai-explainability/explanations/compose")
def compose_route(req: ExplanationRequest): return compose_explanation(req)

@router.post("/ai-explainability/explanations")
def save_route(req: ExplanationRequest): return save_explanation(req)

@router.get("/ai-explainability/explanations/{project_key}")
def list_route(project_key: str): return list_explanations(project_key)

@router.get("/ai-explainability/explanations/{project_key}/{explanation_hash}")
def get_route(project_key: str, explanation_hash: str): return get_explanation(project_key, explanation_hash)

@router.post("/ai-explainability/results")
def result_route(req: ExplanationResultRequest): return record_result(req)

@router.get("/ai-explainability/results/{project_key}/{explanation_hash}")
def result_list_route(project_key: str, explanation_hash: str): return list_results(project_key, explanation_hash)

@router.post("/ai-explainability/compare")
def compare_route(req: ComparisonRequest): return compare_results(req)

@router.post("/ai-explainability/diagnose")
def diagnose_route(req: ExplanationRequest): return diagnose(req)

@router.post("/ai-explainability/core-plan")
def core_plan_route(req: CorePlanRequest): return core_plan(req)

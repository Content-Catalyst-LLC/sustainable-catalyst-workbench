"""Workbench v10.7.0 — Uncertainty & Calibration Workspace.

Defines reproducible uncertainty and calibration specifications/results for scientific AI
workflows, including predictive uncertainty, interval/quantile/conformal contracts,
probabilistic calibration, reliability analysis, calibration metrics, and comparison.

This release is intentionally declarative. It does not retrain models, silently recalibrate
predictions, choose a preferred calibration method, manufacture uncertainty estimates,
or dispatch governed Platform Core objects automatically.
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
SCHEMA = "sc-workbench-uncertainty-calibration-workspace/1.0"
STUDY_SCHEMA = "sc-workbench-ai-uncertainty-calibration-study/1.0"
RESULT_SCHEMA = "sc-workbench-ai-uncertainty-calibration-result/1.0"
COMPARISON_SCHEMA = "sc-workbench-ai-uncertainty-calibration-comparison/1.0"
DIAGNOSTIC_SCHEMA = "sc-workbench-ai-uncertainty-calibration-diagnostic/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-ai-uncertainty-calibration-core-plan/1.0"
router = APIRouter(tags=["workbench-v1070-uncertainty-calibration-workspace"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")

TaskKind = Literal["classification", "regression", "forecasting", "ranking", "other"]
UncertaintyKind = Literal[
    "predictive",
    "aleatoric",
    "epistemic",
    "ensemble",
    "bootstrap",
    "mc-dropout-contract",
    "quantile",
    "prediction-interval",
    "conformal",
]
CalibrationKind = Literal[
    "none",
    "reliability-analysis",
    "platt-contract",
    "isotonic-contract",
    "temperature-scaling-contract",
    "beta-calibration-contract",
    "quantile-calibration",
    "conformal-calibration",
]
SplitRole = Literal["train", "validation", "calibration", "test", "holdout", "external"]
CoreObjectKind = Literal["study", "result", "comparison", "diagnostic"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


def _project_root(project_key: str) -> Path:
    return _store_root() / "ai-uncertainty-calibration" / _stable_id(project_key)


def _study_dir(project_key: str) -> Path:
    return _project_root(project_key) / "studies"


def _study_path(project_key: str, study_hash: str) -> Path:
    return _study_dir(project_key) / f"{study_hash}.json"


def _result_dir(project_key: str, study_hash: str) -> Path:
    return _project_root(project_key) / "results" / study_hash


def _result_path(project_key: str, study_hash: str, result_hash: str) -> Path:
    return _result_dir(project_key, study_hash) / f"{result_hash}.json"


class SplitBinding(BaseModel):
    datasetRecordHash: str
    splitName: str = Field(min_length=1, max_length=200)
    role: SplitRole
    sampleCount: Optional[int] = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_hash(self):
        if not _is_hash(self.datasetRecordHash):
            raise ValueError("datasetRecordHash must be a SHA-256 digest")
        return self


class TargetBinding(BaseModel):
    outputKey: str = Field(min_length=1, max_length=200)
    classLabel: Optional[str] = Field(default=None, max_length=500)
    quantileLevels: List[float] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_quantiles(self):
        for q in self.quantileLevels:
            if not (0.0 < q < 1.0):
                raise ValueError("quantileLevels must be between 0 and 1")
        if len(set(self.quantileLevels)) != len(self.quantileLevels):
            raise ValueError("quantileLevels must be unique")
        return self


class CalibrationParameters(BaseModel):
    bins: int = Field(default=10, ge=2, le=1000)
    confidenceLevel: float = Field(default=0.95, gt=0.0, lt=1.0)
    alpha: Optional[float] = Field(default=None, gt=0.0, lt=1.0)
    randomSeed: Optional[int] = None
    groupKeys: List[str] = Field(default_factory=list, max_length=1000)
    notes: str = Field(default="", max_length=10000)


class StudyRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    studyKey: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=500)
    modelRecordHash: str
    datasetRecordHash: str
    representationHash: Optional[str] = None
    trainingRunHash: Optional[str] = None
    benchmarkRecordHash: Optional[str] = None
    taskKind: TaskKind
    uncertaintyKinds: List[UncertaintyKind] = Field(default_factory=list, min_length=1, max_length=20)
    calibrationKind: CalibrationKind = "reliability-analysis"
    target: TargetBinding
    splits: List[SplitBinding] = Field(default_factory=list, max_length=100)
    parameters: CalibrationParameters = Field(default_factory=CalibrationParameters)
    externalRuntime: Optional[str] = Field(default=None, max_length=300)
    externalLibrary: Optional[str] = Field(default=None, max_length=300)
    externalLibraryVersion: Optional[str] = Field(default=None, max_length=300)
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_contract(self):
        for name in ("modelRecordHash", "datasetRecordHash", "representationHash",
                     "trainingRunHash", "benchmarkRecordHash"):
            value = getattr(self, name)
            if value is not None and not _is_hash(value):
                raise ValueError(f"{name} must be a SHA-256 digest")
        if len(set(self.uncertaintyKinds)) != len(self.uncertaintyKinds):
            raise ValueError("uncertaintyKinds must be unique")
        calibration_roles = [s for s in self.splits if s.role == "calibration"]
        if self.calibrationKind not in {"none", "reliability-analysis", "quantile-calibration"} and not calibration_roles:
            raise ValueError("selected calibration method requires an explicit calibration split")
        if "conformal" in self.uncertaintyKinds and not calibration_roles:
            raise ValueError("conformal uncertainty requires an explicit calibration split")
        if self.calibrationKind == "conformal-calibration" and "conformal" not in self.uncertaintyKinds:
            raise ValueError("conformal-calibration requires uncertaintyKinds to include 'conformal'")
        return self


class ReliabilityBin(BaseModel):
    lowerBound: float
    upperBound: float
    meanConfidence: float
    observedFrequency: float
    count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.upperBound < self.lowerBound:
            raise ValueError("upperBound must be >= lowerBound")
        return self


class IntervalMetric(BaseModel):
    level: float = Field(gt=0.0, lt=1.0)
    empiricalCoverage: float = Field(ge=0.0, le=1.0)
    meanWidth: Optional[float] = Field(default=None, ge=0.0)
    medianWidth: Optional[float] = Field(default=None, ge=0.0)


class GroupMetric(BaseModel):
    groupKey: str = Field(min_length=1, max_length=300)
    groupValue: str = Field(min_length=1, max_length=1000)
    sampleCount: int = Field(ge=0)
    expectedCalibrationError: Optional[float] = Field(default=None, ge=0.0)
    brierScore: Optional[float] = Field(default=None, ge=0.0)
    empiricalCoverage: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class ResultRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    studyHash: str
    runtime: str = Field(min_length=1, max_length=300)
    runtimeVersion: Optional[str] = Field(default=None, max_length=300)
    executionRecordHash: Optional[str] = None
    predictionRecordHash: Optional[str] = None
    calibrationArtifactHash: Optional[str] = None
    expectedCalibrationError: Optional[float] = Field(default=None, ge=0.0)
    maximumCalibrationError: Optional[float] = Field(default=None, ge=0.0)
    brierScore: Optional[float] = Field(default=None, ge=0.0)
    logLoss: Optional[float] = Field(default=None, ge=0.0)
    negativeLogLikelihood: Optional[float] = Field(default=None, ge=0.0)
    reliabilityBins: List[ReliabilityBin] = Field(default_factory=list, max_length=10000)
    intervalMetrics: List[IntervalMetric] = Field(default_factory=list, max_length=1000)
    groupMetrics: List[GroupMetric] = Field(default_factory=list, max_length=10000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list, max_length=1000)
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_hashes(self):
        for name in ("studyHash", "executionRecordHash", "predictionRecordHash", "calibrationArtifactHash"):
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


def _issues_for(req: StudyRequest) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    if "aleatoric" in req.uncertaintyKinds:
        issues.append({
            "severity": "info",
            "code": "aleatoric-contract",
            "message": "Aleatoric uncertainty must be supported by the model/runtime; Workbench does not infer it automatically.",
        })
    if "epistemic" in req.uncertaintyKinds:
        issues.append({
            "severity": "info",
            "code": "epistemic-contract",
            "message": "Epistemic uncertainty estimates depend on modeling assumptions and runtime implementation.",
        })
    if "mc-dropout-contract" in req.uncertaintyKinds:
        issues.append({
            "severity": "info",
            "code": "external-mc-dropout-contract",
            "message": "Workbench records MC-dropout provenance but does not enable dropout inference automatically.",
        })
    if req.calibrationKind not in {"none", "reliability-analysis"}:
        issues.append({
            "severity": "warning",
            "code": "calibration-changes-predictions",
            "message": "Calibration transforms prediction probabilities or intervals and must remain separately versioned from the source model.",
        })
    issues.append({
        "severity": "warning",
        "code": "uncertainty-not-guarantee",
        "message": "Reported uncertainty, confidence, or coverage is conditional on the specified data, model, method, and assumptions.",
    })
    return issues


def _study_payload(req: StudyRequest) -> Dict[str, Any]:
    payload = req.model_dump(mode="json")
    payload.update({
        "schema": STUDY_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "issues": _issues_for(req),
        "automaticCalibrationApplied": False,
        "automaticModelSelection": False,
    })
    return payload


def compose_study(req: StudyRequest) -> Dict[str, Any]:
    payload = _study_payload(req)
    study_hash = content_hash(payload)
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "studyHash": study_hash,
        "study": payload,
        "issues": payload["issues"],
        "studyReady": True,
    }


def save_study(req: StudyRequest) -> Dict[str, Any]:
    row = compose_study(req)
    path = _study_path(req.projectKey, row["studyHash"])
    existing = _json_read(path) if path.exists() else None
    if existing is not None:
        return {**row, "saved": True, "idempotent": True}
    record = {**row["study"], "studyHash": row["studyHash"], "createdAt": _now()}
    _atomic_json_write(path, record)
    return {**row, "saved": True, "idempotent": False}


def list_studies(project_key: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    directory = _study_dir(project_key)
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            row = _json_read(path)
            if isinstance(row, dict):
                rows.append(row)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key, "studies": rows}


def get_study(project_key: str, study_hash: str) -> Dict[str, Any]:
    path = _study_path(project_key, study_hash)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Uncertainty/calibration study not found")
    row = _json_read(path)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "study": row}


def record_result(req: ResultRequest) -> Dict[str, Any]:
    study_path = _study_path(req.projectKey, req.studyHash)
    if not study_path.exists():
        raise HTTPException(status_code=404, detail="Uncertainty/calibration study not found")
    study = _json_read(study_path)
    payload = req.model_dump(mode="json")
    payload.update({
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "modelRecordHash": study["modelRecordHash"],
        "datasetRecordHash": study["datasetRecordHash"],
        "taskKind": study["taskKind"],
        "uncertaintyKinds": study["uncertaintyKinds"],
        "calibrationKind": study["calibrationKind"],
        "sourceStudyHash": req.studyHash,
    })
    result_hash = content_hash(payload)
    path = _result_path(req.projectKey, req.studyHash, result_hash)
    existing = _json_read(path) if path.exists() else None
    if existing is None:
        payload.update({"resultHash": result_hash, "recordedAt": _now()})
        _atomic_json_write(path, payload)
    return {
        "ok": True, "schema": SCHEMA, "version": VERSION,
        "resultHash": result_hash, "result": existing or payload,
        "idempotent": existing is not None,
    }


def list_results(project_key: str, study_hash: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    directory = _result_dir(project_key, study_hash)
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            row = _json_read(path)
            if isinstance(row, dict):
                rows.append(row)
    return {
        "ok": True, "schema": SCHEMA, "version": VERSION,
        "projectKey": project_key, "studyHash": study_hash, "results": rows,
    }


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
            raise HTTPException(status_code=404, detail=f"Uncertainty/calibration result not found: {result_hash}")
        rows.append(row)

    metrics = []
    for key in ("expectedCalibrationError", "maximumCalibrationError", "brierScore",
                "logLoss", "negativeLogLikelihood"):
        values = [row.get(key) for row in rows]
        present = [v for v in values if v is not None]
        metrics.append({
            "metric": key,
            "values": values,
            "min": min(present) if present else None,
            "max": max(present) if present else None,
            "range": (max(present) - min(present)) if present else None,
        })

    payload = {
        "schema": COMPARISON_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "comparisonKey": req.comparisonKey,
        "title": req.title,
        "resultHashes": req.resultHashes,
        "metrics": metrics,
        "notes": req.notes,
        "automaticWinnerSelection": False,
        "interpretationBoundary": "Metric differences describe recorded calibration/uncertainty behavior and do not automatically identify a preferred model or method.",
    }
    comparison_hash = content_hash(payload)
    return {"ok": True, "schema": SCHEMA, "version": VERSION,
            "comparisonHash": comparison_hash, "comparison": payload}


def diagnose(req: StudyRequest) -> Dict[str, Any]:
    issues = _issues_for(req)
    return {
        "ok": True,
        "schema": DIAGNOSTIC_SCHEMA,
        "version": VERSION,
        "issues": issues,
        "blocking": any(i["severity"] == "error" for i in issues),
    }


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "plan": {
            "objectKind": req.objectKind,
            "objectHash": req.objectHash,
            "requestedBy": req.requestedBy,
            "governedCoreObjectCreated": False,
            "automaticDispatch": False,
            "requiredAction": "Submit through a governed Platform Core handoff after explicit review.",
        },
    }


def manifest() -> Dict[str, Any]:
    body = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Uncertainty & Calibration Workspace",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "studySchema": STUDY_SCHEMA,
        "resultSchema": RESULT_SCHEMA,
        "capabilities": {
            "contentAddressedStudies": True,
            "predictiveUncertaintyContracts": True,
            "aleatoricEpistemicContracts": True,
            "ensembleBootstrapContracts": True,
            "mcDropoutContracts": True,
            "quantileContracts": True,
            "predictionIntervalContracts": True,
            "conformalContracts": True,
            "reliabilityAnalysis": True,
            "calibrationMethodContracts": True,
            "eceMceMetrics": True,
            "brierLogLossNllMetrics": True,
            "coverageWidthMetrics": True,
            "groupCalibrationMetrics": True,
            "resultProvenance": True,
            "crossResultComparison": True,
            "platformCorePromotionPlanning": True,
        },
        "boundaries": {
            "automaticModelTraining": False,
            "automaticUncertaintyGeneration": False,
            "automaticCalibrationExecution": False,
            "automaticCalibrationSelection": False,
            "automaticModelRanking": False,
            "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
        },
        "uncertaintyKinds": [
            "predictive", "aleatoric", "epistemic", "ensemble", "bootstrap",
            "mc-dropout-contract", "quantile", "prediction-interval", "conformal",
        ],
        "calibrationKinds": [
            "none", "reliability-analysis", "platt-contract", "isotonic-contract",
            "temperature-scaling-contract", "beta-calibration-contract",
            "quantile-calibration", "conformal-calibration",
        ],
    }
    body["manifestHash"] = content_hash({k: v for k, v in body.items() if k not in {"ok", "manifestHash"}})
    return body


@router.get("/v1070/status")
def status_route():
    return manifest()


@router.post("/ai-uncertainty-calibration/studies/compose")
def compose_route(req: StudyRequest):
    return compose_study(req)


@router.post("/ai-uncertainty-calibration/studies")
def save_route(req: StudyRequest):
    return save_study(req)


@router.get("/ai-uncertainty-calibration/studies/{project_key}")
def list_route(project_key: str):
    return list_studies(project_key)


@router.get("/ai-uncertainty-calibration/studies/{project_key}/{study_hash}")
def get_route(project_key: str, study_hash: str):
    return get_study(project_key, study_hash)


@router.post("/ai-uncertainty-calibration/results")
def result_route(req: ResultRequest):
    return record_result(req)


@router.get("/ai-uncertainty-calibration/results/{project_key}/{study_hash}")
def result_list_route(project_key: str, study_hash: str):
    return list_results(project_key, study_hash)


@router.post("/ai-uncertainty-calibration/compare")
def compare_route(req: ComparisonRequest):
    return compare_results(req)


@router.post("/ai-uncertainty-calibration/diagnose")
def diagnose_route(req: StudyRequest):
    return diagnose(req)


@router.post("/ai-uncertainty-calibration/core-plan")
def core_plan_route(req: CorePlanRequest):
    return core_plan(req)

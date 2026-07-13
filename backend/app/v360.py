from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import re
from statistics import mean, median, pstdev
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

VERSION = "3.6.0"
DATASET_PROFILE_SCHEMA = "sc-workbench-dataset-profile/1.0"
SPLIT_SCHEMA = "sc-workbench-split-plan/1.0"
FEATURE_SCHEMA = "sc-workbench-feature-plan/1.0"
EVALUATION_SCHEMA = "sc-workbench-model-evaluation/1.0"
CV_SCHEMA = "sc-workbench-cross-validation-summary/1.0"
FORECAST_SCHEMA = "sc-workbench-forecast/1.0"
DRIFT_SCHEMA = "sc-workbench-drift-audit/1.0"
LEAKAGE_SCHEMA = "sc-workbench-leakage-audit/1.0"
FAIRNESS_SCHEMA = "sc-workbench-fairness-audit/1.0"
MODEL_CARD_SCHEMA = "sc-workbench-model-card/1.0"
REPRO_SCHEMA = "sc-workbench-reproducibility-plan/1.0"
EXPERIMENT_SCHEMA = "sc-workbench-ml-experiment/1.0"

router = APIRouter(prefix="/v360", tags=["workbench-v360"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _hash(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _slug(value: Any, fallback: str = "record") -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text[:120] or fallback


def _finite(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _numeric(values: list[Any]) -> list[float]:
    return [number for number in (_finite(value) for value in values) if number is not None]


def _round(value: float | None, digits: int = 8) -> float | None:
    return None if value is None or not math.isfinite(value) else round(value, digits)


class DatasetProfileRequest(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    target: str = ""
    dataset_id: str = "dataset"


class SplitPlanRequest(BaseModel):
    record_count: int = Field(ge=3)
    strategy: Literal["random", "stratified", "time", "group"] = "random"
    train_fraction: float = 0.7
    validation_fraction: float = 0.15
    test_fraction: float = 0.15
    seed: int = 42
    timestamp_field: str = ""
    group_field: str = ""


class FeaturePlanRequest(BaseModel):
    columns: list[str] = Field(default_factory=list)
    target: str
    identifiers: list[str] = Field(default_factory=list)
    protected_attributes: list[str] = Field(default_factory=list)
    timestamp_field: str = ""
    transformations: dict[str, str] = Field(default_factory=dict)


class RegressionEvaluationRequest(BaseModel):
    y_true: list[float]
    y_pred: list[float]
    baseline: list[float] = Field(default_factory=list)


class ClassificationEvaluationRequest(BaseModel):
    y_true: list[str]
    y_pred: list[str]
    positive_label: str = "1"


class CrossValidationRequest(BaseModel):
    folds: list[dict[str, float]] = Field(default_factory=list)
    primary_metric: str
    direction: Literal["maximize", "minimize"] = "maximize"


class ForecastRequest(BaseModel):
    values: list[float]
    horizon: int = Field(default=5, ge=1, le=500)
    confidence_z: float = Field(default=1.96, ge=0, le=5)


class DriftAuditRequest(BaseModel):
    reference: list[float]
    current: list[float]
    warning_threshold: float = 0.25
    critical_threshold: float = 0.5
    bins: int = Field(default=10, ge=2, le=50)


class LeakageAuditRequest(BaseModel):
    features: list[str] = Field(default_factory=list)
    target: str
    split_strategy: str = "random"
    timestamp_field: str = ""
    known_post_outcome_fields: list[str] = Field(default_factory=list)


class FairnessGroup(BaseModel):
    group: str
    count: int = Field(ge=0)
    positive_rate: float | None = None
    true_positive_rate: float | None = None
    false_positive_rate: float | None = None
    error_rate: float | None = None


class FairnessAuditRequest(BaseModel):
    groups: list[FairnessGroup] = Field(default_factory=list)
    minimum_group_size: int = Field(default=30, ge=1)
    warning_gap: float = Field(default=0.1, ge=0)
    critical_gap: float = Field(default=0.2, ge=0)


class ModelCardRequest(BaseModel):
    model_name: str
    task: str
    algorithm: str
    dataset_hash: str = ""
    features: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    intended_uses: list[str] = Field(default_factory=list)
    prohibited_uses: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    fairness: dict[str, Any] = Field(default_factory=dict)
    drift: dict[str, Any] = Field(default_factory=dict)
    reviewer: str = ""
    approval_status: Literal["draft", "review-required", "approved", "rejected"] = "review-required"


class ReproducibilityRequest(BaseModel):
    model_type: str = "linear"
    languages: list[str] = Field(default_factory=lambda: ["python", "r", "javascript", "rust"])
    seed: int = 42
    tolerance: float = Field(default=1e-9, gt=0)
    coefficients: list[float] = Field(default_factory=list)
    intercept: float = 0.0


class ExperimentScaffoldRequest(BaseModel):
    project_id: str = "default"
    experiment_name: str = "Predictive analytics experiment"
    task: Literal["regression", "classification", "clustering", "anomaly-detection", "forecasting", "deep-learning"] = "regression"
    dataset_id: str = "dataset"
    target: str = ""
    features: list[str] = Field(default_factory=list)
    validation_strategy: str = "k-fold"
    seed: int = 42
    high_stakes_context: bool = False


def profile_dataset(request: DatasetProfileRequest) -> dict[str, Any]:
    rows = request.rows
    if not rows:
        raise ValueError("at least one dataset row is required")
    columns = sorted({str(key) for row in rows for key in row.keys()})
    profiles: list[dict[str, Any]] = []
    for column in columns:
        values = [row.get(column) for row in rows]
        present = [value for value in values if value is not None and value != ""]
        numbers = _numeric(present)
        numeric = bool(present) and len(numbers) == len(present)
        item: dict[str, Any] = {
            "name": column,
            "kind": "numeric" if numeric else "categorical",
            "count": len(present),
            "missing": len(values) - len(present),
            "missingFraction": _round((len(values) - len(present)) / len(values)),
            "unique": len({_canonical(value) for value in present}),
        }
        if numeric:
            item.update({
                "minimum": _round(min(numbers)),
                "maximum": _round(max(numbers)),
                "mean": _round(mean(numbers)),
                "median": _round(median(numbers)),
                "standardDeviation": _round(pstdev(numbers)) if len(numbers) > 1 else 0.0,
            })
        else:
            counts = Counter(str(value) for value in present)
            item["topValues"] = [{"value": value, "count": count} for value, count in counts.most_common(5)]
        profiles.append(item)
    record = {
        "schema": DATASET_PROFILE_SCHEMA,
        "version": VERSION,
        "datasetId": _slug(request.dataset_id, "dataset"),
        "rowCount": len(rows),
        "columnCount": len(columns),
        "target": request.target,
        "targetPresent": bool(request.target and request.target in columns),
        "columns": profiles,
        "profiledAt": _now(),
    }
    record["datasetHash"] = _hash({"rows": rows, "target": request.target})
    record["profileHash"] = _hash(record)
    return {"ok": True, "profile": record, "profileHash": record["profileHash"]}


def build_split_plan(request: SplitPlanRequest) -> dict[str, Any]:
    fractions = [request.train_fraction, request.validation_fraction, request.test_fraction]
    if any(value < 0 for value in fractions) or sum(fractions) <= 0:
        raise ValueError("split fractions must be non-negative and sum to a positive value")
    total = sum(fractions)
    normalized = [value / total for value in fractions]
    train = int(math.floor(request.record_count * normalized[0]))
    validation = int(math.floor(request.record_count * normalized[1]))
    test = request.record_count - train - validation
    warnings: list[str] = []
    if min(train, validation, test) < 1:
        warnings.append("one or more partitions contain fewer than one record")
    if request.strategy == "time" and not request.timestamp_field:
        warnings.append("time-based splitting requires a timestamp field")
    if request.strategy == "group" and not request.group_field:
        warnings.append("group splitting requires a group field")
    plan = {
        "schema": SPLIT_SCHEMA,
        "version": VERSION,
        "strategy": request.strategy,
        "recordCount": request.record_count,
        "counts": {"train": train, "validation": validation, "test": test},
        "fractions": {"train": _round(normalized[0]), "validation": _round(normalized[1]), "test": _round(normalized[2])},
        "seed": request.seed,
        "timestampField": request.timestamp_field,
        "groupField": request.group_field,
        "warnings": warnings,
        "leakageBoundary": "fit preprocessing only on the training partition",
        "createdAt": _now(),
    }
    plan["splitHash"] = _hash(plan)
    return {"ok": True, "plan": plan, "splitHash": plan["splitHash"]}


def build_feature_plan(request: FeaturePlanRequest) -> dict[str, Any]:
    columns = list(dict.fromkeys(str(item) for item in request.columns if str(item).strip()))
    excluded: dict[str, str] = {}
    excluded[request.target] = "target"
    for item in request.identifiers:
        excluded[item] = "identifier"
    for item in request.protected_attributes:
        excluded[item] = "protected attribute; retain only for auditing unless explicitly justified"
    if request.timestamp_field:
        excluded[request.timestamp_field] = "timestamp; engineer only with time-aware validation"
    candidates = [column for column in columns if column not in excluded]
    plan = {
        "schema": FEATURE_SCHEMA,
        "version": VERSION,
        "target": request.target,
        "candidateFeatures": candidates,
        "excluded": [{"column": key, "reason": value} for key, value in excluded.items() if key],
        "transformations": request.transformations,
        "fitBoundary": "all learned transformations must be fit on training data only",
        "featureCount": len(candidates),
        "createdAt": _now(),
    }
    plan["featurePlanHash"] = _hash(plan)
    return {"ok": True, "plan": plan, "featurePlanHash": plan["featurePlanHash"]}


def evaluate_regression(request: RegressionEvaluationRequest) -> dict[str, Any]:
    if len(request.y_true) != len(request.y_pred) or not request.y_true:
        raise ValueError("y_true and y_pred must be non-empty and equal length")
    errors = [pred - actual for actual, pred in zip(request.y_true, request.y_pred)]
    absolute = [abs(value) for value in errors]
    squared = [value * value for value in errors]
    y_mean = mean(request.y_true)
    ss_total = sum((value - y_mean) ** 2 for value in request.y_true)
    ss_residual = sum(squared)
    nonzero = [(actual, pred) for actual, pred in zip(request.y_true, request.y_pred) if actual != 0]
    metrics = {
        "mae": _round(mean(absolute)),
        "mse": _round(mean(squared)),
        "rmse": _round(math.sqrt(mean(squared))),
        "r2": _round(1 - ss_residual / ss_total) if ss_total else None,
        "mape": _round(mean(abs((actual - pred) / actual) for actual, pred in nonzero)) if nonzero else None,
        "bias": _round(mean(errors)),
        "count": len(errors),
    }
    if request.baseline:
        if len(request.baseline) != len(request.y_true):
            raise ValueError("baseline must match y_true length")
        baseline_mae = mean(abs(pred - actual) for actual, pred in zip(request.y_true, request.baseline))
        metrics["baselineMae"] = _round(baseline_mae)
        metrics["maeImprovement"] = _round(baseline_mae - mean(absolute))
    record = {"schema": EVALUATION_SCHEMA, "version": VERSION, "task": "regression", "metrics": metrics, "evaluatedAt": _now()}
    record["evaluationHash"] = _hash(record)
    return {"ok": True, "evaluation": record, "evaluationHash": record["evaluationHash"]}


def evaluate_classification(request: ClassificationEvaluationRequest) -> dict[str, Any]:
    if len(request.y_true) != len(request.y_pred) or not request.y_true:
        raise ValueError("y_true and y_pred must be non-empty and equal length")
    positive = request.positive_label
    tp = sum(1 for actual, pred in zip(request.y_true, request.y_pred) if actual == positive and pred == positive)
    tn = sum(1 for actual, pred in zip(request.y_true, request.y_pred) if actual != positive and pred != positive)
    fp = sum(1 for actual, pred in zip(request.y_true, request.y_pred) if actual != positive and pred == positive)
    fn = sum(1 for actual, pred in zip(request.y_true, request.y_pred) if actual == positive and pred != positive)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    metrics = {
        "accuracy": _round((tp + tn) / len(request.y_true)),
        "precision": _round(precision),
        "recall": _round(recall),
        "f1": _round(2 * precision * recall / (precision + recall)) if precision + recall else 0.0,
        "specificity": _round(tn / (tn + fp)) if tn + fp else 0.0,
        "confusionMatrix": {"truePositive": tp, "trueNegative": tn, "falsePositive": fp, "falseNegative": fn},
        "positiveLabel": positive,
        "count": len(request.y_true),
    }
    record = {"schema": EVALUATION_SCHEMA, "version": VERSION, "task": "classification", "metrics": metrics, "evaluatedAt": _now()}
    record["evaluationHash"] = _hash(record)
    return {"ok": True, "evaluation": record, "evaluationHash": record["evaluationHash"]}


def summarize_cross_validation(request: CrossValidationRequest) -> dict[str, Any]:
    if not request.folds:
        raise ValueError("at least one fold is required")
    values = [float(fold[request.primary_metric]) for fold in request.folds if request.primary_metric in fold]
    if len(values) != len(request.folds):
        raise ValueError("every fold must contain the primary metric")
    summary = {
        "schema": CV_SCHEMA,
        "version": VERSION,
        "primaryMetric": request.primary_metric,
        "direction": request.direction,
        "foldCount": len(values),
        "mean": _round(mean(values)),
        "standardDeviation": _round(pstdev(values)) if len(values) > 1 else 0.0,
        "minimum": _round(min(values)),
        "maximum": _round(max(values)),
        "bestFold": values.index(max(values) if request.direction == "maximize" else min(values)) + 1,
        "folds": request.folds,
        "createdAt": _now(),
    }
    summary["crossValidationHash"] = _hash(summary)
    return {"ok": True, "summary": summary, "crossValidationHash": summary["crossValidationHash"]}


def build_linear_trend_forecast(request: ForecastRequest) -> dict[str, Any]:
    values = [float(value) for value in request.values]
    if len(values) < 3:
        raise ValueError("at least three observations are required")
    x_mean = (len(values) - 1) / 2
    y_mean = mean(values)
    denominator = sum((index - x_mean) ** 2 for index in range(len(values)))
    slope = sum((index - x_mean) * (value - y_mean) for index, value in enumerate(values)) / denominator if denominator else 0.0
    intercept = y_mean - slope * x_mean
    fitted = [intercept + slope * index for index in range(len(values))]
    residuals = [actual - predicted for actual, predicted in zip(values, fitted)]
    residual_std = pstdev(residuals) if len(residuals) > 1 else 0.0
    predictions = []
    for step in range(1, request.horizon + 1):
        index = len(values) + step - 1
        predicted = intercept + slope * index
        width = request.confidence_z * residual_std * math.sqrt(1 + step / len(values))
        predictions.append({"step": step, "value": _round(predicted), "lower": _round(predicted - width), "upper": _round(predicted + width)})
    record = {
        "schema": FORECAST_SCHEMA,
        "version": VERSION,
        "method": "linear-trend",
        "observations": len(values),
        "horizon": request.horizon,
        "slope": _round(slope),
        "intercept": _round(intercept),
        "residualStandardDeviation": _round(residual_std),
        "predictions": predictions,
        "limitations": ["linear trend does not represent seasonality, structural breaks, or causal effects"],
        "createdAt": _now(),
    }
    record["forecastHash"] = _hash(record)
    return {"ok": True, "forecast": record, "forecastHash": record["forecastHash"]}


def _psi(reference: list[float], current: list[float], bins: int) -> float:
    low = min(reference + current)
    high = max(reference + current)
    if low == high:
        return 0.0
    width = (high - low) / bins
    epsilon = 1e-6
    score = 0.0
    for index in range(bins):
        left = low + index * width
        right = high if index == bins - 1 else left + width
        ref_count = sum(1 for value in reference if ((left <= value <= right) if index == bins - 1 else (left <= value < right)))
        cur_count = sum(1 for value in current if ((left <= value <= right) if index == bins - 1 else (left <= value < right)))
        ref_fraction = max(ref_count / len(reference), epsilon)
        cur_fraction = max(cur_count / len(current), epsilon)
        score += (cur_fraction - ref_fraction) * math.log(cur_fraction / ref_fraction)
    return score


def audit_drift(request: DriftAuditRequest) -> dict[str, Any]:
    reference = [float(value) for value in request.reference]
    current = [float(value) for value in request.current]
    if len(reference) < 2 or len(current) < 2:
        raise ValueError("reference and current samples require at least two values")
    ref_std = pstdev(reference)
    standardized_shift = abs(mean(current) - mean(reference)) / ref_std if ref_std else (0.0 if mean(current) == mean(reference) else math.inf)
    psi = _psi(reference, current, request.bins)
    severity = "critical" if psi >= request.critical_threshold else "warning" if psi >= request.warning_threshold else "stable"
    record = {
        "schema": DRIFT_SCHEMA,
        "version": VERSION,
        "referenceCount": len(reference),
        "currentCount": len(current),
        "referenceMean": _round(mean(reference)),
        "currentMean": _round(mean(current)),
        "standardizedMeanShift": _round(standardized_shift) if math.isfinite(standardized_shift) else None,
        "populationStabilityIndex": _round(psi),
        "severity": severity,
        "thresholds": {"warning": request.warning_threshold, "critical": request.critical_threshold},
        "action": "review data and model performance before continued use" if severity != "stable" else "continue monitoring",
        "auditedAt": _now(),
    }
    record["driftHash"] = _hash(record)
    return {"ok": True, "audit": record, "driftHash": record["driftHash"]}


def audit_leakage(request: LeakageAuditRequest) -> dict[str, Any]:
    target = request.target.lower().strip()
    findings: list[dict[str, str]] = []
    post_outcome = {item.lower().strip() for item in request.known_post_outcome_fields}
    suspicious_tokens = ("outcome", "result", "approved", "diagnosis", "disposition", "after", "future", "label", "target")
    for feature in request.features:
        normalized = feature.lower().strip()
        if normalized == target:
            findings.append({"feature": feature, "severity": "critical", "reason": "target included as a feature"})
        elif normalized in post_outcome:
            findings.append({"feature": feature, "severity": "critical", "reason": "known post-outcome field"})
        elif any(token in normalized for token in suspicious_tokens):
            findings.append({"feature": feature, "severity": "warning", "reason": "name suggests post-outcome or label-derived information"})
    if request.split_strategy.lower() == "random" and request.timestamp_field:
        findings.append({"feature": request.timestamp_field, "severity": "warning", "reason": "random split may leak future information; consider a time split"})
    record = {
        "schema": LEAKAGE_SCHEMA,
        "version": VERSION,
        "target": request.target,
        "splitStrategy": request.split_strategy,
        "findingCount": len(findings),
        "criticalCount": sum(1 for item in findings if item["severity"] == "critical"),
        "findings": findings,
        "fitBoundary": "preprocessing, imputation, encoding, scaling, and feature selection must be fit on training data only",
        "status": "blocked" if any(item["severity"] == "critical" for item in findings) else "review" if findings else "clear",
        "auditedAt": _now(),
    }
    record["leakageHash"] = _hash(record)
    return {"ok": True, "audit": record, "leakageHash": record["leakageHash"]}


def audit_fairness(request: FairnessAuditRequest) -> dict[str, Any]:
    if len(request.groups) < 2:
        raise ValueError("at least two groups are required")
    metrics = ("positive_rate", "true_positive_rate", "false_positive_rate", "error_rate")
    gaps: dict[str, float | None] = {}
    for metric in metrics:
        values = [getattr(group, metric) for group in request.groups if getattr(group, metric) is not None]
        gaps[metric] = _round(max(values) - min(values)) if len(values) >= 2 else None
    max_gap = max((value for value in gaps.values() if value is not None), default=0.0)
    severity = "critical" if max_gap >= request.critical_gap else "warning" if max_gap >= request.warning_gap else "stable"
    small = [group.group for group in request.groups if group.count < request.minimum_group_size]
    record = {
        "schema": FAIRNESS_SCHEMA,
        "version": VERSION,
        "groups": [group.model_dump() for group in request.groups],
        "gaps": {
            "positiveRate": gaps["positive_rate"],
            "truePositiveRate": gaps["true_positive_rate"],
            "falsePositiveRate": gaps["false_positive_rate"],
            "errorRate": gaps["error_rate"],
        },
        "maximumObservedGap": _round(max_gap),
        "severity": severity,
        "smallGroups": small,
        "minimumGroupSize": request.minimum_group_size,
        "limitations": ["group metrics do not establish causation or legal compliance", "small groups can produce unstable estimates"],
        "humanReviewRequired": True,
        "auditedAt": _now(),
    }
    record["fairnessHash"] = _hash(record)
    return {"ok": True, "audit": record, "fairnessHash": record["fairnessHash"]}


def build_model_card(request: ModelCardRequest) -> dict[str, Any]:
    prohibited = list(dict.fromkeys(request.prohibited_uses + [
        "fully autonomous high-stakes decisions without qualified human review",
        "use outside documented data, population, geography, or time boundaries without revalidation",
    ]))
    status = request.approval_status
    warnings: list[str] = []
    if status == "approved" and not request.reviewer.strip():
        status = "review-required"
        warnings.append("approval was downgraded because no reviewer was recorded")
    card = {
        "schema": MODEL_CARD_SCHEMA,
        "version": VERSION,
        "modelId": _slug(request.model_name, "model"),
        "modelName": request.model_name,
        "task": request.task,
        "algorithm": request.algorithm,
        "datasetHash": request.dataset_hash,
        "features": request.features,
        "metrics": request.metrics,
        "intendedUses": request.intended_uses,
        "prohibitedUses": prohibited,
        "limitations": request.limitations,
        "fairness": request.fairness,
        "drift": request.drift,
        "reviewer": request.reviewer,
        "approvalStatus": status,
        "warnings": warnings,
        "humanReviewRequired": True,
        "createdAt": _now(),
    }
    card["modelCardHash"] = _hash(card)
    return {"ok": True, "modelCard": card, "modelCardHash": card["modelCardHash"]}


def build_reproducibility_plan(request: ReproducibilityRequest) -> dict[str, Any]:
    supported = [language for language in request.languages if language.lower() in {"python", "r", "javascript", "rust"}]
    if not supported:
        raise ValueError("at least one supported language is required")
    coefficients = ", ".join(str(float(value)) for value in request.coefficients)
    snippets = {
        "python": f"def predict(x):\n    coefficients = [{coefficients}]\n    return {float(request.intercept)} + sum(a*b for a,b in zip(coefficients, x))",
        "r": f"predict_value <- function(x) {{ coefficients <- c({coefficients}); {float(request.intercept)} + sum(coefficients * x) }}",
        "javascript": f"const predict = x => {float(request.intercept)} + [{coefficients}].reduce((s,c,i) => s + c*x[i], 0);",
        "rust": f"fn predict(x: &[f64]) -> f64 {{ let coefficients = [{coefficients}]; {float(request.intercept)} + coefficients.iter().zip(x).map(|(a,b)| a*b).sum::<f64>() }}",
    }
    plan = {
        "schema": REPRO_SCHEMA,
        "version": VERSION,
        "modelType": request.model_type,
        "languages": supported,
        "seed": request.seed,
        "absoluteTolerance": request.tolerance,
        "inputOrderingRequired": True,
        "numericContract": "IEEE-754 double precision where available",
        "snippets": {language: snippets[language.lower()] for language in supported},
        "validation": ["run identical fixtures", "compare outputs within tolerance", "record runtime and library versions", "fail on missing or reordered features"],
        "createdAt": _now(),
    }
    plan["reproducibilityHash"] = _hash(plan)
    return {"ok": True, "plan": plan, "reproducibilityHash": plan["reproducibilityHash"]}


def build_experiment_scaffold(request: ExperimentScaffoldRequest) -> dict[str, Any]:
    if request.task in {"regression", "classification", "forecasting", "deep-learning"} and not request.target:
        raise ValueError("the selected task requires a target")
    controls = [
        "preserve an untouched test partition",
        "fit preprocessing on training data only",
        "record random seeds and dependency versions",
        "compare against a transparent baseline",
        "evaluate uncertainty, leakage, drift, and subgroup performance",
    ]
    if request.task == "deep-learning":
        controls += ["use early stopping", "save best-validation checkpoint", "calibrate outputs when probabilities are reported", "document architecture and parameter count"]
    if request.high_stakes_context:
        controls += ["independent qualified review is required", "do not automate final eligibility, diagnosis, employment, credit, safety, or legal decisions"]
    scaffold = {
        "schema": EXPERIMENT_SCHEMA,
        "version": VERSION,
        "experimentId": _slug(request.experiment_name, "experiment"),
        "projectId": _slug(request.project_id, "default"),
        "experimentName": request.experiment_name,
        "task": request.task,
        "datasetId": _slug(request.dataset_id, "dataset"),
        "target": request.target,
        "features": request.features,
        "validationStrategy": request.validation_strategy,
        "seed": request.seed,
        "stages": ["profile", "split", "features", "baseline", "train", "validate", "stress-test", "document", "review"],
        "controls": controls,
        "highStakesContext": request.high_stakes_context,
        "humanReviewRequired": True,
        "createdAt": _now(),
    }
    scaffold["experimentHash"] = _hash(scaffold)
    return {"ok": True, "experiment": scaffold, "experimentHash": scaffold["experimentHash"]}


def _route(function, request):
    try:
        return function(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "schema": "sc-workbench-computational-intelligence-status/1.0",
        "capabilities": ["dataset-profiling", "split-planning", "feature-planning", "regression", "classification", "cross-validation", "forecasting", "drift", "leakage", "fairness", "model-cards", "cross-language-reproducibility", "experiment-scaffolds"],
        "trainingExecution": False,
        "highStakesAutomation": False,
    }


@router.post("/dataset/profile")
def route_dataset_profile(request: DatasetProfileRequest): return _route(profile_dataset, request)


@router.post("/split/plan")
def route_split_plan(request: SplitPlanRequest): return _route(build_split_plan, request)


@router.post("/feature/plan")
def route_feature_plan(request: FeaturePlanRequest): return _route(build_feature_plan, request)


@router.post("/evaluate/regression")
def route_regression(request: RegressionEvaluationRequest): return _route(evaluate_regression, request)


@router.post("/evaluate/classification")
def route_classification(request: ClassificationEvaluationRequest): return _route(evaluate_classification, request)


@router.post("/cross-validation/summarize")
def route_cross_validation(request: CrossValidationRequest): return _route(summarize_cross_validation, request)


@router.post("/forecast/linear-trend")
def route_forecast(request: ForecastRequest): return _route(build_linear_trend_forecast, request)


@router.post("/drift/audit")
def route_drift(request: DriftAuditRequest): return _route(audit_drift, request)


@router.post("/leakage/audit")
def route_leakage(request: LeakageAuditRequest): return _route(audit_leakage, request)


@router.post("/fairness/audit")
def route_fairness(request: FairnessAuditRequest): return _route(audit_fairness, request)


@router.post("/model-card/build")
def route_model_card(request: ModelCardRequest): return _route(build_model_card, request)


@router.post("/reproducibility/plan")
def route_reproducibility(request: ReproducibilityRequest): return _route(build_reproducibility_plan, request)


@router.post("/experiment/scaffold")
def route_experiment(request: ExperimentScaffoldRequest): return _route(build_experiment_scaffold, request)

"""Workbench v2.7.0 scientific visualization and engineering dashboard routes."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from statistics import mean, median, pstdev
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "2.7.0"
router = APIRouter(prefix="/v270", tags=["workbench-v270"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finite(values: list[float]) -> list[float]:
    return [float(value) for value in values if math.isfinite(float(value))]


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * min(1.0, max(0.0, probability))
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _round(value: float | int | None, digits: int = 9) -> float | int | None:
    if value is None:
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    rounded = round(numeric, digits)
    return int(rounded) if rounded.is_integer() else rounded


class SeriesSummaryRequest(BaseModel):
    values: list[float] = Field(min_length=1, max_length=200000)
    labels: list[str] = Field(default_factory=list, max_length=200000)
    units: str = Field(default="", max_length=80)
    expected_interval: float | None = Field(default=None, gt=0)


class HistogramRequest(BaseModel):
    values: list[float] = Field(min_length=1, max_length=200000)
    bins: int = Field(default=12, ge=2, le=100)
    normalize: bool = False


class DashboardMetric(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    label: str = Field(min_length=1, max_length=120)
    value: float
    units: str = Field(default="", max_length=40)
    warning_low: float | None = None
    warning_high: float | None = None
    critical_low: float | None = None
    critical_high: float | None = None
    target: float | None = None


class DashboardRequest(BaseModel):
    title: str = Field(default="Engineering dashboard", max_length=180)
    metrics: list[DashboardMetric] = Field(min_length=1, max_length=100)


class ValidationOverlayRequest(BaseModel):
    observed: list[float] = Field(min_length=2, max_length=200000)
    predicted: list[float] = Field(min_length=2, max_length=200000)
    uncertainty: list[float] | float = 0.0
    sigma_multiplier: float = Field(default=1.96, gt=0, le=10)
    labels: list[str] = Field(default_factory=list, max_length=200000)


class StateNode(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    label: str = Field(default="", max_length=120)
    state: Literal["normal", "warning", "critical", "offline", "unknown"] = "unknown"
    value: float | None = None
    units: str = Field(default="", max_length=40)


class StateEdge(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    target: str = Field(min_length=1, max_length=80)
    relation: str = Field(default="connects", max_length=80)


class SystemStateRequest(BaseModel):
    nodes: list[StateNode] = Field(min_length=1, max_length=500)
    edges: list[StateEdge] = Field(default_factory=list, max_length=2000)


class AccessibleDescriptionRequest(BaseModel):
    title: str = Field(default="Scientific visualization", max_length=180)
    chart_type: Literal["line", "scatter", "bar", "histogram", "spectrum", "spatial", "state"]
    x_label: str = Field(default="", max_length=100)
    y_label: str = Field(default="", max_length=100)
    series_label: str = Field(default="Series", max_length=100)
    x: list[float] = Field(default_factory=list, max_length=200000)
    y: list[float] = Field(min_length=1, max_length=200000)
    units: str = Field(default="", max_length=40)


@router.post("/visualization/summary")
def visualization_summary(request: SeriesSummaryRequest) -> dict[str, Any]:
    values = _finite(request.values)
    if not values:
        return {"ok": False, "version": VERSION, "error": "No finite values supplied"}
    deltas = [values[index] - values[index - 1] for index in range(1, len(values))]
    monotonic_up = all(delta >= 0 for delta in deltas)
    monotonic_down = all(delta <= 0 for delta in deltas)
    interval_findings: list[dict[str, Any]] = []
    if request.expected_interval and len(request.labels) == len(request.values):
        interval_findings.append({
            "severity": "info",
            "code": "text-label-interval-not-numerically-validated",
            "expectedInterval": request.expected_interval,
        })
    return {
        "ok": True,
        "schema": "sc-workbench-visualization-summary/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "count": len(values),
        "units": request.units,
        "statistics": {
            "minimum": _round(min(values)),
            "maximum": _round(max(values)),
            "range": _round(max(values) - min(values)),
            "mean": _round(mean(values)),
            "median": _round(median(values)),
            "standardDeviation": _round(pstdev(values) if len(values) > 1 else 0.0),
            "q05": _round(_quantile(values, 0.05)),
            "q25": _round(_quantile(values, 0.25)),
            "q75": _round(_quantile(values, 0.75)),
            "q95": _round(_quantile(values, 0.95)),
            "first": _round(values[0]),
            "last": _round(values[-1]),
            "netChange": _round(values[-1] - values[0]),
        },
        "shape": {
            "monotonicIncreasing": monotonic_up,
            "monotonicDecreasing": monotonic_down,
            "turningPoints": sum(1 for index in range(1, len(deltas)) if deltas[index] * deltas[index - 1] < 0),
        },
        "findings": interval_findings,
    }


@router.post("/distribution/histogram")
def distribution_histogram(request: HistogramRequest) -> dict[str, Any]:
    values = _finite(request.values)
    if not values:
        return {"ok": False, "version": VERSION, "error": "No finite values supplied"}
    lower, upper = min(values), max(values)
    if lower == upper:
        edges = [lower - 0.5, upper + 0.5]
        counts = [len(values)]
    else:
        width = (upper - lower) / request.bins
        edges = [lower + width * index for index in range(request.bins + 1)]
        counts = [0] * request.bins
        for value in values:
            index = min(request.bins - 1, int((value - lower) / width))
            counts[index] += 1
    denominator = len(values) if request.normalize else 1
    bins = [
        {
            "lower": _round(edges[index]),
            "upper": _round(edges[index + 1]),
            "count": counts[index],
            "value": _round(counts[index] / denominator),
        }
        for index in range(len(counts))
    ]
    return {
        "ok": True,
        "schema": "sc-workbench-histogram/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "normalized": request.normalize,
        "sampleCount": len(values),
        "bins": bins,
    }


def _metric_status(metric: DashboardMetric) -> tuple[str, list[str]]:
    value = metric.value
    reasons: list[str] = []
    if metric.critical_low is not None and value < metric.critical_low:
        reasons.append("below-critical-low")
    if metric.critical_high is not None and value > metric.critical_high:
        reasons.append("above-critical-high")
    if reasons:
        return "critical", reasons
    if metric.warning_low is not None and value < metric.warning_low:
        reasons.append("below-warning-low")
    if metric.warning_high is not None and value > metric.warning_high:
        reasons.append("above-warning-high")
    return ("warning", reasons) if reasons else ("normal", ["within-configured-boundary"])


@router.post("/dashboard/evaluate")
def evaluate_dashboard(request: DashboardRequest) -> dict[str, Any]:
    evaluated = []
    counts = {"normal": 0, "warning": 0, "critical": 0}
    for metric in request.metrics:
        status, reasons = _metric_status(metric)
        counts[status] += 1
        target_error = None if metric.target is None else metric.value - metric.target
        evaluated.append({
            "key": metric.key,
            "label": metric.label,
            "value": _round(metric.value),
            "units": metric.units,
            "status": status,
            "reasons": reasons,
            "target": _round(metric.target),
            "targetError": _round(target_error),
        })
    overall = "critical" if counts["critical"] else "warning" if counts["warning"] else "normal"
    return {
        "ok": overall != "critical",
        "schema": "sc-workbench-engineering-dashboard/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "title": request.title,
        "overallStatus": overall,
        "statusCounts": counts,
        "metrics": evaluated,
    }


@router.post("/validation/overlay")
def validation_overlay(request: ValidationOverlayRequest) -> dict[str, Any]:
    if len(request.observed) != len(request.predicted):
        return {"ok": False, "version": VERSION, "error": "Observed and predicted arrays must have equal lengths"}
    observed = _finite(request.observed)
    predicted = _finite(request.predicted)
    if len(observed) != len(request.observed) or len(predicted) != len(request.predicted):
        return {"ok": False, "version": VERSION, "error": "Inputs must contain only finite values"}
    if isinstance(request.uncertainty, list):
        uncertainty = _finite(request.uncertainty)
        if len(uncertainty) != len(observed):
            return {"ok": False, "version": VERSION, "error": "Uncertainty must be scalar or match the series length"}
    else:
        uncertainty = [max(0.0, float(request.uncertainty))] * len(observed)
    residuals = [obs - pred for obs, pred in zip(observed, predicted)]
    bands = []
    covered = 0
    for index, (obs, pred, sigma) in enumerate(zip(observed, predicted, uncertainty)):
        half_width = request.sigma_multiplier * abs(sigma)
        low, high = pred - half_width, pred + half_width
        is_covered = low <= obs <= high
        covered += int(is_covered)
        bands.append({
            "index": index,
            "label": request.labels[index] if index < len(request.labels) else str(index + 1),
            "observed": _round(obs),
            "predicted": _round(pred),
            "lower": _round(low),
            "upper": _round(high),
            "residual": _round(obs - pred),
            "covered": is_covered,
        })
    mse = mean([residual * residual for residual in residuals])
    observed_mean = mean(observed)
    total = sum((value - observed_mean) ** 2 for value in observed)
    unexplained = sum(residual * residual for residual in residuals)
    r_squared = 1.0 - unexplained / total if total > 0 else (1.0 if unexplained == 0 else 0.0)
    return {
        "ok": True,
        "schema": "sc-workbench-validation-overlay/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "metrics": {
            "rmse": _round(math.sqrt(mse)),
            "mae": _round(mean([abs(value) for value in residuals])),
            "bias": _round(mean(residuals)),
            "rSquared": _round(r_squared),
            "coverageFraction": _round(covered / len(observed)),
            "coverageCount": covered,
            "sampleCount": len(observed),
        },
        "sigmaMultiplier": request.sigma_multiplier,
        "points": bands,
    }


@router.post("/system-state/analyze")
def analyze_system_state(request: SystemStateRequest) -> dict[str, Any]:
    identifiers = [node.id for node in request.nodes]
    duplicate_ids = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
    known = set(identifiers)
    unknown_edges = [edge.model_dump() if hasattr(edge, "model_dump") else edge.dict() for edge in request.edges if edge.source not in known or edge.target not in known]
    adjacency: dict[str, list[str]] = {identifier: [] for identifier in known}
    for edge in request.edges:
        if edge.source in known and edge.target in known:
            adjacency[edge.source].append(edge.target)
    roots = sorted(identifier for identifier in known if not any(identifier in targets for targets in adjacency.values()))
    leaves = sorted(identifier for identifier, targets in adjacency.items() if not targets)
    status_counts = {state: 0 for state in ["normal", "warning", "critical", "offline", "unknown"]}
    for node in request.nodes:
        status_counts[node.state] += 1
    findings = []
    if duplicate_ids:
        findings.append({"severity": "error", "code": "duplicate-node-id", "nodes": duplicate_ids})
    if unknown_edges:
        findings.append({"severity": "error", "code": "edge-references-unknown-node", "edges": unknown_edges})
    if status_counts["critical"]:
        findings.append({"severity": "critical", "code": "critical-node-present", "count": status_counts["critical"]})
    if status_counts["offline"]:
        findings.append({"severity": "warning", "code": "offline-node-present", "count": status_counts["offline"]})
    if not findings:
        findings.append({"severity": "pass", "code": "state-graph-structurally-valid"})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-system-state-view/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "nodeCount": len(request.nodes),
        "edgeCount": len(request.edges),
        "statusCounts": status_counts,
        "roots": roots,
        "leaves": leaves,
        "findings": findings,
    }


@router.post("/accessibility/describe")
def accessible_description(request: AccessibleDescriptionRequest) -> dict[str, Any]:
    values = _finite(request.y)
    if not values:
        return {"ok": False, "version": VERSION, "error": "No finite y values supplied"}
    minimum, maximum = min(values), max(values)
    min_index, max_index = values.index(minimum), values.index(maximum)
    direction = "increases" if values[-1] > values[0] else "decreases" if values[-1] < values[0] else "ends unchanged"
    unit_text = f" {request.units}" if request.units else ""
    description = (
        f"{request.title} is a {request.chart_type} visualization of {request.series_label}. "
        f"It contains {len(values)} observations. Values range from {_round(minimum)}{unit_text} "
        f"at observation {min_index + 1} to {_round(maximum)}{unit_text} at observation {max_index + 1}. "
        f"The series {direction} overall, moving from {_round(values[0])}{unit_text} to {_round(values[-1])}{unit_text}. "
        f"The mean is {_round(mean(values))}{unit_text} and the median is {_round(median(values))}{unit_text}."
    )
    table = [
        {
            "index": index + 1,
            "x": _round(request.x[index]) if index < len(request.x) else index + 1,
            "y": _round(value),
        }
        for index, value in enumerate(values[:1000])
    ]
    return {
        "ok": True,
        "schema": "sc-workbench-accessible-visualization/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "description": description,
        "axisSummary": {"x": request.x_label, "y": request.y_label, "units": request.units},
        "dataTable": table,
        "tableTruncated": len(values) > 1000,
    }

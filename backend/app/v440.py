"""Workbench v4.4.0 — Automated Evaluation, Benchmarking, and Comparison Laboratory."""
from __future__ import annotations

from itertools import product
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import statistics
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "4.4.0"
EXPECTED_STUDIOS = 26
router = APIRouter(prefix="/v440", tags=["workbench-v440"])

MetricDirection = Literal["maximize", "minimize"]
TaskType = Literal["scientific", "engineering", "simulation", "forecasting", "classification", "regression", "instrumentation", "systems", "custom"]


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def slug(value: str, fallback: str = "record") -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return cleaned or fallback


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BenchmarkInput(BaseModel):
    benchmarkId: str = ""
    title: str
    domain: str = "general"
    taskType: TaskType = "custom"
    metricName: str
    direction: MetricDirection = "maximize"
    unit: str = ""
    baselineName: str = ""
    baselineValue: Optional[float] = None
    datasetHash: str = ""
    protocolHash: str = ""
    sampleSize: int = Field(default=1, ge=1)
    highStakes: bool = False
    notes: List[str] = Field(default_factory=list)


class ExperimentMatrixInput(BaseModel):
    benchmarkId: str
    candidates: List[str]
    parameterGrid: Dict[str, List[Any]] = Field(default_factory=dict)
    seeds: List[int] = Field(default_factory=lambda: [42])
    datasets: List[str] = Field(default_factory=lambda: ["default"])
    maxRuns: int = Field(default=500, ge=1, le=10000)


class TrialRecord(BaseModel):
    trialId: str = ""
    candidate: str
    metricValue: float
    seed: Optional[int] = None
    datasetHash: str = ""
    protocolHash: str = ""
    runtime: str = ""
    environmentHash: str = ""
    durationSeconds: float = Field(default=0.0, ge=0.0)
    success: bool = True
    createdAt: str = ""
    notes: List[str] = Field(default_factory=list)


class TrialSummaryInput(BaseModel):
    benchmarkId: str
    metricName: str
    direction: MetricDirection = "maximize"
    trials: List[TrialRecord]


class CandidateComparisonInput(BaseModel):
    baseline: Dict[str, Any]
    candidate: Dict[str, Any]
    direction: MetricDirection = "maximize"
    practicalThreshold: float = Field(default=0.0, ge=0.0)


class RegressionInput(BaseModel):
    baselineValue: float
    currentValue: float
    direction: MetricDirection = "maximize"
    absoluteTolerance: float = Field(default=0.0, ge=0.0)
    percentTolerance: float = Field(default=0.0, ge=0.0)
    severity: Literal["info", "review", "high", "critical"] = "high"
    label: str = "metric"


class ReproducibilityInput(BaseModel):
    trials: List[TrialRecord]
    metricTolerance: float = Field(default=1e-9, ge=0.0)
    requireSeed: bool = True
    requireDatasetHash: bool = True
    requireProtocolHash: bool = True
    requireRuntime: bool = True
    requireEnvironmentHash: bool = True


class LeaderboardEntry(BaseModel):
    candidate: str
    metricValue: float
    uncertainty: float = Field(default=0.0, ge=0.0)
    reproducibilityScore: float = Field(default=1.0, ge=0.0, le=1.0)
    valid: bool = True
    notes: List[str] = Field(default_factory=list)


class LeaderboardInput(BaseModel):
    benchmarkId: str
    metricName: str
    direction: MetricDirection = "maximize"
    entries: List[LeaderboardEntry]


class EvaluationGateInput(BaseModel):
    benchmark: Dict[str, Any]
    comparison: Dict[str, Any] = Field(default_factory=dict)
    regressions: List[Dict[str, Any]] = Field(default_factory=list)
    reproducibility: Dict[str, Any] = Field(default_factory=dict)
    unresolvedFindings: List[Dict[str, Any]] = Field(default_factory=list)
    requiredArtifacts: List[str] = Field(default_factory=list)
    availableArtifacts: List[str] = Field(default_factory=list)
    humanApproval: bool = False
    approver: str = ""


class EvaluationPackageInput(BaseModel):
    benchmark: Dict[str, Any]
    matrix: Dict[str, Any]
    summaries: Dict[str, Any]
    comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    regressions: List[Dict[str, Any]] = Field(default_factory=list)
    reproducibility: Dict[str, Any] = Field(default_factory=dict)
    leaderboard: Dict[str, Any] = Field(default_factory=dict)
    gate: Dict[str, Any] = Field(default_factory=dict)


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-evaluation-laboratory-status/1.0",
        "version": VERSION,
        "expectedStudioCount": EXPECTED_STUDIOS,
        "benchmarkTaskTypes": ["scientific", "engineering", "simulation", "forecasting", "classification", "regression", "instrumentation", "systems", "custom"],
        "metricDirections": ["maximize", "minimize"],
        "browserFallback": True,
        "offlineEvaluation": True,
        "privateByDefault": True,
        "paidExternalDatabaseRequired": False,
        "automaticExperimentExecutionAuthorized": False,
        "automaticLeaderboardPublicationAuthorized": False,
        "automaticBaselineReplacementAuthorized": False,
        "automaticReleaseApprovalAuthorized": False,
        "automaticCertificationAuthorized": False,
    }


def normalize_benchmark(payload: BenchmarkInput) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    if not payload.datasetHash:
        findings.append({"level": "review", "code": "dataset-hash-missing", "message": "Attach a content hash for the evaluated dataset."})
    if not payload.protocolHash:
        findings.append({"level": "review", "code": "protocol-hash-missing", "message": "Attach a content hash for the benchmark protocol."})
    if payload.highStakes:
        findings.append({"level": "review", "code": "professional-review-required", "message": "High-stakes benchmarks require qualified domain and governance review."})
    if payload.baselineValue is not None and not payload.baselineName:
        findings.append({"level": "review", "code": "baseline-name-missing", "message": "Name the baseline associated with the baseline metric."})
    record = {
        "schema": "sc-workbench-benchmark/1.0",
        "version": VERSION,
        "benchmarkId": slug(payload.benchmarkId or payload.title, "benchmark"),
        "title": payload.title.strip(),
        "domain": slug(payload.domain, "general"),
        "taskType": payload.taskType,
        "metricName": payload.metricName.strip(),
        "direction": payload.direction,
        "unit": payload.unit,
        "baseline": {"name": payload.baselineName, "value": payload.baselineValue},
        "datasetHash": payload.datasetHash,
        "protocolHash": payload.protocolHash,
        "sampleSize": payload.sampleSize,
        "highStakes": payload.highStakes,
        "notes": payload.notes,
        "findings": findings,
        "readyForExecutionPlanning": bool(payload.metricName.strip()) and not any(item["level"] == "block" for item in findings),
        "humanReviewRequired": payload.highStakes,
        "automaticExperimentExecutionAuthorized": False,
        "automaticCertificationAuthorized": False,
    }
    record["benchmarkHash"] = content_hash({k: v for k, v in record.items() if k != "benchmarkHash"})
    return record


def build_experiment_matrix(payload: ExperimentMatrixInput) -> Dict[str, Any]:
    candidates = sorted({item.strip() for item in payload.candidates if item.strip()})
    seeds = sorted(set(payload.seeds or [42]))
    datasets = sorted({item.strip() for item in (payload.datasets or ["default"]) if item.strip()}) or ["default"]
    parameter_names = sorted(payload.parameterGrid)
    parameter_values = [payload.parameterGrid[name] or [None] for name in parameter_names]
    parameter_combinations = [dict(zip(parameter_names, values)) for values in product(*parameter_values)] if parameter_names else [{}]
    projected_runs = len(candidates) * len(seeds) * len(datasets) * len(parameter_combinations)
    findings: List[Dict[str, str]] = []
    if not candidates:
        findings.append({"level": "block", "code": "candidate-required", "message": "At least one candidate is required."})
    if projected_runs > payload.maxRuns:
        findings.append({"level": "block", "code": "matrix-limit-exceeded", "message": f"Projected run count {projected_runs} exceeds maxRuns {payload.maxRuns}."})
    runs: List[Dict[str, Any]] = []
    if not any(item["level"] == "block" for item in findings):
        for candidate, dataset, seed, params in product(candidates, datasets, seeds, parameter_combinations):
            core = {"benchmarkId": slug(payload.benchmarkId, "benchmark"), "candidate": candidate, "dataset": dataset, "seed": seed, "parameters": params}
            runs.append({**core, "runId": "run-" + content_hash(core)[:16], "requiresExplicitExecution": True})
    result = {
        "schema": "sc-workbench-experiment-matrix/1.0",
        "version": VERSION,
        "benchmarkId": slug(payload.benchmarkId, "benchmark"),
        "candidates": candidates,
        "datasets": datasets,
        "seeds": seeds,
        "parameterGrid": {name: payload.parameterGrid[name] for name in parameter_names},
        "projectedRuns": projected_runs,
        "runs": runs,
        "findings": findings,
        "ready": not any(item["level"] == "block" for item in findings),
        "requiresExplicitExecution": True,
        "automaticExperimentExecutionAuthorized": False,
    }
    result["matrixHash"] = content_hash({k: v for k, v in result.items() if k != "matrixHash"})
    return result


def _summary(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "stdev": None, "minimum": None, "maximum": None, "standardError": None, "ci95": [None, None]}
    mean = statistics.fmean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0.0
    standard_error = stdev / math.sqrt(len(values)) if values else 0.0
    margin = 1.96 * standard_error
    return {
        "count": len(values),
        "mean": mean,
        "median": statistics.median(values),
        "stdev": stdev,
        "minimum": min(values),
        "maximum": max(values),
        "standardError": standard_error,
        "ci95": [mean - margin, mean + margin],
    }


def summarize_trials(payload: TrialSummaryInput) -> Dict[str, Any]:
    grouped: Dict[str, List[TrialRecord]] = {}
    for trial in payload.trials:
        grouped.setdefault(trial.candidate.strip() or "unnamed", []).append(trial)
    candidates: Dict[str, Any] = {}
    for candidate in sorted(grouped):
        trials = grouped[candidate]
        successful = [trial.metricValue for trial in trials if trial.success]
        summary = _summary(successful)
        summary.update({
            "candidate": candidate,
            "failureCount": len(trials) - len(successful),
            "trialCount": len(trials),
            "datasetHashes": sorted({trial.datasetHash for trial in trials if trial.datasetHash}),
            "protocolHashes": sorted({trial.protocolHash for trial in trials if trial.protocolHash}),
            "runtimes": sorted({trial.runtime for trial in trials if trial.runtime}),
        })
        summary["summaryHash"] = content_hash({k: v for k, v in summary.items() if k != "summaryHash"})
        candidates[candidate] = summary
    result = {
        "schema": "sc-workbench-trial-summary/1.0",
        "version": VERSION,
        "benchmarkId": slug(payload.benchmarkId, "benchmark"),
        "metricName": payload.metricName,
        "direction": payload.direction,
        "candidateCount": len(candidates),
        "trialCount": len(payload.trials),
        "candidates": candidates,
        "generatedAt": utc_now(),
        "automaticWinnerDeclarationAuthorized": False,
    }
    result["reportHash"] = content_hash({k: v for k, v in result.items() if k not in {"reportHash", "generatedAt"}})
    return result


def compare_candidates(payload: CandidateComparisonInput) -> Dict[str, Any]:
    baseline_mean = float(payload.baseline.get("mean", payload.baseline.get("metricValue", 0.0)))
    candidate_mean = float(payload.candidate.get("mean", payload.candidate.get("metricValue", 0.0)))
    raw_delta = candidate_mean - baseline_mean
    aligned_improvement = raw_delta if payload.direction == "maximize" else -raw_delta
    percent_change = (raw_delta / abs(baseline_mean) * 100.0) if baseline_mean != 0 else None
    practical = aligned_improvement > payload.practicalThreshold
    baseline_stdev = float(payload.baseline.get("stdev") or 0.0)
    candidate_stdev = float(payload.candidate.get("stdev") or 0.0)
    pooled = math.sqrt((baseline_stdev ** 2 + candidate_stdev ** 2) / 2.0) if baseline_stdev or candidate_stdev else 0.0
    effect_size = raw_delta / pooled if pooled else None
    result = {
        "schema": "sc-workbench-candidate-comparison/1.0",
        "version": VERSION,
        "direction": payload.direction,
        "baselineMean": baseline_mean,
        "candidateMean": candidate_mean,
        "rawDelta": raw_delta,
        "alignedImprovement": aligned_improvement,
        "percentChange": percent_change,
        "practicalThreshold": payload.practicalThreshold,
        "practicallySignificant": practical,
        "effectSize": effect_size,
        "result": "improved" if aligned_improvement > payload.practicalThreshold else ("degraded" if aligned_improvement < -payload.practicalThreshold else "equivalent"),
        "statisticalClaimAuthorized": False,
        "automaticBaselineReplacementAuthorized": False,
    }
    result["comparisonHash"] = content_hash({k: v for k, v in result.items() if k != "comparisonHash"})
    return result


def detect_regression(payload: RegressionInput) -> Dict[str, Any]:
    raw_delta = payload.currentValue - payload.baselineValue
    aligned_delta = raw_delta if payload.direction == "maximize" else -raw_delta
    degradation = max(0.0, -aligned_delta)
    degradation_percent = (degradation / abs(payload.baselineValue) * 100.0) if payload.baselineValue != 0 else (100.0 if degradation else 0.0)
    regression = degradation > payload.absoluteTolerance and degradation_percent > payload.percentTolerance
    result = {
        "schema": "sc-workbench-regression-detection/1.0",
        "version": VERSION,
        "label": payload.label,
        "direction": payload.direction,
        "baselineValue": payload.baselineValue,
        "currentValue": payload.currentValue,
        "rawDelta": raw_delta,
        "degradation": degradation,
        "degradationPercent": degradation_percent,
        "absoluteTolerance": payload.absoluteTolerance,
        "percentTolerance": payload.percentTolerance,
        "regression": regression,
        "severity": payload.severity if regression else "none",
        "releaseBlocking": regression and payload.severity in {"high", "critical"},
        "automaticRollbackAuthorized": False,
    }
    result["regressionHash"] = content_hash({k: v for k, v in result.items() if k != "regressionHash"})
    return result


def reproducibility_audit(payload: ReproducibilityInput) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    required_checks = [
        ("seed", payload.requireSeed, lambda trial: trial.seed is not None),
        ("dataset-hash", payload.requireDatasetHash, lambda trial: bool(trial.datasetHash)),
        ("protocol-hash", payload.requireProtocolHash, lambda trial: bool(trial.protocolHash)),
        ("runtime", payload.requireRuntime, lambda trial: bool(trial.runtime)),
        ("environment-hash", payload.requireEnvironmentHash, lambda trial: bool(trial.environmentHash)),
    ]
    for index, trial in enumerate(payload.trials):
        for code, required, check in required_checks:
            if required and not check(trial):
                findings.append({"level": "block", "code": f"missing-{code}", "trialIndex": index, "candidate": trial.candidate})
    grouped: Dict[str, List[float]] = {}
    for trial in payload.trials:
        key = canonical({"candidate": trial.candidate, "seed": trial.seed, "datasetHash": trial.datasetHash, "protocolHash": trial.protocolHash, "environmentHash": trial.environmentHash})
        grouped.setdefault(key, []).append(trial.metricValue)
    repeatability: List[Dict[str, Any]] = []
    for key in sorted(grouped):
        values = grouped[key]
        spread = max(values) - min(values) if values else 0.0
        repeated = len(values) > 1
        consistent = spread <= payload.metricTolerance
        repeatability.append({"configurationHash": content_hash(json.loads(key)), "repeatCount": len(values), "spread": spread, "consistent": consistent})
        if repeated and not consistent:
            findings.append({"level": "block", "code": "repeatability-failure", "configurationHash": content_hash(json.loads(key)), "spread": spread})
    ready = bool(payload.trials) and not any(item["level"] == "block" for item in findings)
    result = {
        "schema": "sc-workbench-reproducibility-audit/1.0",
        "version": VERSION,
        "trialCount": len(payload.trials),
        "metricTolerance": payload.metricTolerance,
        "repeatability": repeatability,
        "findings": findings,
        "ready": ready,
        "score": 1.0 if ready else max(0.0, 1.0 - (len(findings) / max(1, len(payload.trials) * 5))),
        "humanReviewRequired": True,
        "automaticCertificationAuthorized": False,
    }
    result["auditHash"] = content_hash({k: v for k, v in result.items() if k != "auditHash"})
    return result


def build_leaderboard(payload: LeaderboardInput) -> Dict[str, Any]:
    valid_entries = [entry for entry in payload.entries if entry.valid]
    reverse = payload.direction == "maximize"
    ordered = sorted(valid_entries, key=lambda entry: ((-entry.metricValue if reverse else entry.metricValue), entry.candidate.lower()))
    rows: List[Dict[str, Any]] = []
    last_metric: Optional[float] = None
    last_rank = 0
    for position, entry in enumerate(ordered, start=1):
        rank = last_rank if last_metric is not None and math.isclose(entry.metricValue, last_metric, rel_tol=1e-12, abs_tol=1e-12) else position
        row = {
            "rank": rank,
            "candidate": entry.candidate,
            "metricValue": entry.metricValue,
            "uncertainty": entry.uncertainty,
            "reproducibilityScore": entry.reproducibilityScore,
            "notes": entry.notes,
        }
        row["rowHash"] = content_hash({k: v for k, v in row.items() if k != "rowHash"})
        rows.append(row)
        last_metric = entry.metricValue
        last_rank = rank
    result = {
        "schema": "sc-workbench-evaluation-leaderboard/1.0",
        "version": VERSION,
        "benchmarkId": slug(payload.benchmarkId, "benchmark"),
        "metricName": payload.metricName,
        "direction": payload.direction,
        "rows": rows,
        "excludedCount": len(payload.entries) - len(valid_entries),
        "provisional": True,
        "humanReviewRequired": True,
        "automaticLeaderboardPublicationAuthorized": False,
        "automaticWinnerDeclarationAuthorized": False,
    }
    result["leaderboardHash"] = content_hash({k: v for k, v in result.items() if k != "leaderboardHash"})
    return result


def build_evaluation_gate(payload: EvaluationGateInput) -> Dict[str, Any]:
    blockers: List[Dict[str, Any]] = []
    for regression in payload.regressions:
        if regression.get("regression") and regression.get("severity") in {"high", "critical"}:
            blockers.append({"code": "blocking-regression", "detail": regression.get("label", "metric")})
    if payload.reproducibility and not payload.reproducibility.get("ready", False):
        blockers.append({"code": "reproducibility-not-ready", "detail": "Reproducibility audit contains unresolved findings."})
    for finding in payload.unresolvedFindings:
        if finding.get("level") in {"block", "high", "critical"}:
            blockers.append({"code": "unresolved-finding", "detail": finding.get("code", "finding")})
    available = set(payload.availableArtifacts)
    missing_artifacts = sorted(set(payload.requiredArtifacts) - available)
    for artifact in missing_artifacts:
        blockers.append({"code": "required-artifact-missing", "detail": artifact})
    if not payload.humanApproval:
        blockers.append({"code": "human-approval-required", "detail": "A named human approver must accept the evaluation."})
    if payload.humanApproval and not payload.approver.strip():
        blockers.append({"code": "approver-identity-required", "detail": "Record the approver identity."})
    ready = not blockers
    result = {
        "schema": "sc-workbench-evaluation-gate/1.0",
        "version": VERSION,
        "benchmarkId": payload.benchmark.get("benchmarkId", "benchmark"),
        "ready": ready,
        "state": "approved-for-human-controlled-use" if ready else "blocked",
        "blockers": blockers,
        "missingArtifacts": missing_artifacts,
        "humanApproval": payload.humanApproval,
        "approver": payload.approver,
        "evaluatedAt": utc_now(),
        "automaticReleaseApprovalAuthorized": False,
        "automaticPublicationAuthorized": False,
        "automaticBaselineReplacementAuthorized": False,
        "automaticCertificationAuthorized": False,
    }
    result["gateHash"] = content_hash({k: v for k, v in result.items() if k not in {"gateHash", "evaluatedAt"}})
    return result


def build_evaluation_package(payload: EvaluationPackageInput) -> Dict[str, Any]:
    components = {
        "benchmark": payload.benchmark,
        "matrix": payload.matrix,
        "summaries": payload.summaries,
        "comparisons": payload.comparisons,
        "regressions": payload.regressions,
        "reproducibility": payload.reproducibility,
        "leaderboard": payload.leaderboard,
        "gate": payload.gate,
    }
    component_hashes = {name: content_hash(value) for name, value in components.items()}
    result = {
        "schema": "sc-workbench-evaluation-package/1.0",
        "version": VERSION,
        "createdAt": utc_now(),
        "components": components,
        "componentHashes": component_hashes,
        "portable": True,
        "privateByDefault": True,
        "requiresExplicitImport": True,
        "requiresHumanReview": True,
        "automaticExperimentExecutionAuthorized": False,
        "automaticLeaderboardPublicationAuthorized": False,
        "automaticBaselineReplacementAuthorized": False,
        "automaticReleaseApprovalAuthorized": False,
    }
    result["packageHash"] = content_hash({k: v for k, v in result.items() if k not in {"packageHash", "createdAt"}})
    return result


@router.get("/status")
def route_status() -> Dict[str, Any]:
    return status_record()


@router.post("/benchmark/normalize")
def route_benchmark(payload: BenchmarkInput) -> Dict[str, Any]:
    return normalize_benchmark(payload)


@router.post("/matrix/build")
def route_matrix(payload: ExperimentMatrixInput) -> Dict[str, Any]:
    return build_experiment_matrix(payload)


@router.post("/trials/summarize")
def route_trials(payload: TrialSummaryInput) -> Dict[str, Any]:
    return summarize_trials(payload)


@router.post("/candidates/compare")
def route_compare(payload: CandidateComparisonInput) -> Dict[str, Any]:
    return compare_candidates(payload)


@router.post("/regression/detect")
def route_regression(payload: RegressionInput) -> Dict[str, Any]:
    return detect_regression(payload)


@router.post("/reproducibility/audit")
def route_reproducibility(payload: ReproducibilityInput) -> Dict[str, Any]:
    return reproducibility_audit(payload)


@router.post("/leaderboard/build")
def route_leaderboard(payload: LeaderboardInput) -> Dict[str, Any]:
    return build_leaderboard(payload)


@router.post("/gate/evaluate")
def route_gate(payload: EvaluationGateInput) -> Dict[str, Any]:
    return build_evaluation_gate(payload)


@router.post("/package/build")
def route_package(payload: EvaluationPackageInput) -> Dict[str, Any]:
    return build_evaluation_package(payload)

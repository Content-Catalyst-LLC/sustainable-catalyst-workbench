"""Workbench v2.8.0 experiment automation and reproducible workflow routes."""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict, deque
from datetime import datetime, timezone
from statistics import mean, pstdev
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "2.8.0"
router = APIRouter(prefix="/v280", tags=["workbench-v280"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _round(value: float | int | None, digits: int = 9) -> float | int | None:
    if value is None:
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    rounded = round(numeric, digits)
    return int(rounded) if rounded.is_integer() else rounded


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


class ProtocolStep(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=180)
    procedure: str = Field(default="", max_length=5000)
    duration_minutes: float = Field(default=0.0, ge=0, le=100000)
    dependencies: list[str] = Field(default_factory=list, max_length=50)
    required_inputs: list[str] = Field(default_factory=list, max_length=100)
    outputs: list[str] = Field(default_factory=list, max_length=100)
    checkpoint: str = Field(default="", max_length=500)


class ProtocolRequest(BaseModel):
    title: str = Field(default="Experiment protocol", max_length=180)
    objective: str = Field(default="", max_length=3000)
    operator_role: str = Field(default="", max_length=180)
    materials: list[str] = Field(default_factory=list, max_length=500)
    hazards: list[str] = Field(default_factory=list, max_length=200)
    steps: list[ProtocolStep] = Field(min_length=1, max_length=500)


class WorkflowTask(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=180)
    duration_minutes: float = Field(default=1.0, gt=0, le=100000)
    dependencies: list[str] = Field(default_factory=list, max_length=100)
    resource: str = Field(default="", max_length=100)
    command_profile: str = Field(default="manual", max_length=80)
    retry_limit: int = Field(default=0, ge=0, le=20)


class WorkflowRequest(BaseModel):
    title: str = Field(default="Reproducible workflow", max_length=180)
    tasks: list[WorkflowTask] = Field(min_length=1, max_length=1000)


class ScheduleTask(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    start_minute: int = Field(ge=0, le=525600)
    duration_minutes: int = Field(gt=0, le=525600)
    resource: str = Field(default="", max_length=100)
    repeat_every_minutes: int | None = Field(default=None, ge=1, le=525600)
    occurrences: int = Field(default=1, ge=1, le=10000)


class ScheduleRequest(BaseModel):
    tasks: list[ScheduleTask] = Field(min_length=1, max_length=1000)
    window_minutes: int = Field(default=1440, ge=1, le=525600)


class VersionManifestRequest(BaseModel):
    project_id: str = Field(default="default", max_length=120)
    dataset: Any
    configuration: Any
    code_revision: str = Field(default="", max_length=200)
    environment: dict[str, str] = Field(default_factory=dict, max_length=200)


class CheckpointRule(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    operator: Literal["between", "gte", "lte", "equal", "not_equal", "finite"] = "between"
    expected: float | str | bool | None = None
    lower: float | None = None
    upper: float | None = None
    tolerance: float = Field(default=0.0, ge=0)
    severity: Literal["info", "warning", "critical"] = "critical"


class CheckpointRequest(BaseModel):
    observed: dict[str, Any] = Field(default_factory=dict, max_length=1000)
    rules: list[CheckpointRule] = Field(min_length=1, max_length=1000)


class ReproMetric(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    values: list[float] = Field(min_length=2, max_length=10000)
    absolute_tolerance: float = Field(default=0.0, ge=0)
    relative_tolerance: float = Field(default=0.0, ge=0)


class ReproducibilityRequest(BaseModel):
    run_ids: list[str] = Field(min_length=2, max_length=10000)
    dataset_hashes: list[str] = Field(min_length=2, max_length=10000)
    configuration_hashes: list[str] = Field(min_length=2, max_length=10000)
    code_revisions: list[str] = Field(min_length=2, max_length=10000)
    metrics: list[ReproMetric] = Field(default_factory=list, max_length=500)
    deviations: list[str] = Field(default_factory=list, max_length=1000)


def _graph_findings(ids: list[str], dependencies: dict[str, list[str]]) -> tuple[list[str], list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    id_set = set(ids)
    for node, deps in dependencies.items():
        for dep in deps:
            if dep not in id_set:
                findings.append({"severity": "critical", "code": "unknown-dependency", "node": node, "dependency": dep})
        if node in deps:
            findings.append({"severity": "critical", "code": "self-dependency", "node": node})
    indegree = {node: 0 for node in ids}
    children: dict[str, list[str]] = defaultdict(list)
    for node, deps in dependencies.items():
        for dep in deps:
            if dep in indegree and dep != node:
                indegree[node] += 1
                children[dep].append(node)
    queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in sorted(children[node]):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(order) != len(ids):
        cyclic = sorted(node for node, degree in indegree.items() if degree > 0)
        findings.append({"severity": "critical", "code": "dependency-cycle", "nodes": cyclic})
    return order, findings


@router.post("/protocol/validate")
def validate_protocol(request: ProtocolRequest) -> dict[str, Any]:
    ids = [step.id for step in request.steps]
    findings: list[dict[str, Any]] = []
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        findings.append({"severity": "critical", "code": "duplicate-step-id", "steps": duplicates})
    order, graph_findings = _graph_findings(ids, {step.id: step.dependencies for step in request.steps})
    findings.extend(graph_findings)
    for step in request.steps:
        if not step.procedure.strip():
            findings.append({"severity": "warning", "code": "missing-procedure", "step": step.id})
        if not step.outputs:
            findings.append({"severity": "warning", "code": "missing-output-record", "step": step.id})
        if not step.checkpoint.strip():
            findings.append({"severity": "warning", "code": "missing-checkpoint", "step": step.id})
    total_minutes = sum(step.duration_minutes for step in request.steps)
    critical = any(item["severity"] == "critical" for item in findings)
    return {
        "ok": not critical,
        "schema": "sc-workbench-experiment-protocol/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "title": request.title,
        "objective": request.objective,
        "stepCount": len(request.steps),
        "topologicalOrder": order,
        "estimatedDurationMinutes": _round(total_minutes),
        "materialsCount": len(request.materials),
        "hazardCount": len(request.hazards),
        "findings": findings,
        "protocolHash": _sha256(request.model_dump()),
    }


@router.post("/workflow/plan")
def plan_workflow(request: WorkflowRequest) -> dict[str, Any]:
    ids = [task.id for task in request.tasks]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    order, findings = _graph_findings(ids, {task.id: task.dependencies for task in request.tasks})
    if duplicates:
        findings.append({"severity": "critical", "code": "duplicate-task-id", "tasks": duplicates})
    task_map = {task.id: task for task in request.tasks}
    earliest_finish: dict[str, float] = {}
    for task_id in order:
        task = task_map[task_id]
        start = max((earliest_finish.get(dep, 0.0) for dep in task.dependencies), default=0.0)
        earliest_finish[task_id] = start + task.duration_minutes
    duration = max(earliest_finish.values(), default=0.0)
    resource_minutes: dict[str, float] = defaultdict(float)
    for task in request.tasks:
        resource_minutes[task.resource or "unassigned"] += task.duration_minutes
    critical = any(item["severity"] == "critical" for item in findings)
    return {
        "ok": not critical,
        "schema": "sc-workbench-reproducible-workflow/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "title": request.title,
        "taskCount": len(request.tasks),
        "executionOrder": order,
        "estimatedCriticalPathMinutes": _round(duration),
        "resourceMinutes": {key: _round(value) for key, value in sorted(resource_minutes.items())},
        "retryBudget": sum(task.retry_limit for task in request.tasks),
        "findings": findings,
        "workflowHash": _sha256(request.model_dump()),
    }


@router.post("/schedule/evaluate")
def evaluate_schedule(request: ScheduleRequest) -> dict[str, Any]:
    intervals: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for task in request.tasks:
        starts = [task.start_minute]
        if task.repeat_every_minutes is not None:
            starts = [task.start_minute + index * task.repeat_every_minutes for index in range(task.occurrences)]
        for occurrence, start in enumerate(starts, start=1):
            end = start + task.duration_minutes
            record = {"task": task.id, "occurrence": occurrence, "startMinute": start, "endMinute": end, "resource": task.resource or "unassigned"}
            intervals.append(record)
            if end > request.window_minutes:
                findings.append({"severity": "warning", "code": "outside-schedule-window", **record})
    intervals.sort(key=lambda item: (item["startMinute"], item["endMinute"], item["task"]))
    by_resource: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for interval in intervals:
        by_resource[interval["resource"]].append(interval)
    for resource, records in by_resource.items():
        for left, right in zip(records, records[1:]):
            if right["startMinute"] < left["endMinute"]:
                findings.append({"severity": "critical", "code": "resource-conflict", "resource": resource, "first": left, "second": right})
    critical = any(item["severity"] == "critical" for item in findings)
    return {
        "ok": not critical,
        "schema": "sc-workbench-experiment-schedule/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "windowMinutes": request.window_minutes,
        "occurrenceCount": len(intervals),
        "intervals": intervals,
        "findings": findings,
        "note": "This plan does not install an operating-system scheduler or run unattended tasks by itself.",
    }


@router.post("/version/manifest")
def version_manifest(request: VersionManifestRequest) -> dict[str, Any]:
    dataset_hash = _sha256(request.dataset)
    configuration_hash = _sha256(request.configuration)
    environment_hash = _sha256(request.environment)
    manifest = {
        "projectId": request.project_id,
        "datasetHash": dataset_hash,
        "configurationHash": configuration_hash,
        "codeRevision": request.code_revision,
        "environmentHash": environment_hash,
    }
    return {
        "ok": True,
        "schema": "sc-workbench-experiment-version-manifest/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        **manifest,
        "manifestHash": _sha256(manifest),
    }


def _evaluate_rule(value: Any, rule: CheckpointRule) -> tuple[bool, str]:
    if rule.operator == "finite":
        try:
            return math.isfinite(float(value)), "finite-value-required"
        except (TypeError, ValueError):
            return False, "finite-value-required"
    if rule.operator in {"between", "gte", "lte"}:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return False, "numeric-value-required"
        if not math.isfinite(numeric):
            return False, "finite-value-required"
        if rule.operator == "between":
            if rule.lower is None or rule.upper is None:
                return False, "between-requires-lower-and-upper"
            return rule.lower <= numeric <= rule.upper, "outside-allowed-range"
        if rule.operator == "gte":
            if rule.lower is None:
                return False, "gte-requires-lower"
            return numeric >= rule.lower, "below-minimum"
        if rule.upper is None:
            return False, "lte-requires-upper"
        return numeric <= rule.upper, "above-maximum"
    if rule.operator in {"equal", "not_equal"}:
        expected = rule.expected
        if isinstance(expected, (int, float)) and isinstance(value, (int, float)):
            equal = abs(float(value) - float(expected)) <= rule.tolerance
        else:
            equal = value == expected
        return (equal, "outside-equality-tolerance") if rule.operator == "equal" else (not equal, "unexpected-equality")
    return False, "unsupported-operator"


@router.post("/checkpoint/evaluate")
def evaluate_checkpoint(request: CheckpointRequest) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    counts = {"pass": 0, "fail": 0}
    critical_failures = 0
    for rule in request.rules:
        present = rule.key in request.observed
        passed, reason = _evaluate_rule(request.observed.get(rule.key), rule) if present else (False, "missing-observation")
        status = "pass" if passed else "fail"
        counts[status] += 1
        if not passed and rule.severity == "critical":
            critical_failures += 1
        results.append({
            "key": rule.key,
            "status": status,
            "severity": rule.severity,
            "observed": request.observed.get(rule.key),
            "operator": rule.operator,
            "reason": "within-checkpoint-rule" if passed else reason,
        })
    return {
        "ok": critical_failures == 0,
        "schema": "sc-workbench-automatic-checkpoint/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "counts": counts,
        "criticalFailures": critical_failures,
        "results": results,
    }


@router.post("/reproducibility/compare")
def compare_reproducibility(request: ReproducibilityRequest) -> dict[str, Any]:
    run_count = len(request.run_ids)
    lengths = [len(request.dataset_hashes), len(request.configuration_hashes), len(request.code_revisions)]
    if any(length != run_count for length in lengths):
        return {"ok": False, "version": VERSION, "error": "Run metadata arrays must have equal lengths"}
    metric_results: list[dict[str, Any]] = []
    metric_failures = 0
    for metric in request.metrics:
        if len(metric.values) != run_count:
            return {"ok": False, "version": VERSION, "error": f"Metric {metric.key} must have one value per run"}
        values = [float(value) for value in metric.values]
        if not all(math.isfinite(value) for value in values):
            return {"ok": False, "version": VERSION, "error": f"Metric {metric.key} contains a non-finite value"}
        reference = values[0]
        absolute_deltas = [abs(value - reference) for value in values]
        relative_deltas = [delta / max(abs(reference), 1e-15) for delta in absolute_deltas]
        passed = max(absolute_deltas) <= metric.absolute_tolerance or max(relative_deltas) <= metric.relative_tolerance
        if not passed:
            metric_failures += 1
        metric_results.append({
            "key": metric.key,
            "status": "pass" if passed else "fail",
            "mean": _round(mean(values)),
            "standardDeviation": _round(pstdev(values)),
            "coefficientOfVariation": _round(pstdev(values) / abs(mean(values)) if mean(values) else 0.0),
            "maximumAbsoluteDelta": _round(max(absolute_deltas)),
            "maximumRelativeDelta": _round(max(relative_deltas)),
            "absoluteTolerance": metric.absolute_tolerance,
            "relativeTolerance": metric.relative_tolerance,
        })
    same_dataset = len(set(request.dataset_hashes)) == 1
    same_configuration = len(set(request.configuration_hashes)) == 1
    same_code = len(set(request.code_revisions)) == 1
    metadata_ok = same_dataset and same_configuration and same_code
    return {
        "ok": metadata_ok and metric_failures == 0 and not request.deviations,
        "schema": "sc-workbench-reproducibility-comparison/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "runCount": run_count,
        "metadataConsistency": {
            "sameDataset": same_dataset,
            "sameConfiguration": same_configuration,
            "sameCodeRevision": same_code,
        },
        "metricFailures": metric_failures,
        "metrics": metric_results,
        "deviations": request.deviations,
        "reproducibilityHash": _sha256({
            "runIds": request.run_ids,
            "datasetHashes": request.dataset_hashes,
            "configurationHashes": request.configuration_hashes,
            "codeRevisions": request.code_revisions,
            "metrics": [metric.model_dump() for metric in request.metrics],
            "deviations": request.deviations,
        }),
    }

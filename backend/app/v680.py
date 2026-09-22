"""Workbench v6.8.0 — Scenario & Uncertainty Compute Runtime Integration.

Provides a deterministic numerical execution plane for Platform Core scenario
compute and uncertainty handoffs.  Workbench consumes Core-prepared scenario
input manifests, performs explicit Workbench-owned scenario/uncertainty
computation, emits deterministic result manifests, and can prepare v6.7
computation-lineage records for Core persistence.

Platform Core remains the owner of research scenarios, uncertainty definitions,
sensitivity-study semantics, ensemble semantics, research-session context, and
provenance.  This module never dispatches to Core automatically and never
executes arbitrary code supplied by Core.
"""
from __future__ import annotations

import math
import random
import statistics
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route
from .v650 import PRODUCT_REF
from .v660 import CORE_UNIFIED_RUNTIME_CONTRACT
from .v670 import (
    CORE_COMPUTATION_LINEAGE_CONTRACT,
    ExecutionCreateRequest,
    ExecutionComponentsRequest,
    InputItem,
    ParameterItem,
    OutputItem,
    EnvironmentItem,
    StepItem,
    VerificationItem,
    build_execution_create,
    build_components,
)

VERSION = APP_VERSION
SCHEMA = "sc-workbench-core-scenario-uncertainty-runtime/1.0"
RESULT_SCHEMA = "sc-workbench-scenario-uncertainty-result/1.0"
CONTEXT_SCHEMA = "sc-workbench-core-scenario-request-context/1.0"
CORE_REQUEST_SCHEMA = "sc-workbench-core-scenario-uncertainty-request/1.0"
BRIDGE_REF = "workbench:/integration/core/scenario-uncertainty"
CORE_SCENARIO_MANIFEST_SCHEMA = "scenario-compute-input-manifest-v1"
CORE_SCENARIO_RUNTIME = "platform-core:/v1/scenario-compute"
CORE_UNCERTAINTY_RUNTIME = "platform-core:/v1/uncertainty-compute"

CORE_PATHS = {
    "scenarioReadiness": "/v1/scenario-compute/readiness",
    "scenarioRequest": "/v1/scenario-compute/requests/{request_id}",
    "scenarioAttempts": "/v1/scenario-compute/requests/{request_id}/attempts",
    "scenarioBindRun": "/v1/scenario-compute/requests/{request_id}/bind-run",
    "scenarioResults": "/v1/scenario-compute/requests/{request_id}/results",
    "uncertaintyReadiness": "/v1/uncertainty-compute/readiness",
    "uncertaintySampling": "/v1/uncertainty-compute/sampling/design",
    "uncertaintySobol": "/v1/uncertainty-compute/sensitivity/sobol",
    "uncertaintyMorris": "/v1/uncertainty-compute/sensitivity/morris",
    "uncertaintyEnsembleStats": "/v1/uncertainty-compute/ensembles/statistics",
    "uncertaintyExceedance": "/v1/uncertainty-compute/probabilities/exceedance",
    "uncertaintyRuntimeHandoffs": "/v1/uncertainty-compute/runtime-handoffs",
}

SUPPORTED_SAMPLERS = {"monte-carlo", "latin-hypercube", "sobol-design", "morris-design"}
SUPPORTED_DISTRIBUTIONS = {"uniform", "interval", "triangular", "normal", "empirical"}

router = APIRouter(tags=["workbench-v680-scenario-uncertainty-runtime"])


def _bad(exc: Exception) -> HTTPException:
    return exc if isinstance(exc, HTTPException) else HTTPException(status_code=422, detail=str(exc))


def _bounded(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _refs(values: List[str]) -> List[str]:
    return sorted({_bounded(v, 1000) for v in values if _bounded(v, 1000)})


def _core_request(path: str, data: Dict[str, Any], phase: str) -> Dict[str, Any]:
    out = {
        "schema": CORE_REQUEST_SCHEMA,
        "version": VERSION,
        "method": "POST",
        "path": path,
        "phase": phase,
        "data": data,
        "payload": {"data": data},
        "automaticDispatchAuthorized": False,
        "callerMustPersistToCore": True,
    }
    out["requestHash"] = content_hash(out)
    return out


def scenario_uncertainty_manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "productRef": PRODUCT_REF,
        "runtime": RUNTIME_KIND,
        "bridgeRef": BRIDGE_REF,
        "runtimeContractRef": CORE_RUNTIME_CONTRACT,
        "coreUnifiedRuntimeContract": CORE_UNIFIED_RUNTIME_CONTRACT,
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "coreScenarioRuntime": CORE_SCENARIO_RUNTIME,
        "coreScenarioInputManifestSchema": CORE_SCENARIO_MANIFEST_SCHEMA,
        "coreUncertaintyRuntime": CORE_UNCERTAINTY_RUNTIME,
        "corePaths": dict(CORE_PATHS),
        "samplingMethods": sorted(SUPPORTED_SAMPLERS),
        "distributions": sorted(SUPPORTED_DISTRIBUTIONS),
        "capabilities": [
            "core-scenario-request-consumption",
            "deterministic-monte-carlo-design",
            "deterministic-latin-hypercube-design",
            "sobol-design-generation",
            "morris-design-generation",
            "sobol-output-analysis",
            "morris-elementary-effects-analysis",
            "ensemble-weight-normalization",
            "ensemble-descriptive-statistics",
            "empirical-exceedance-probability",
            "deterministic-affine-scenario-execution",
            "core-scenario-attempt-callback-planning",
            "v670-computation-lineage-handoff",
        ],
        "boundaries": {
            "workbenchExecutesScenarioNumerics": True,
            "workbenchExecutesUncertaintyNumerics": True,
            "coreOwnsScenarioDefinitions": True,
            "coreOwnsUncertaintySemantics": True,
            "coreNetworkDispatchPerformed": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "arbitraryCodeFromCoreAuthorized": False,
            "coreDeterminesTruth": False,
            "workbenchDeterminesTruth": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


class FactorSpec(BaseModel):
    key: str
    distribution: Literal["uniform", "interval", "triangular", "normal", "empirical"] = "uniform"
    lowerBound: float | None = None
    upperBound: float | None = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    empiricalValues: List[float] = Field(default_factory=list)
    unit: str = ""

    @field_validator("key")
    @classmethod
    def key_required(cls, value: str) -> str:
        value = _bounded(value, 180)
        if not value:
            raise ValueError("factor key is required")
        return value


class SamplingDesignRequest(BaseModel):
    method: Literal["monte-carlo", "latin-hypercube", "sobol-design", "morris-design"] = "monte-carlo"
    sampleCount: int = Field(default=1000, ge=1, le=100000)
    seed: int = 42
    levels: int = Field(default=6, ge=4, le=100)
    factors: List[FactorSpec]
    coreUncertaintyDefinitionIds: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class SobolAnalysisRequest(BaseModel):
    A: List[float]
    B: List[float]
    AB: Dict[str, List[float]]
    provenance: Dict[str, Any] = Field(default_factory=dict)


class MorrisAnalysisRequest(BaseModel):
    samples: List[Dict[str, float]]
    outputs: List[float]
    trajectories: List[Dict[str, Any]]
    provenance: Dict[str, Any] = Field(default_factory=dict)


class EnsembleStatisticsRequest(BaseModel):
    values: List[float]
    weights: List[float] | None = None
    quantiles: List[float] = Field(default_factory=lambda: [0.05, 0.5, 0.95])
    weightPolicy: Literal["explicit", "equal"] = "explicit"
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ExceedanceRequest(BaseModel):
    values: List[float]
    threshold: float
    operator: Literal[">", ">=", "<", "<="] = ">"
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ScenarioRequestConsumeRequest(BaseModel):
    coreRequest: Dict[str, Any]


class AffineOutputSpec(BaseModel):
    intercept: float = 0.0
    coefficients: Dict[str, float] = Field(default_factory=dict)


class ScenarioAffineExecuteRequest(BaseModel):
    coreRequestId: str
    inputManifest: Dict[str, Any]
    outputs: Dict[str, AffineOutputSpec]
    coreSessionId: str = ""
    coreExecutionId: str = ""
    workbenchExecutionRef: str = ""
    environmentRef: str = ""
    methodRef: str = "sc://workbench/method/scenario-affine-evaluator-v1"
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("coreRequestId")
    @classmethod
    def request_id_required(cls, value: str) -> str:
        value = _bounded(value, 128)
        if not value:
            raise ValueError("coreRequestId is required")
        return value


class ScenarioCallbackBuildRequest(BaseModel):
    coreRequestId: str
    attemptState: Literal["accepted", "running", "completed", "failed", "cancelled"] = "completed"
    externalExecutionId: str
    externalRequestId: str = ""
    runtimeMetadata: Dict[str, Any] = Field(default_factory=dict)
    error: Dict[str, Any] = Field(default_factory=dict)
    coreModelRunEntityId: str = ""
    resultBindings: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator("coreRequestId", "externalExecutionId")
    @classmethod
    def required_ids(cls, value: str) -> str:
        value = _bounded(value, 180)
        if not value:
            raise ValueError("Core request id and external execution id are required")
        return value


def _factor_dict(f: FactorSpec) -> Dict[str, Any]:
    return {
        "key": f.key,
        "distribution": f.distribution,
        "lower_bound": f.lowerBound,
        "upper_bound": f.upperBound,
        "parameters": dict(f.parameters),
        "empirical_values": list(f.empiricalValues),
        "unit": _bounded(f.unit, 128) or None,
    }


def _validate_factor(spec: Dict[str, Any]) -> Dict[str, Any]:
    kind = spec["distribution"]
    lo, hi = spec.get("lower_bound"), spec.get("upper_bound")
    if kind in {"uniform", "interval", "triangular"} and (lo is None or hi is None):
        raise ValueError(f"{spec['key']}: lowerBound and upperBound are required")
    if lo is not None and hi is not None and float(lo) > float(hi):
        raise ValueError(f"{spec['key']}: lowerBound cannot exceed upperBound")
    if kind == "normal" and float(spec.get("parameters", {}).get("stddev", spec.get("parameters", {}).get("sigma", 0))) <= 0:
        raise ValueError(f"{spec['key']}: normal stddev must be positive")
    if kind == "empirical" and not spec.get("empirical_values"):
        raise ValueError(f"{spec['key']}: empiricalValues are required")
    return spec


def _inv_sample(spec: Dict[str, Any], u: float) -> float:
    kind = spec["distribution"]
    lo, hi = spec.get("lower_bound"), spec.get("upper_bound")
    p = spec.get("parameters") or {}
    if kind in {"uniform", "interval"}:
        return float(lo) + (float(hi) - float(lo)) * u
    if kind == "triangular":
        lo_f, hi_f = float(lo), float(hi)
        if hi_f == lo_f:
            return lo_f
        mode = float(p.get("mode", (lo_f + hi_f) / 2))
        mode = min(hi_f, max(lo_f, mode))
        c = (mode - lo_f) / (hi_f - lo_f)
        if u < c:
            return lo_f + math.sqrt(u * (hi_f - lo_f) * (mode - lo_f))
        return hi_f - math.sqrt((1 - u) * (hi_f - lo_f) * (hi_f - mode))
    if kind == "normal":
        mu = float(p.get("mean", 0))
        sd = float(p.get("stddev", p.get("sigma", 1)))
        return statistics.NormalDist(mu=mu, sigma=sd).inv_cdf(min(max(u, 1e-12), 1 - 1e-12))
    vals = sorted(float(x) for x in spec["empirical_values"])
    return vals[min(int(u * len(vals)), len(vals) - 1)]


def run_sampling_design(request: SamplingDesignRequest) -> Dict[str, Any]:
    specs = [_validate_factor(_factor_dict(x)) for x in request.factors]
    if not specs:
        raise ValueError("At least one factor is required")
    rng = random.Random(request.seed)
    n = request.sampleCount
    method = request.method
    if method == "monte-carlo":
        samples = [{s["key"]: _inv_sample(s, rng.random()) for s in specs} for _ in range(n)]
        data: Dict[str, Any] = {"samples": samples, "total_evaluations": n}
    elif method == "latin-hypercube":
        cols: Dict[str, List[float]] = {}
        for s in specs:
            us = [(i + rng.random()) / n for i in range(n)]
            rng.shuffle(us)
            cols[s["key"]] = [_inv_sample(s, u) for u in us]
        samples = [{s["key"]: cols[s["key"]][i] for s in specs} for i in range(n)]
        data = {"samples": samples, "total_evaluations": n}
    elif method == "sobol-design":
        a_req = request.model_copy(update={"method": "latin-hypercube"})
        A = run_sampling_design(a_req)["samples"]
        b_req = request.model_copy(update={"method": "latin-hypercube", "seed": request.seed + 104729})
        B = run_sampling_design(b_req)["samples"]
        AB = {s["key"]: [{**A[i], s["key"]: B[i][s["key"]]} for i in range(n)] for s in specs}
        data = {"A": A, "B": B, "AB": AB, "base_sample_count": n, "total_evaluations": n * (2 + len(specs))}
    else:
        delta = request.levels / (2 * (request.levels - 1))
        rows: List[Dict[str, float]] = []
        trajectory_meta: List[Dict[str, Any]] = []
        for t in range(n):
            u = {s["key"]: rng.randint(0, max(0, request.levels - 2)) / (request.levels - 1) for s in specs}
            order = [s["key"] for s in specs]
            rng.shuffle(order)
            start = len(rows)
            rows.append({s["key"]: _inv_sample(s, u[s["key"]]) for s in specs})
            for key in order:
                u[key] = min(1.0, u[key] + delta) if u[key] + delta <= 1 else max(0.0, u[key] - delta)
                rows.append({s["key"]: _inv_sample(s, u[s["key"]]) for s in specs})
            trajectory_meta.append({"trajectory": t, "start_index": start, "order": order})
        data = {"samples": rows, "trajectories": trajectory_meta, "levels": request.levels, "delta": delta, "total_evaluations": len(rows)}
    manifest = {
        "ok": True,
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "operation": "sampling-design",
        "method": method,
        "seed": request.seed,
        "sample_count": n,
        "factor_keys": [s["key"] for s in specs],
        "core_uncertainty_definition_ids": _refs(request.coreUncertaintyDefinitionIds),
        **data,
        "provenance": {"computedBy": PRODUCT_REF, "bridgeRef": BRIDGE_REF, **request.provenance},
        "calculated_by_workbench": True,
        "calculated_by_core": False,
        "model_execution_by_core": False,
    }
    manifest["manifest_sha256"] = content_hash(manifest)
    return manifest


def run_sobol_analysis(request: SobolAnalysisRequest) -> Dict[str, Any]:
    ya = [float(x) for x in request.A]
    yb = [float(x) for x in request.B]
    if not ya or len(ya) != len(yb):
        raise ValueError("A and B output vectors must be non-empty and equal length")
    n = len(ya)
    var = statistics.pvariance(ya + yb)
    if var <= 0:
        raise ValueError("Output variance must be positive for Sobol analysis")
    rows = []
    for key, vals in request.AB.items():
        y = [float(x) for x in vals]
        if len(y) != n:
            raise ValueError(f"AB output vector for {key} has wrong length")
        s1 = sum(yb[i] * (y[i] - ya[i]) for i in range(n)) / n / var
        st = sum((ya[i] - y[i]) ** 2 for i in range(n)) / (2 * n * var)
        rows.append({"factor_key": key, "sobol_first": s1, "sobol_total": st})
    rows.sort(key=lambda x: abs(x["sobol_total"]), reverse=True)
    for i, row in enumerate(rows, 1):
        row["rank_position"] = i
    out = {"ok": True, "schema": RESULT_SCHEMA, "version": VERSION, "operation": "sobol-analysis", "method": "sobol", "sample_count": n, "output_variance": var, "factors": rows, "provenance": request.provenance, "calculated_by_workbench": True, "calculated_by_core": False, "model_execution_by_core": False}
    out["resultHash"] = content_hash(out)
    return out


def run_morris_analysis(request: MorrisAnalysisRequest) -> Dict[str, Any]:
    samples = list(request.samples)
    outputs = [float(x) for x in request.outputs]
    if len(samples) != len(outputs):
        raise ValueError("samples and outputs must have equal length")
    effects: Dict[str, List[float]] = {}
    for tr in request.trajectories:
        start = int(tr["start_index"])
        order = list(tr["order"])
        for j, key in enumerate(order):
            if start + j + 1 >= len(samples):
                raise ValueError("trajectory references samples outside the supplied design")
            a, b = samples[start + j], samples[start + j + 1]
            dx = float(b[key]) - float(a[key])
            if dx == 0:
                continue
            effects.setdefault(key, []).append((outputs[start + j + 1] - outputs[start + j]) / dx)
    rows = []
    for key, vals in effects.items():
        rows.append({"factor_key": key, "mu": statistics.fmean(vals), "mu_star": statistics.fmean(abs(v) for v in vals), "sigma": statistics.pstdev(vals) if len(vals) > 1 else 0.0, "effects": len(vals)})
    rows.sort(key=lambda x: x["mu_star"], reverse=True)
    for i, row in enumerate(rows, 1):
        row["rank_position"] = i
    out = {"ok": True, "schema": RESULT_SCHEMA, "version": VERSION, "operation": "morris-analysis", "method": "morris", "factors": rows, "provenance": request.provenance, "calculated_by_workbench": True, "calculated_by_core": False, "model_execution_by_core": False}
    out["resultHash"] = content_hash(out)
    return out


def _normalize_weights(weights: List[float], policy: str) -> Dict[str, Any]:
    vals = [float(x) for x in weights]
    if not vals:
        raise ValueError("weights are required")
    if any(x < 0 for x in vals):
        raise ValueError("weights cannot be negative")
    if policy == "equal":
        vals = [1.0] * len(vals)
    total = sum(vals)
    if total <= 0:
        raise ValueError("weight total must be positive")
    norm = [x / total for x in vals]
    return {"policy": policy, "raw_weights": weights, "normalized_weights": norm, "raw_sum": total, "normalized_sum": sum(norm)}


def _weighted_quantile(values: List[float], weights: List[float], q: float) -> float:
    pairs = sorted(zip(values, weights), key=lambda x: x[0])
    target = q * sum(weights)
    cumulative = 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative >= target:
            return value
    return pairs[-1][0]


def run_ensemble_statistics(request: EnsembleStatisticsRequest) -> Dict[str, Any]:
    vals = [float(x) for x in request.values]
    if not vals:
        raise ValueError("values are required")
    weights = request.weights if request.weights is not None else [1.0] * len(vals)
    if len(weights) != len(vals):
        raise ValueError("weights length must match values")
    norm = _normalize_weights(list(weights), request.weightPolicy)
    nw = norm["normalized_weights"]
    qs = [float(q) for q in request.quantiles]
    if any(q < 0 or q > 1 for q in qs):
        raise ValueError("quantiles must be between 0 and 1")
    mean = sum(v * w for v, w in zip(vals, nw))
    var = sum(w * (v - mean) ** 2 for v, w in zip(vals, nw))
    out = {"ok": True, "schema": RESULT_SCHEMA, "version": VERSION, "operation": "ensemble-statistics", "count": len(vals), "mean": mean, "variance": var, "stddev": math.sqrt(var), "min": min(vals), "max": max(vals), "quantiles": {str(q): _weighted_quantile(vals, nw, q) for q in qs}, "normalized_weights": nw, "weightPolicy": request.weightPolicy, "provenance": request.provenance, "aggregation_performed_by_workbench": True, "aggregation_performed_by_core": False}
    out["resultHash"] = content_hash(out)
    return out


def run_exceedance(request: ExceedanceRequest) -> Dict[str, Any]:
    vals = [float(x) for x in request.values]
    if not vals:
        raise ValueError("values are required")
    t = float(request.threshold)
    ops = {">": lambda x: x > t, ">=": lambda x: x >= t, "<": lambda x: x < t, "<=": lambda x: x <= t}
    k = sum(1 for x in vals if ops[request.operator](x))
    n = len(vals)
    p = k / n
    z = 1.959963984540054
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    out = {"ok": True, "schema": RESULT_SCHEMA, "version": VERSION, "operation": "exceedance-probability", "threshold": t, "operator": request.operator, "sample_count": n, "exceedances": k, "probability": p, "confidence_interval_95": [max(0, center - half), min(1, center + half)], "estimator": "empirical-binomial", "provenance": request.provenance, "probability_estimation_performed_by_workbench": True, "probability_estimation_performed_by_core": False}
    out["resultHash"] = content_hash(out)
    return out


def consume_scenario_request(request: ScenarioRequestConsumeRequest) -> Dict[str, Any]:
    record = request.coreRequest or {}
    manifest = record.get("input_manifest_json") if isinstance(record.get("input_manifest_json"), dict) else record.get("input_manifest")
    if not isinstance(manifest, dict):
        manifest = record if record.get("schema") == CORE_SCENARIO_MANIFEST_SCHEMA else {}
    if manifest.get("schema") != CORE_SCENARIO_MANIFEST_SCHEMA:
        return {"ok": False, "schema": CONTEXT_SCHEMA, "version": VERSION, "error": f"Core scenario request must contain {CORE_SCENARIO_MANIFEST_SCHEMA}", "readOnlyContext": True}
    requested_product = _bounded(record.get("requested_product") or manifest.get("execution_product"), 64)
    if requested_product and requested_product != "workbench":
        return {"ok": False, "schema": CONTEXT_SCHEMA, "version": VERSION, "error": "Scenario request is not assigned to Workbench", "requestedProduct": requested_product, "readOnlyContext": True}
    context = {
        "coreRequestId": _bounded(record.get("id"), 128) or None,
        "requestHash": _bounded(record.get("request_hash"), 256) or content_hash(manifest),
        "projectEntityId": manifest.get("project_entity_id"),
        "modelEntityId": manifest.get("model_entity_id"),
        "modelVersionEntityId": manifest.get("model_version_entity_id"),
        "scenarioEntityId": manifest.get("scenario_entity_id"),
        "parameterValues": dict(manifest.get("parameter_values") or {}),
        "expectedOutputs": list(manifest.get("expected_outputs") or []),
        "executionContract": dict(manifest.get("execution_contract") or {}),
        "outputContract": dict(manifest.get("output_contract") or {}),
        "caseHash": manifest.get("case_hash"),
        "coreExecution": bool(manifest.get("core_execution", False)),
        "requestedProduct": requested_product or "workbench",
        "readOnlyContext": True,
        "automaticWorkbenchExecutionAuthorized": False,
        "arbitraryCodeFromCoreAuthorized": False,
    }
    context["contextHash"] = content_hash(context)
    return {"ok": True, "schema": CONTEXT_SCHEMA, "version": VERSION, "context": context}


def _affine_outputs(params: Dict[str, Any], outputs: Dict[str, AffineOutputSpec]) -> Dict[str, float]:
    result: Dict[str, float] = {}
    numeric: Dict[str, float] = {}
    for key, value in params.items():
        if isinstance(value, bool):
            continue
        try:
            numeric[key] = float(value)
        except (TypeError, ValueError):
            continue
    for output_key, spec in outputs.items():
        value = float(spec.intercept)
        for key, coef in spec.coefficients.items():
            if key not in numeric:
                raise ValueError(f"scenario parameter '{key}' required by output '{output_key}' is missing or non-numeric")
            value += float(coef) * numeric[key]
        result[output_key] = value
    return result


def execute_affine_scenario(request: ScenarioAffineExecuteRequest) -> Dict[str, Any]:
    manifest = request.inputManifest or {}
    if manifest.get("schema") != CORE_SCENARIO_MANIFEST_SCHEMA:
        raise ValueError(f"inputManifest.schema must be {CORE_SCENARIO_MANIFEST_SCHEMA}")
    if _bounded(manifest.get("execution_product"), 64) not in {"", "workbench"}:
        raise ValueError("inputManifest is not assigned to Workbench")
    params = dict(manifest.get("parameter_values") or {})
    results = _affine_outputs(params, request.outputs)
    execution_ref = _bounded(request.workbenchExecutionRef, 1000) or f"sc://workbench/scenario-execution/{request.coreRequestId}"
    result_items = [
        {"output_key": key, "value": value, "content_hash": content_hash({"output_key": key, "value": value, "case_hash": manifest.get("case_hash")})}
        for key, value in sorted(results.items())
    ]
    execution_draft = build_execution_create(ExecutionCreateRequest(
        executionKey=f"scenario-{request.coreRequestId}",
        title=f"Scenario compute request {request.coreRequestId}",
        executionType="simulation",
        projectRef=_bounded(manifest.get("project_entity_id"), 1000),
        coreSessionId=_bounded(request.coreSessionId, 128),
        workbenchExecutionRef=execution_ref,
        methodPlanRef=_bounded(request.methodRef, 1000),
        provenance={"coreScenarioRequestId": request.coreRequestId, "coreScenarioManifestHash": content_hash(manifest), **request.provenance},
        metadata={"scenarioEntityId": manifest.get("scenario_entity_id"), "modelEntityId": manifest.get("model_entity_id"), "modelVersionEntityId": manifest.get("model_version_entity_id"), "caseHash": manifest.get("case_hash"), "evaluator": "deterministic-affine-v1"},
    ))
    lineage = None
    if _bounded(request.coreExecutionId, 128):
        lineage = build_components(ExecutionComponentsRequest(
            coreExecutionId=_bounded(request.coreExecutionId, 128),
            coreSessionId=_bounded(request.coreSessionId, 128),
            projectRef=_bounded(manifest.get("project_entity_id"), 1000),
            workbenchExecutionRef=execution_ref,
            environmentRef=_bounded(request.environmentRef, 1000),
            methodRef=_bounded(request.methodRef, 1000),
            inputs=[InputItem(inputKey="scenario-manifest", inputType="research_object", objectRef=f"sc://platform-core/scenario-compute/request/{request.coreRequestId}", contentHash=content_hash(manifest), role="scenario-input")],
            parameters=[ParameterItem(parameterKey=str(k), value={"value": v}, sourceRef=f"sc://platform-core/scenario/{manifest.get('scenario_entity_id')}", sensitivityRole="scenario-parameter") for k, v in sorted(params.items())],
            environments=[EnvironmentItem(environmentKey="workbench-v680", runtimeVersion=VERSION, environmentHash=content_hash({"runtime": "workbench", "version": VERSION}))],
            steps=[StepItem(stepKey="evaluate-affine", sequence=1, stepType="scenario-evaluation", toolRef="workbench:v680", operationText="Evaluate declared affine output specifications against Core scenario parameter values.")],
            outputs=[OutputItem(outputKey=x["output_key"], outputType="statistic", objectRef=f"sc://workbench/scenario-result/{request.coreRequestId}/{x['output_key']}", contentHash=x["content_hash"], metadata={"value": x["value"]}) for x in result_items],
            verifications=[VerificationItem(verificationKey="deterministic-result-hash", verificationType="checksum", status="passed", evidence={"resultHash": content_hash(result_items), "manifestHash": content_hash(manifest)})],
        ))
    out = {
        "ok": True,
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "operation": "scenario-affine-execution",
        "coreRequestId": request.coreRequestId,
        "coreScenarioInputManifestSchema": CORE_SCENARIO_MANIFEST_SCHEMA,
        "workbenchExecutionRef": execution_ref,
        "parameterValues": params,
        "outputs": result_items,
        "executionRegistrationPlan": execution_draft,
        "lineageComponentsPlan": lineage,
        "numerical_computation_performed_by_workbench": True,
        "numerical_computation_performed_by_core": False,
        "arbitrary_code_execution_performed": False,
        "automaticCorePersistenceAuthorized": False,
    }
    out["resultHash"] = content_hash(out)
    return out


def build_scenario_callbacks(request: ScenarioCallbackBuildRequest) -> Dict[str, Any]:
    rid = _bounded(request.coreRequestId, 128)
    attempt = {
        "attempt_state": request.attemptState,
        "executor_product": "workbench",
        "external_execution_id": _bounded(request.externalExecutionId, 1000),
        "external_request_id": _bounded(request.externalRequestId, 1000) or None,
        "runtime_metadata": {"workbenchVersion": VERSION, "bridgeRef": BRIDGE_REF, **request.runtimeMetadata},
        "error": dict(request.error),
        "executed_by_core": False,
    }
    core_requests = [_core_request(CORE_PATHS["scenarioAttempts"].format(request_id=rid), attempt, "scenario-attempt")]
    if _bounded(request.coreModelRunEntityId, 128):
        core_requests.append(_core_request(CORE_PATHS["scenarioBindRun"].format(request_id=rid), {"model_run_entity_id": _bounded(request.coreModelRunEntityId, 128)}, "scenario-model-run-binding"))
    for binding in request.resultBindings:
        if not _bounded(binding.get("result_entity_id"), 128):
            raise ValueError("each result binding requires a Core result_entity_id")
        data = {
            "result_entity_id": _bounded(binding.get("result_entity_id"), 128),
            "output_key": _bounded(binding.get("output_key"), 180) or _bounded(binding.get("result_entity_id"), 128),
            "binding_role": _bounded(binding.get("binding_role"), 64) or "primary",
            "metadata": dict(binding.get("metadata") or {}),
        }
        core_requests.append(_core_request(CORE_PATHS["scenarioResults"].format(request_id=rid), data, "scenario-result-binding"))
    out = {"ok": True, "schema": SCHEMA, "version": VERSION, "coreRequestId": rid, "coreRequests": core_requests, "requestCount": len(core_requests), "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False}
    out["planHash"] = content_hash(out)
    return out


@router.get("/integration/core/scenario-uncertainty/manifest")
def manifest(x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    return scenario_uncertainty_manifest()


@router.post("/integration/core/scenario-uncertainty/scenario/request/consume")
def scenario_request_consume(request: ScenarioRequestConsumeRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return consume_scenario_request(request)
    except Exception as exc:
        raise _bad(exc)


@router.post("/integration/core/scenario-uncertainty/scenario/affine/run")
def scenario_affine_run(request: ScenarioAffineExecuteRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return execute_affine_scenario(request)
    except Exception as exc:
        raise _bad(exc)


@router.post("/integration/core/scenario-uncertainty/scenario/callbacks/build")
def scenario_callbacks_build(request: ScenarioCallbackBuildRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return build_scenario_callbacks(request)
    except Exception as exc:
        raise _bad(exc)


@router.post("/integration/core/scenario-uncertainty/sampling/design/run")
def sampling_design_run(request: SamplingDesignRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return run_sampling_design(request)
    except Exception as exc:
        raise _bad(exc)


@router.post("/integration/core/scenario-uncertainty/sensitivity/sobol/run")
def sobol_run(request: SobolAnalysisRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return run_sobol_analysis(request)
    except Exception as exc:
        raise _bad(exc)


@router.post("/integration/core/scenario-uncertainty/sensitivity/morris/run")
def morris_run(request: MorrisAnalysisRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return run_morris_analysis(request)
    except Exception as exc:
        raise _bad(exc)


@router.post("/integration/core/scenario-uncertainty/ensembles/statistics/run")
def ensemble_run(request: EnsembleStatisticsRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return run_ensemble_statistics(request)
    except Exception as exc:
        raise _bad(exc)


@router.post("/integration/core/scenario-uncertainty/probabilities/exceedance/run")
def exceedance_run(request: ExceedanceRequest, x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str, Any]:
    _authorize_core_route(x_sc_service_token)
    try:
        return run_exceedance(request)
    except Exception as exc:
        raise _bad(exc)


@router.get("/v680/status")
def v680_status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Scenario & Uncertainty Compute Runtime Integration",
        "coreScenarioRuntime": CORE_SCENARIO_RUNTIME,
        "coreUncertaintyRuntime": CORE_UNCERTAINTY_RUNTIME,
        "scenarioManifestSchema": CORE_SCENARIO_MANIFEST_SCHEMA,
        "workbenchNumericalExecution": True,
        "deterministicSampling": True,
        "monteCarlo": True,
        "latinHypercube": True,
        "sobol": True,
        "morris": True,
        "ensembleStatistics": True,
        "empiricalProbability": True,
        "v670LineageIntegration": True,
        "automaticCoreDispatch": False,
        "automaticCorePersistence": False,
        "arbitraryCoreCodeExecution": False,
    }

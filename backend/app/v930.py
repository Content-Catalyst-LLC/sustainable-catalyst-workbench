"""Workbench v9.3.0 — Statistical Analysis & Diagnostic Workspace.

Explicit, provenance-preserving statistical analysis over completed Workbench jobs
and v9.2 computational campaigns. Researchers choose the response metric, optional
group/predictor parameter, requested methods, reference values, and confidence
level. The workspace computes transparent statistics and diagnostics, persists
content-addressed analysis records, and prepares Platform Core bindings.

It does not auto-select a statistical method, declare significance, accept/reject
hypotheses, infer causality, validate a scientific model, or dispatch to Core.
"""
from __future__ import annotations

import hashlib
import math
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from scipy import stats

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import load_project
from .v840 import _load_job, list_jobs
from .v920 import _load_state, list_campaigns, load_campaign

VERSION = APP_VERSION
SCHEMA = "sc-workbench-statistical-analysis-diagnostic-workspace/1.0"
ANALYSIS_SCHEMA = "sc-workbench-statistical-analysis/1.0"
CATALOG_SCHEMA = "sc-workbench-statistical-analysis-source-catalog/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-statistical-analysis-core-plan/1.0"
router = APIRouter(tags=["workbench-v930-statistical-analysis-diagnostic-workspace"])

MAX_OBSERVATIONS = 5000
MAX_JOBS = 5000
MAX_METHODS = 16
Method = Literal[
    "descriptive",
    "distribution-diagnostics",
    "normality-shapiro",
    "variance-diagnostic-levene",
    "one-sample-t",
    "independent-t",
    "one-way-anova",
    "kruskal-wallis",
    "pearson-correlation",
    "spearman-correlation",
    "linear-regression",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _analysis_dir(project_key: str) -> Path:
    return _store_root() / "statistical-analyses" / _stable_id(project_key)


def _analysis_path(project_key: str, analysis_hash: str) -> Path:
    return _analysis_dir(project_key) / f"{analysis_hash}.json"


def _finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _clean_float(value: Any) -> float | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _nested_get(value: Any, path: str) -> Any:
    cur = value
    for token in path.split("."):
        if isinstance(cur, dict) and token in cur:
            cur = cur[token]
        else:
            raise KeyError(path)
    return cur


def _parameter_value(job: Dict[str, Any], path: str) -> Any:
    params = ((job.get("metadata") or {}).get("parameterValues") or {})
    if path in params:
        return params[path]
    try:
        return _nested_get(params, path)
    except KeyError:
        return None


class StatisticalAnalysisRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    analysisKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    campaignHash: str = Field(default="", max_length=64)
    jobIds: List[str] = Field(default_factory=list, max_length=MAX_JOBS)
    resultMetricPath: str = Field(min_length=1, max_length=300)
    groupParameterPath: str = Field(default="", max_length=300)
    predictorParameterPath: str = Field(default="", max_length=300)
    methods: List[Method] = Field(default_factory=lambda: ["descriptive"], min_length=1, max_length=MAX_METHODS)
    referenceValue: float | None = None
    confidenceLevel: float = Field(default=0.95, gt=0.5, lt=1.0)
    researcherInterpretation: str = Field(default="", max_length=12000)
    notes: str = Field(default="", max_length=12000)

    @model_validator(mode="after")
    def validate_analysis(self):
        self.projectKey = self.projectKey.strip()
        self.analysisKey = self.analysisKey.strip()
        self.title = self.title.strip()
        self.resultMetricPath = self.resultMetricPath.strip()
        self.groupParameterPath = self.groupParameterPath.strip()
        self.predictorParameterPath = self.predictorParameterPath.strip()
        if not self.campaignHash and not self.jobIds:
            raise ValueError("campaignHash or jobIds is required")
        if self.campaignHash and len(self.campaignHash) != 64:
            raise ValueError("campaignHash must be a 64-character content hash")
        ids = [str(x).strip() for x in self.jobIds if str(x).strip()]
        if len(ids) != len(set(ids)):
            raise ValueError("jobIds must be unique")
        self.jobIds = ids
        self.methods = list(dict.fromkeys(self.methods))
        group_methods = {"variance-diagnostic-levene", "independent-t", "one-way-anova", "kruskal-wallis"}
        predictor_methods = {"pearson-correlation", "spearman-correlation", "linear-regression"}
        if group_methods.intersection(self.methods) and not self.groupParameterPath:
            raise ValueError("groupParameterPath is required for requested group analysis methods")
        if predictor_methods.intersection(self.methods) and not self.predictorParameterPath:
            raise ValueError("predictorParameterPath is required for requested predictor analysis methods")
        if "one-sample-t" in self.methods and self.referenceValue is None:
            raise ValueError("referenceValue is required for one-sample-t")
        return self


class SaveStatisticalAnalysisRequest(StatisticalAnalysisRequest):
    createdBy: str = Field(default="workbench", max_length=160)
    recordLabel: str = Field(default="Statistical analysis", max_length=500)


class CoreStatisticalPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    analysisHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Statistical Analysis & Diagnostic Workspace",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "methods": [
            "descriptive", "distribution-diagnostics", "normality-shapiro",
            "variance-diagnostic-levene", "one-sample-t", "independent-t",
            "one-way-anova", "kruskal-wallis", "pearson-correlation",
            "spearman-correlation", "linear-regression",
        ],
        "capabilities": {
            "campaignAndCompletedJobSources": True,
            "explicitMetricExtraction": True,
            "descriptiveStatistics": True,
            "confidenceIntervals": True,
            "distributionDiagnostics": True,
            "normalityDiagnostics": True,
            "varianceDiagnostics": True,
            "explicitHypothesisTestStatistics": True,
            "correlationAnalysis": True,
            "linearRegressionDiagnostics": True,
            "contentAddressedAnalysisRecords": True,
            "provenancePreservation": True,
            "platformCoreStatisticalAnalysisPlanning": True,
        },
        "boundaries": {
            "automaticMethodSelection": False,
            "automaticSignificanceDecision": False,
            "automaticHypothesisAcceptanceOrRejection": False,
            "automaticCausalInference": False,
            "automaticScientificValidityInference": False,
            "automaticPreferredModelSelection": False,
            "automaticResearchInterpretation": False,
            "automaticCoreDispatch": False,
            "platformCoreGovernanceReplaced": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _source_jobs(req: StatisticalAnalysisRequest) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    load_project(req.projectKey)
    selected: Dict[str, Dict[str, Any]] = {}
    source: Dict[str, Any] = {"campaignHash": None, "campaignStateHash": None, "requestedJobIds": list(req.jobIds)}
    if req.campaignHash:
        campaign = load_campaign(req.projectKey, req.campaignHash)
        state = _load_state(req.projectKey, req.campaignHash)
        source.update({
            "campaignHash": req.campaignHash,
            "campaignRef": campaign.get("campaignRef"),
            "protocolHash": campaign.get("protocolHash"),
            "studyHash": campaign.get("studyHash"),
            "campaignStateHash": state.get("stateHash"),
        })
        for row in (state.get("jobs") or {}).values():
            jid = str(row.get("jobId") or "")
            if jid:
                try:
                    job = _load_job(jid)
                except Exception:
                    continue
                if job.get("status") == "completed" and job.get("projectKey") == req.projectKey:
                    selected[jid] = job
    for jid in req.jobIds:
        try:
            job = _load_job(jid)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"execution job not found: {jid}") from exc
        if job.get("projectKey") != req.projectKey:
            raise ValueError(f"job {jid} belongs to another project")
        if job.get("status") != "completed":
            raise ValueError(f"job {jid} is not completed")
        selected[jid] = job
    jobs = [selected[k] for k in sorted(selected)]
    if not jobs:
        raise ValueError("no completed execution jobs are available for this analysis")
    if len(jobs) > MAX_OBSERVATIONS:
        raise ValueError(f"analysis exceeds hard observation limit of {MAX_OBSERVATIONS}")
    return jobs, source


def _extract_rows(req: StatisticalAnalysisRequest, jobs: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []
    for job in jobs:
        jid = str(job.get("jobId") or "")
        try:
            raw = _nested_get(job.get("result") or {}, req.resultMetricPath)
        except KeyError:
            excluded.append({"jobId": jid, "reason": "result metric path missing"})
            continue
        value = _finite_float(raw)
        if value is None:
            excluded.append({"jobId": jid, "reason": "result metric is not a finite number"})
            continue
        group = _parameter_value(job, req.groupParameterPath) if req.groupParameterPath else None
        predictor_raw = _parameter_value(job, req.predictorParameterPath) if req.predictorParameterPath else None
        predictor = _finite_float(predictor_raw) if req.predictorParameterPath else None
        if req.predictorParameterPath and predictor is None:
            excluded.append({"jobId": jid, "reason": "predictor parameter is missing or not numeric"})
            continue
        rows.append({
            "jobId": jid,
            "value": value,
            "group": group,
            "predictor": predictor,
            "requestHash": job.get("requestHash"),
            "resultHash": job.get("resultHash"),
            "jobHash": job.get("jobHash"),
            "parameterValues": deepcopy(((job.get("metadata") or {}).get("parameterValues") or {})),
        })
    if not rows:
        raise ValueError("no finite observations could be extracted from the requested result metric")
    return rows, excluded


def _descriptive(values: np.ndarray, confidence: float) -> Dict[str, Any]:
    n = int(values.size)
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if n > 1 else None
    sem = float(stats.sem(values)) if n > 1 else None
    ci = [None, None]
    if n > 1 and sem is not None and math.isfinite(sem):
        crit = float(stats.t.ppf((1 + confidence) / 2.0, df=n - 1))
        ci = [_clean_float(mean - crit * sem), _clean_float(mean + crit * sem)]
    q = np.quantile(values, [0.0, 0.25, 0.5, 0.75, 1.0])
    return {
        "n": n, "mean": _clean_float(mean), "median": _clean_float(np.median(values)),
        "standardDeviation": _clean_float(std), "standardError": _clean_float(sem),
        "variance": _clean_float(np.var(values, ddof=1)) if n > 1 else None,
        "minimum": _clean_float(q[0]), "q1": _clean_float(q[1]), "q2": _clean_float(q[2]),
        "q3": _clean_float(q[3]), "maximum": _clean_float(q[4]),
        "interquartileRange": _clean_float(q[3] - q[1]),
        "confidenceLevel": confidence, "meanConfidenceInterval": ci,
    }


def _distribution(values: np.ndarray) -> Dict[str, Any]:
    med = float(np.median(values)); mad = float(np.median(np.abs(values - med)))
    return {
        "n": int(values.size),
        "skewness": _clean_float(stats.skew(values, bias=False)) if values.size >= 3 else None,
        "excessKurtosis": _clean_float(stats.kurtosis(values, fisher=True, bias=False)) if values.size >= 4 else None,
        "medianAbsoluteDeviation": _clean_float(mad),
        "range": _clean_float(np.max(values) - np.min(values)),
        "diagnosticDecisionGenerated": False,
    }


def _shapiro(values: np.ndarray) -> Dict[str, Any]:
    if values.size < 3:
        raise ValueError("normality-shapiro requires at least 3 observations")
    if values.size > 5000:
        raise ValueError("normality-shapiro is limited to at most 5000 observations")
    r = stats.shapiro(values)
    return {"n": int(values.size), "statistic": _clean_float(r.statistic), "pValue": _clean_float(r.pvalue), "normalityDecisionGenerated": False}


def _groups(rows: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
    grouped: Dict[str, List[float]] = {}
    for row in rows:
        key = str(row.get("group"))
        grouped.setdefault(key, []).append(float(row["value"]))
    return {k: np.asarray(v, dtype=float) for k, v in sorted(grouped.items())}


def _group_summaries(groups: Dict[str, np.ndarray], confidence: float) -> Dict[str, Any]:
    return {key: _descriptive(vals, confidence) for key, vals in groups.items()}


def _compute_methods(req: StatisticalAnalysisRequest, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    values = np.asarray([r["value"] for r in rows], dtype=float)
    results: Dict[str, Any] = {}
    groups = _groups(rows) if req.groupParameterPath else {}
    predictor = np.asarray([r["predictor"] for r in rows], dtype=float) if req.predictorParameterPath else np.asarray([], dtype=float)

    for method in req.methods:
        if method == "descriptive":
            results[method] = _descriptive(values, req.confidenceLevel)
        elif method == "distribution-diagnostics":
            results[method] = _distribution(values)
        elif method == "normality-shapiro":
            results[method] = _shapiro(values)
        elif method == "variance-diagnostic-levene":
            usable = [v for v in groups.values() if v.size >= 2]
            if len(usable) < 2:
                raise ValueError("variance-diagnostic-levene requires at least two groups with 2+ observations each")
            r = stats.levene(*usable, center="median")
            results[method] = {"groupCount": len(usable), "statistic": _clean_float(r.statistic), "pValue": _clean_float(r.pvalue), "varianceDecisionGenerated": False, "groupSummaries": _group_summaries(groups, req.confidenceLevel)}
        elif method == "one-sample-t":
            if values.size < 2:
                raise ValueError("one-sample-t requires at least 2 observations")
            r = stats.ttest_1samp(values, popmean=float(req.referenceValue))
            std = float(np.std(values, ddof=1))
            effect = None if std == 0 else float((np.mean(values) - float(req.referenceValue)) / std)
            results[method] = {"n": int(values.size), "referenceValue": req.referenceValue, "statistic": _clean_float(r.statistic), "pValue": _clean_float(r.pvalue), "cohensD": _clean_float(effect), "significanceDecisionGenerated": False, "hypothesisDecisionGenerated": False}
        elif method == "independent-t":
            if len(groups) != 2:
                raise ValueError("independent-t requires exactly two groups")
            keys = list(groups); a, b = groups[keys[0]], groups[keys[1]]
            if min(a.size, b.size) < 2:
                raise ValueError("independent-t requires 2+ observations in each group")
            r = stats.ttest_ind(a, b, equal_var=False)
            pooled = math.sqrt(((a.size - 1) * np.var(a, ddof=1) + (b.size - 1) * np.var(b, ddof=1)) / max(1, a.size + b.size - 2))
            effect = None if pooled == 0 else float((np.mean(a) - np.mean(b)) / pooled)
            results[method] = {"groups": keys, "statistic": _clean_float(r.statistic), "pValue": _clean_float(r.pvalue), "cohensD": _clean_float(effect), "equalVarianceAssumed": False, "significanceDecisionGenerated": False, "groupSummaries": _group_summaries(groups, req.confidenceLevel)}
        elif method == "one-way-anova":
            usable = [v for v in groups.values() if v.size >= 2]
            if len(usable) < 2:
                raise ValueError("one-way-anova requires at least two groups with 2+ observations each")
            r = stats.f_oneway(*usable)
            grand = float(np.mean(np.concatenate(usable)))
            ss_between = sum(float(v.size) * (float(np.mean(v)) - grand) ** 2 for v in usable)
            allv = np.concatenate(usable); ss_total = float(np.sum((allv - grand) ** 2))
            eta = None if ss_total == 0 else ss_between / ss_total
            results[method] = {"groupCount": len(usable), "statistic": _clean_float(r.statistic), "pValue": _clean_float(r.pvalue), "etaSquared": _clean_float(eta), "significanceDecisionGenerated": False, "groupSummaries": _group_summaries(groups, req.confidenceLevel)}
        elif method == "kruskal-wallis":
            usable = [v for v in groups.values() if v.size >= 1]
            if len(usable) < 2:
                raise ValueError("kruskal-wallis requires at least two non-empty groups")
            r = stats.kruskal(*usable)
            results[method] = {"groupCount": len(usable), "statistic": _clean_float(r.statistic), "pValue": _clean_float(r.pvalue), "significanceDecisionGenerated": False, "groupSummaries": _group_summaries(groups, req.confidenceLevel)}
        elif method == "pearson-correlation":
            if values.size < 2 or np.std(predictor) == 0 or np.std(values) == 0:
                raise ValueError("pearson-correlation requires 2+ observations and non-constant predictor/response")
            r = stats.pearsonr(predictor, values)
            results[method] = {"n": int(values.size), "coefficient": _clean_float(r.statistic), "pValue": _clean_float(r.pvalue), "significanceDecisionGenerated": False, "causalInterpretationGenerated": False}
        elif method == "spearman-correlation":
            if values.size < 2:
                raise ValueError("spearman-correlation requires at least 2 observations")
            r = stats.spearmanr(predictor, values)
            results[method] = {"n": int(values.size), "coefficient": _clean_float(r.statistic), "pValue": _clean_float(r.pvalue), "significanceDecisionGenerated": False, "causalInterpretationGenerated": False}
        elif method == "linear-regression":
            if values.size < 2 or np.std(predictor) == 0:
                raise ValueError("linear-regression requires 2+ observations and a non-constant predictor")
            r = stats.linregress(predictor, values)
            fitted = r.intercept + r.slope * predictor; residuals = values - fitted
            ss_res = float(np.sum(residuals ** 2)); rmse = math.sqrt(ss_res / values.size); mae = float(np.mean(np.abs(residuals)))
            dw_den = float(np.sum(residuals ** 2)); dw = None if dw_den == 0 else float(np.sum(np.diff(residuals) ** 2) / dw_den)
            residual_shapiro = None
            if 3 <= residuals.size <= 5000 and float(np.std(residuals)) > 0:
                sr = stats.shapiro(residuals)
                residual_shapiro = {"statistic": _clean_float(sr.statistic), "pValue": _clean_float(sr.pvalue), "normalityDecisionGenerated": False}
            results[method] = {
                "n": int(values.size), "slope": _clean_float(r.slope), "intercept": _clean_float(r.intercept),
                "rValue": _clean_float(r.rvalue), "rSquared": _clean_float(r.rvalue ** 2),
                "pValue": _clean_float(r.pvalue), "slopeStandardError": _clean_float(r.stderr),
                "interceptStandardError": _clean_float(getattr(r, "intercept_stderr", None)),
                "residualDiagnostics": {"rmse": _clean_float(rmse), "mae": _clean_float(mae), "meanResidual": _clean_float(np.mean(residuals)), "durbinWatson": _clean_float(dw), "shapiro": residual_shapiro},
                "significanceDecisionGenerated": False, "causalInterpretationGenerated": False, "modelValidityInferred": False,
            }
    return results


def analyze(req: StatisticalAnalysisRequest) -> Dict[str, Any]:
    jobs, source = _source_jobs(req)
    rows, excluded = _extract_rows(req, jobs)
    results = _compute_methods(req, rows)
    provenance = {
        "projectKey": req.projectKey,
        "campaignHash": source.get("campaignHash"),
        "campaignStateHash": source.get("campaignStateHash"),
        "protocolHash": source.get("protocolHash"),
        "studyHash": source.get("studyHash"),
        "jobHashes": {r["jobId"]: r.get("jobHash") for r in rows},
        "requestHashes": {r["jobId"]: r.get("requestHash") for r in rows},
        "resultHashes": {r["jobId"]: r.get("resultHash") for r in rows},
    }
    seed = {
        "projectKey": req.projectKey, "analysisKey": req.analysisKey, "title": req.title,
        "campaignHash": req.campaignHash or None, "jobIds": [r["jobId"] for r in rows],
        "resultMetricPath": req.resultMetricPath, "groupParameterPath": req.groupParameterPath or None,
        "predictorParameterPath": req.predictorParameterPath or None, "methods": req.methods,
        "referenceValue": req.referenceValue, "confidenceLevel": req.confidenceLevel,
        "researcherInterpretation": req.researcherInterpretation, "notes": req.notes,
        "results": results, "provenance": provenance,
    }
    out = {
        "ok": True, "schema": ANALYSIS_SCHEMA, "version": VERSION,
        **seed,
        "observationCount": len(rows), "excludedObservationCount": len(excluded),
        "observations": rows, "excludedObservations": excluded,
        "source": source,
        "boundaries": manifest()["boundaries"],
    }
    out["analysisHash"] = content_hash(seed)
    out["analysisRef"] = f"sc://workbench/statistical-analysis/{req.projectKey}/{out['analysisHash']}"
    return out


def save_analysis(req: SaveStatisticalAnalysisRequest) -> Dict[str, Any]:
    base = set(StatisticalAnalysisRequest.model_fields)
    result = analyze(StatisticalAnalysisRequest(**req.model_dump(include=base)))
    record = {**result, "createdBy": req.createdBy, "recordLabel": req.recordLabel, "createdAt": _now()}
    record["recordHash"] = content_hash({k: v for k, v in record.items() if k not in {"createdAt", "recordHash", "idempotent"}})
    path = _analysis_path(req.projectKey, result["analysisHash"])
    if path.exists():
        existing = _json_read(path)
        expected = content_hash({k: v for k, v in existing.items() if k not in {"createdAt", "recordHash", "idempotent"}})
        if existing.get("recordHash") != expected:
            raise ValueError("stored statistical analysis failed integrity validation")
        existing["idempotent"] = True
        return existing
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_json_write(path, record)
    record["idempotent"] = False
    return record


def load_analysis(project_key: str, analysis_hash: str) -> Dict[str, Any]:
    load_project(project_key)
    path = _analysis_path(project_key, analysis_hash)
    if not path.exists():
        raise FileNotFoundError("statistical analysis not found")
    rec = _json_read(path)
    if rec.get("projectKey") != project_key or rec.get("analysisHash") != analysis_hash:
        raise ValueError("statistical analysis identity mismatch")
    expected = content_hash({k: v for k, v in rec.items() if k not in {"createdAt", "recordHash", "idempotent"}})
    if rec.get("recordHash") != expected:
        raise ValueError("statistical analysis failed integrity validation")
    return rec


def list_analyses(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    rows: List[Dict[str, Any]] = []
    root = _analysis_dir(project_key)
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                rec = _json_read(path)
                if rec.get("projectKey") != project_key:
                    continue
                rows.append({k: rec.get(k) for k in ("analysisHash", "analysisRef", "analysisKey", "title", "campaignHash", "resultMetricPath", "methods", "observationCount", "createdBy", "createdAt", "recordHash")})
            except Exception:
                continue
    rows.sort(key=lambda x: str(x.get("createdAt") or ""), reverse=True)
    return {"ok": True, "schema": ANALYSIS_SCHEMA, "version": VERSION, "projectKey": project_key, "analysisCount": len(rows), "analyses": rows}


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key)
    campaigns = list_campaigns(project_key)
    jobs = list_jobs(project_key)
    completed = [x for x in jobs.get("jobs", []) if x.get("status") == "completed"]
    analyses = list_analyses(project_key)
    out = {
        "ok": True, "schema": CATALOG_SCHEMA, "version": VERSION, "projectKey": project_key,
        "campaignCount": campaigns.get("campaignCount", 0), "campaigns": campaigns.get("campaigns", []),
        "completedJobCount": len(completed), "completedJobs": completed,
        "analysisCount": analyses.get("analysisCount", 0), "analyses": analyses.get("analyses", []),
        "boundaries": {"catalogRunsAnalysis": False, "catalogMutatesSources": False, "catalogRunsJobs": False, "catalogInfersScientificValidity": False},
    }
    out["catalogHash"] = content_hash(out)
    return out


def core_plan(req: CoreStatisticalPlanRequest) -> Dict[str, Any]:
    analysis = load_analysis(req.projectKey, req.analysisHash)
    cfg = core_config()
    out = {
        "ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION,
        "projectKey": req.projectKey, "analysisHash": req.analysisHash, "analysisRef": analysis.get("analysisRef"),
        "coreProjectEntityId": req.coreProjectEntityId or req.projectKey, "coreSessionId": req.coreSessionId,
        "visibility": req.visibility, "createdBy": req.createdBy, "coreEnabled": bool(cfg.get("enabled")), "coreTarget": cfg.get("baseUrl") or "",
        "bindingPlan": {
            "objectType": "workbench.statistical-analysis", "objectRef": analysis.get("analysisRef"), "objectHash": req.analysisHash,
            "campaignHash": analysis.get("campaignHash"), "methods": analysis.get("methods"), "resultMetricPath": analysis.get("resultMetricPath"),
            "sourceResultHashes": analysis.get("provenance", {}).get("resultHashes", {}), "role": "statistical-analytical-view",
        },
        "boundaries": {
            "automaticCoreDispatchAuthorized": False, "automaticCorePersistenceAuthorized": False,
            "coreGovernanceAuthorityPreserved": True, "significanceDecisionGenerated": False,
            "hypothesisDecisionGenerated": False, "causalInferenceGenerated": False, "scientificValidityInferred": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


def _wrap(fn, *args):
    try:
        return fn(*args)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/statistical-workspace/manifest")
def route_manifest(): return manifest()

@router.get("/statistical-workspace/source-catalog/{project_key}")
def route_catalog(project_key: str): return _wrap(source_catalog, project_key)

@router.post("/statistical-workspace/analyze")
def route_analyze(req: StatisticalAnalysisRequest): return _wrap(analyze, req)

@router.post("/statistical-workspace/analyses")
def route_save(req: SaveStatisticalAnalysisRequest): return _wrap(save_analysis, req)

@router.get("/statistical-workspace/analyses/{project_key}")
def route_list(project_key: str): return _wrap(list_analyses, project_key)

@router.get("/statistical-workspace/analyses/{project_key}/{analysis_hash}")
def route_get(project_key: str, analysis_hash: str): return _wrap(load_analysis, project_key, analysis_hash)

@router.post("/integration/core/statistical-workspace/plan")
def route_core(req: CoreStatisticalPlanRequest): return _wrap(core_plan, req)

@router.get("/v930/status")
def status():
    m = manifest()
    return {
        "ok": True, "schema": SCHEMA, "version": VERSION, "release": m["release"],
        "statisticalAnalysisDiagnosticWorkspace": True,
        "explicitStatisticalMethodSelection": True,
        "contentAddressedStatisticalAnalyses": True,
        "campaignResultAnalysis": True,
        "automaticSignificanceDecision": False,
        "automaticCausalInference": False,
        "automaticScientificValidityInference": False,
        "automaticCoreDispatch": False,
        "manifestHash": m["manifestHash"],
    }

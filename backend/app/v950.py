"""Workbench v9.5.0 — Model Calibration & Parameter Estimation.

Explicit, provenance-preserving calibration of model parameters against researcher-
authored target observations using completed Workbench campaign results. The
workspace supports objective scoring of observed campaign runs and bounded
weighted/robust parameter estimation through transparent linear response surfaces.

Calibration is an analytical operation, not scientific validation: the workspace
does not declare a model correct, select a scientifically preferred model, infer
causality, choose priors, execute new jobs, or dispatch to Platform Core.
"""
from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from scipy import optimize, stats

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import load_project
from .v840 import _load_job
from .v920 import _load_state, list_campaigns, load_campaign
from .v930 import _finite_float, _nested_get

VERSION = APP_VERSION
SCHEMA = "sc-workbench-model-calibration-parameter-estimation/1.0"
PROBLEM_SCHEMA = "sc-workbench-calibration-problem/1.0"
CALIBRATION_SCHEMA = "sc-workbench-model-calibration/1.0"
CATALOG_SCHEMA = "sc-workbench-model-calibration-source-catalog/1.0"
ANALYSIS_PLAN_SCHEMA = "sc-workbench-model-calibration-analysis-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-model-calibration-core-plan/1.0"
router = APIRouter(tags=["workbench-v950-model-calibration-parameter-estimation"])

MAX_PARAMETERS = 32
MAX_TARGETS = 64
Estimator = Literal["campaign-search", "linear-response-surface"]
Loss = Literal["least-squares", "weighted-least-squares", "huber"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _calibration_dir(project_key: str) -> Path:
    return _store_root() / "model-calibrations" / _stable_id(project_key)


def _calibration_path(project_key: str, calibration_hash: str) -> Path:
    return _calibration_dir(project_key) / f"{calibration_hash}.json"


class CalibrationParameter(BaseModel):
    path: str = Field(min_length=1, max_length=300)
    lower: float
    upper: float
    initial: float | None = None
    label: str = Field(default="", max_length=500)
    unit: str = Field(default="", max_length=120)

    @model_validator(mode="after")
    def validate_parameter(self):
        self.path = self.path.strip(); self.label = self.label.strip(); self.unit = self.unit.strip()
        if not math.isfinite(self.lower) or not math.isfinite(self.upper) or not self.lower < self.upper:
            raise ValueError("parameter requires finite lower < upper")
        if self.initial is not None and not self.lower <= self.initial <= self.upper:
            raise ValueError("parameter initial must lie within bounds")
        return self


class TargetObservation(BaseModel):
    metricPath: str = Field(min_length=1, max_length=300)
    observedValue: float
    weight: float = Field(default=1.0, gt=0)
    label: str = Field(default="", max_length=500)
    unit: str = Field(default="", max_length=120)

    @model_validator(mode="after")
    def validate_target(self):
        self.metricPath = self.metricPath.strip(); self.label = self.label.strip(); self.unit = self.unit.strip()
        if not math.isfinite(self.observedValue) or not math.isfinite(self.weight):
            raise ValueError("target observedValue and weight must be finite")
        return self


class CalibrationRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    calibrationKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    campaignHash: str = Field(min_length=64, max_length=64)
    estimator: Estimator = "linear-response-surface"
    loss: Loss = "weighted-least-squares"
    parameters: List[CalibrationParameter] = Field(min_length=1, max_length=MAX_PARAMETERS)
    targets: List[TargetObservation] = Field(min_length=1, max_length=MAX_TARGETS)
    confidenceLevel: float = Field(default=0.95, gt=0.5, lt=1.0)
    huberScale: float = Field(default=1.0, gt=0)
    assumptions: List[str] = Field(default_factory=list, max_length=200)
    researcherInterpretation: str = Field(default="", max_length=12000)
    notes: str = Field(default="", max_length=12000)

    @model_validator(mode="after")
    def validate_calibration(self):
        self.projectKey = self.projectKey.strip(); self.calibrationKey = self.calibrationKey.strip(); self.title = self.title.strip()
        p = [x.path for x in self.parameters]; t = [x.metricPath for x in self.targets]
        if len(p) != len(set(p)): raise ValueError("parameter paths must be unique")
        if len(t) != len(set(t)): raise ValueError("target metric paths must be unique")
        return self


class SaveCalibrationRequest(CalibrationRequest):
    createdBy: str = Field(default="workbench", max_length=160)
    recordLabel: str = Field(default="Model calibration", max_length=500)


class AnalysisPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    calibrationHash: str = Field(min_length=64, max_length=64)
    includeStatisticalDiagnostics: bool = True
    includeUncertaintySensitivity: bool = True
    createdBy: str = Field(default="workbench", max_length=160)


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    calibrationHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION,
        "release": "Model Calibration & Parameter Estimation",
        "product": PRODUCT_KEY, "runtime": RUNTIME_KIND,
        "estimators": ["campaign-search", "linear-response-surface"],
        "losses": ["least-squares", "weighted-least-squares", "huber"],
        "capabilities": {
            "researcherAuthoredCalibrationProblems": True,
            "campaignCandidateObjectiveScoring": True,
            "boundedParameterEstimation": True,
            "weightedLeastSquaresCalibration": True,
            "robustHuberCalibration": True,
            "linearResponseSurfaceEstimation": True,
            "identifiabilityDiagnostics": True,
            "residualDiagnostics": True,
            "approximateParameterIntervals": True,
            "contentAddressedCalibrationRecords": True,
            "calibrationAnalysisPlanning": True,
            "provenancePreservation": True,
            "platformCoreCalibrationPlanning": True,
        },
        "boundaries": {
            "automaticModelValidityInference": False,
            "automaticScientificAcceptance": False,
            "automaticPreferredModelSelection": False,
            "automaticCausalInference": False,
            "automaticPriorSelection": False,
            "automaticJobExecution": False,
            "automaticCalibrationExperimentDispatch": False,
            "automaticCoreDispatch": False,
            "parameterIntervalsAreApproximate": True,
            "platformCoreGovernanceReplaced": False,
        },
    }
    out["manifestHash"] = content_hash(out); return out


def _parameter_value(job: Dict[str, Any], path: str) -> float | None:
    params = ((job.get("metadata") or {}).get("parameterValues") or {})
    if path in params: return _finite_float(params[path])
    try: return _finite_float(_nested_get(params, path))
    except KeyError: return None


def _metric_value(job: Dict[str, Any], path: str) -> float | None:
    try: return _finite_float(_nested_get(job.get("result") or {}, path))
    except KeyError: return None


def _campaign_rows(req: CalibrationRequest):
    load_project(req.projectKey)
    campaign = load_campaign(req.projectKey, req.campaignHash)
    state = _load_state(req.projectKey, req.campaignHash)
    rows, excluded = [], []
    for item in (state.get("jobs") or {}).values():
        jid = str(item.get("jobId") or "")
        if not jid: continue
        try: job = _load_job(jid)
        except Exception: continue
        if job.get("projectKey") != req.projectKey or job.get("status") != "completed": continue
        params = {p.path: _parameter_value(job, p.path) for p in req.parameters}
        metrics = {t.metricPath: _metric_value(job, t.metricPath) for t in req.targets}
        good = all(v is not None for v in params.values()) and all(v is not None for v in metrics.values())
        if good:
            rows.append({"jobId": jid, "parameters": params, "metrics": metrics, "jobHash": job.get("jobHash"), "resultHash": job.get("resultHash")})
        else:
            excluded.append({"jobId": jid, "reason": "missing-or-nonnumeric-parameter-or-target-metric"})
    if not rows: raise ValueError("no complete completed campaign observations are available for calibration")
    return campaign, state, rows, excluded


def _weights(req: CalibrationRequest) -> np.ndarray:
    if req.loss == "least-squares": return np.ones(len(req.targets), dtype=float)
    return np.array([t.weight for t in req.targets], dtype=float)


def _raw_residuals(req: CalibrationRequest, predicted: Dict[str, float]) -> np.ndarray:
    return np.array([float(predicted[t.metricPath]) - t.observedValue for t in req.targets], dtype=float)


def _scaled_residuals(req: CalibrationRequest, predicted: Dict[str, float]) -> np.ndarray:
    return _raw_residuals(req, predicted) * np.sqrt(_weights(req))


def _objective(req: CalibrationRequest, predicted: Dict[str, float]) -> float:
    r = _scaled_residuals(req, predicted)
    if req.loss != "huber": return float(np.sum(r * r))
    a = np.abs(r); d = req.huberScale
    return float(np.sum(np.where(a <= d, 0.5 * r * r, d * (a - 0.5 * d))))


def compose_problem(req: CalibrationRequest) -> Dict[str, Any]:
    campaign, state, rows, excluded = _campaign_rows(req)
    seed = {
        "projectKey": req.projectKey, "calibrationKey": req.calibrationKey, "title": req.title,
        "campaignHash": req.campaignHash, "campaignStateHash": state.get("stateHash"),
        "estimator": req.estimator, "loss": req.loss,
        "parameters": [p.model_dump() for p in req.parameters], "targets": [t.model_dump() for t in req.targets],
        "confidenceLevel": req.confidenceLevel, "huberScale": req.huberScale,
        "assumptions": req.assumptions, "researcherInterpretation": req.researcherInterpretation, "notes": req.notes,
    }
    ph = content_hash(seed)
    out = {"ok": True, "schema": PROBLEM_SCHEMA, "version": VERSION, **seed,
           "problemHash": ph, "problemRef": f"sc://workbench/model-calibration-problem/{req.projectKey}/{ph}",
           "availableObservationCount": len(rows), "excludedObservationCount": len(excluded), "excludedObservations": excluded,
           "provenance": {"campaignRef": campaign.get("campaignRef"), "campaignStateHash": state.get("stateHash")},
           "boundaries": manifest()["boundaries"]}
    return out


def _candidate_search(req: CalibrationRequest, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    scored = []
    for row in rows:
        obj = _objective(req, row["metrics"])
        residuals = {t.metricPath: row["metrics"][t.metricPath] - t.observedValue for t in req.targets}
        scored.append({"jobId": row["jobId"], "objective": obj, "parameters": row["parameters"], "predicted": row["metrics"], "residuals": residuals, "resultHash": row.get("resultHash")})
    scored.sort(key=lambda x: (x["objective"], x["jobId"]))
    chosen = scored[0]
    return {
        "estimator": "campaign-search", "estimatedParameters": chosen["parameters"],
        "predictedTargets": chosen["predicted"], "residuals": chosen["residuals"],
        "objective": chosen["objective"], "sourceJobId": chosen["jobId"],
        "candidateScores": scored,
        "diagnostics": {"candidateCount": len(scored), "continuousOptimizationPerformed": False, "responseSurfaceFitted": False},
        "parameterIntervals": {},
    }


def _fit_surfaces(req: CalibrationRequest, rows: List[Dict[str, Any]]):
    ppaths = [p.path for p in req.parameters]; tpaths = [t.metricPath for t in req.targets]
    X = np.array([[r["parameters"][p] for p in ppaths] for r in rows], dtype=float)
    A = np.column_stack([np.ones(len(X)), X])
    rank = int(np.linalg.matrix_rank(A)); cols = A.shape[1]
    cond = float(np.linalg.cond(A)) if A.size else float("inf")
    surfaces = {}; B = []
    for path in tpaths:
        y = np.array([r["metrics"][path] for r in rows], dtype=float)
        beta = np.linalg.lstsq(A, y, rcond=None)[0]
        pred = A @ beta; resid = y - pred
        ss_res = float(np.sum(resid**2)); ss_tot = float(np.sum((y-y.mean())**2))
        r2 = None if ss_tot == 0 else float(1 - ss_res/ss_tot)
        surfaces[path] = {"intercept": float(beta[0]), "coefficients": {p: float(beta[i+1]) for i,p in enumerate(ppaths)}, "rSquared": r2, "rmse": float(np.sqrt(np.mean(resid**2)))}
        B.append(beta)
    return np.array(B), surfaces, {"designRank": rank, "designColumns": cols, "fullColumnRank": rank == cols, "conditionNumber": cond, "observationCount": len(rows)}


def _linear_surface_estimate(req: CalibrationRequest, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    ppaths = [p.path for p in req.parameters]; tpaths = [t.metricPath for t in req.targets]
    if len(rows) < len(req.parameters) + 1:
        raise ValueError("linear-response-surface requires at least parameterCount + 1 complete observations")
    B, surfaces, ident = _fit_surfaces(req, rows)
    if not ident["fullColumnRank"]:
        raise ValueError("linear-response-surface design matrix is rank deficient")
    target = np.array([t.observedValue for t in req.targets], dtype=float)
    weights = _weights(req)
    lower = np.array([p.lower for p in req.parameters], dtype=float); upper = np.array([p.upper for p in req.parameters], dtype=float)
    initial = np.array([p.initial if p.initial is not None else (p.lower+p.upper)/2 for p in req.parameters], dtype=float)
    def predict(x): return np.array([b[0] + np.dot(b[1:], x) for b in B], dtype=float)
    def residual(x): return (predict(x) - target) * np.sqrt(weights)
    loss = "huber" if req.loss == "huber" else "linear"
    fit = optimize.least_squares(residual, initial, bounds=(lower, upper), loss=loss, f_scale=req.huberScale)
    pred = predict(fit.x); raw = pred-target; scaled = residual(fit.x)
    estimated = {p: float(fit.x[i]) for i,p in enumerate(ppaths)}
    predicted = {tpaths[i]: float(pred[i]) for i in range(len(tpaths))}
    residuals = {tpaths[i]: float(raw[i]) for i in range(len(tpaths))}
    intervals = {}
    jac = np.asarray(fit.jac, dtype=float)
    rank = int(np.linalg.matrix_rank(jac)) if jac.size else 0
    dof = len(target)-len(fit.x)
    if jac.size and rank == len(fit.x) and dof > 0:
        sigma2 = float(np.sum(scaled**2) / dof)
        cov = sigma2 * np.linalg.pinv(jac.T @ jac)
        z = float(stats.norm.ppf((1+req.confidenceLevel)/2))
        for i,p in enumerate(req.parameters):
            se = math.sqrt(max(float(cov[i,i]),0.0)); intervals[p.path] = {"estimate": float(fit.x[i]), "standardError": se, "lower": float(fit.x[i]-z*se), "upper": float(fit.x[i]+z*se), "confidenceLevel": req.confidenceLevel, "approximate": True}
    return {
        "estimator": "linear-response-surface", "estimatedParameters": estimated,
        "predictedTargets": predicted, "residuals": residuals, "objective": _objective(req, predicted),
        "responseSurfaces": surfaces, "parameterIntervals": intervals,
        "diagnostics": {**ident, "optimizerSuccess": bool(fit.success), "optimizerStatus": int(fit.status), "optimizerMessage": str(fit.message), "optimizerEvaluations": int(fit.nfev), "optimizerCost": float(fit.cost), "calibrationJacobianRank": rank, "calibrationDegreesOfFreedom": dof, "parameterIntervalsAvailable": bool(intervals), "continuousOptimizationPerformed": True, "responseSurfaceFitted": True},
    }


def estimate(req: CalibrationRequest) -> Dict[str, Any]:
    problem = compose_problem(req); campaign, state, rows, excluded = _campaign_rows(req)
    result = _candidate_search(req, rows) if req.estimator == "campaign-search" else _linear_surface_estimate(req, rows)
    residual_values = np.array(list(result["residuals"].values()), dtype=float)
    result["residualSummary"] = {"count": int(len(residual_values)), "mean": float(np.mean(residual_values)), "meanAbsolute": float(np.mean(np.abs(residual_values))), "rootMeanSquare": float(np.sqrt(np.mean(residual_values**2))), "maxAbsolute": float(np.max(np.abs(residual_values)))}
    seed = {"problemHash": problem["problemHash"], "projectKey": req.projectKey, "campaignHash": req.campaignHash, "campaignStateHash": state.get("stateHash"), "estimator": req.estimator, "loss": req.loss, "result": result}
    ch = content_hash(seed)
    return {"ok": True, "schema": CALIBRATION_SCHEMA, "version": VERSION, "projectKey": req.projectKey,
            "calibrationKey": req.calibrationKey, "title": req.title, "problemHash": problem["problemHash"],
            "campaignHash": req.campaignHash, "campaignStateHash": state.get("stateHash"), "estimator": req.estimator, "loss": req.loss, "confidenceLevel": req.confidenceLevel, "calibrationHash": ch,
            "calibrationRef": f"sc://workbench/model-calibration/{req.projectKey}/{ch}", "result": result,
            "sourceObservationCount": len(rows), "excludedObservationCount": len(excluded), "excludedObservations": excluded,
            "provenance": {"campaignRef": campaign.get("campaignRef"), "resultHashes": {r["jobId"]: r.get("resultHash") for r in rows}, "jobHashes": {r["jobId"]: r.get("jobHash") for r in rows}},
            "researcherInterpretation": req.researcherInterpretation, "assumptions": req.assumptions, "notes": req.notes,
            "boundaries": manifest()["boundaries"]}


def _record_hash(rec: Dict[str, Any]) -> str:
    return content_hash({k:v for k,v in rec.items() if k not in {"createdAt","recordHash","idempotent"}})


def save_calibration(req: SaveCalibrationRequest) -> Dict[str, Any]:
    out = estimate(req)
    rec = {**out, "createdBy": req.createdBy, "recordLabel": req.recordLabel, "createdAt": _now()}
    rec["recordHash"] = _record_hash(rec)
    path = _calibration_path(req.projectKey, rec["calibrationHash"]); path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    if existed:
        old = _json_read(path)
        if old.get("recordHash") != rec["recordHash"]: raise ValueError("existing calibration hash collision or record mismatch")
        old["idempotent"] = True; return old
    _atomic_json_write(path, rec); rec["idempotent"] = False; return rec


def load_calibration(project_key: str, calibration_hash: str) -> Dict[str, Any]:
    load_project(project_key); path = _calibration_path(project_key, calibration_hash)
    if not path.exists(): raise FileNotFoundError("model calibration not found")
    rec = _json_read(path)
    if rec.get("projectKey") != project_key or rec.get("calibrationHash") != calibration_hash: raise ValueError("model calibration identity mismatch")
    if rec.get("recordHash") != _record_hash(rec): raise ValueError("model calibration failed integrity validation")
    return rec


def list_calibrations(project_key: str) -> Dict[str, Any]:
    load_project(project_key); rows=[]; root=_calibration_dir(project_key)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r=_json_read(p)
                if r.get("projectKey")==project_key: rows.append({k:r.get(k) for k in ("calibrationHash","calibrationRef","calibrationKey","title","campaignHash","createdBy","createdAt","recordHash")})
            except Exception: pass
    rows.sort(key=lambda x:str(x.get("createdAt") or ""),reverse=True)
    return {"ok":True,"schema":CALIBRATION_SCHEMA,"version":VERSION,"projectKey":project_key,"calibrationCount":len(rows),"calibrations":rows}


def source_catalog(project_key: str) -> Dict[str, Any]:
    load_project(project_key); campaigns=list_campaigns(project_key); calibrations=list_calibrations(project_key)
    out={"ok":True,"schema":CATALOG_SCHEMA,"version":VERSION,"projectKey":project_key,
         "campaignCount":campaigns.get("campaignCount",0),"campaigns":campaigns.get("campaigns",[]),
         "calibrationCount":calibrations.get("calibrationCount",0),"calibrations":calibrations.get("calibrations",[]),
         "boundaries":{"catalogExecutesJobs":False,"catalogPerformsCalibration":False,"catalogInfersModelValidity":False}}
    out["catalogHash"]=content_hash(out); return out


def analysis_plan(req: AnalysisPlanRequest) -> Dict[str, Any]:
    rec=load_calibration(req.projectKey,req.calibrationHash)
    planned=[]
    if req.includeStatisticalDiagnostics: planned.append({"target":"statistical-analysis","purpose":"residual-and-fit-diagnostics","automaticDispatch":False})
    if req.includeUncertaintySensitivity: planned.append({"target":"uncertainty-sensitivity","purpose":"parameter-uncertainty-and-sensitivity-follow-up","automaticDispatch":False})
    out={"ok":True,"schema":ANALYSIS_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"calibrationHash":req.calibrationHash,"calibrationRef":rec.get("calibrationRef"),"createdBy":req.createdBy,"plannedHandoffs":planned,"boundaries":{"automaticAnalysisDispatch":False,"automaticScientificInterpretation":False,"automaticPreferredModelSelection":False}}
    out["planHash"]=content_hash(out); return out


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    rec=load_calibration(req.projectKey,req.calibrationHash); cfg=core_config()
    out={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"calibrationHash":req.calibrationHash,"calibrationRef":rec.get("calibrationRef"),"coreProjectEntityId":req.coreProjectEntityId or req.projectKey,"coreSessionId":req.coreSessionId,"visibility":req.visibility,"createdBy":req.createdBy,"coreEnabled":bool(cfg.get("enabled")),"coreTarget":cfg.get("baseUrl") or "","bindingPlan":{"objectType":"workbench.model-calibration","objectRef":rec.get("calibrationRef"),"objectHash":req.calibrationHash,"campaignHash":rec.get("campaignHash"),"problemHash":rec.get("problemHash"),"role":"model-calibration-parameter-estimation"},"boundaries":{"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"coreGovernanceAuthorityPreserved":True,"modelValidityInferred":False,"scientificAcceptanceInferred":False}}
    out["planHash"]=content_hash(out); return out


def _wrap(fn,*args):
    try: return fn(*args)
    except FileNotFoundError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except (ValueError,RuntimeError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc


@router.get("/model-calibration/manifest")
def route_manifest(): return manifest()
@router.get("/model-calibration/source-catalog/{project_key}")
def route_catalog(project_key:str): return _wrap(source_catalog,project_key)
@router.post("/model-calibration/compose")
def route_compose(req:CalibrationRequest): return _wrap(compose_problem,req)
@router.post("/model-calibration/estimate")
def route_estimate(req:CalibrationRequest): return _wrap(estimate,req)
@router.post("/model-calibration/calibrations")
def route_save(req:SaveCalibrationRequest): return _wrap(save_calibration,req)
@router.get("/model-calibration/calibrations/{project_key}")
def route_list(project_key:str): return _wrap(list_calibrations,project_key)
@router.get("/model-calibration/calibrations/{project_key}/{calibration_hash}")
def route_get(project_key:str,calibration_hash:str): return _wrap(load_calibration,project_key,calibration_hash)
@router.post("/model-calibration/analysis-plan")
def route_analysis(req:AnalysisPlanRequest): return _wrap(analysis_plan,req)
@router.post("/integration/core/model-calibration/plan")
def route_core(req:CorePlanRequest): return _wrap(core_plan,req)
@router.get("/v950/status")
def status():
    m=manifest(); return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":m["release"],"modelCalibrationParameterEstimation":True,"campaignCandidateObjectiveScoring":True,"boundedParameterEstimation":True,"robustHuberCalibration":True,"automaticModelValidityInference":False,"automaticPreferredModelSelection":False,"automaticJobExecution":False,"automaticCoreDispatch":False,"manifestHash":m["manifestHash"]}

"""Workbench v6.10.0 — Predictive Intelligence Runtime Integration.

Executes deterministic predictive calculations in Workbench and prepares
Platform Core predictive-intelligence persistence plans. Core owns predictive
registries, provenance, calibration evidence, packages, and visual predictive
semantics. Workbench owns specialist execution and never dispatches or persists
into Core automatically.
"""
from __future__ import annotations

import math
import statistics
from statistics import NormalDist
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import CORE_RUNTIME_CONTRACT, _authorize_core_route
from .v650 import PRODUCT_REF
from .v660 import CORE_UNIFIED_RUNTIME_CONTRACT
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT
from .v690 import CORE_UNIFIED_VISUAL_CONTRACT

VERSION = APP_VERSION
SCHEMA = "sc-workbench-core-predictive-intelligence-runtime/1.0"
FORECAST_SCHEMA = "sc-workbench-predictive-forecast-result/1.0"
BACKTEST_SCHEMA = "sc-workbench-predictive-backtest-result/1.0"
CALIBRATION_SCHEMA = "sc-workbench-predictive-calibration-result/1.0"
CORE_REQUEST_SCHEMA = "sc-workbench-core-predictive-request/1.0"
BRIDGE_REF = "workbench:/integration/core/predictive-intelligence"

CORE_PREDICTIVE_MODEL_CONTRACT = "sc.predictive.model.v1"
CORE_FORECAST_CONTRACT = "sc.predictive.forecast-provenance.v1"
CORE_BACKTEST_CONTRACT = "sc.predictive.backtest-plan.v1"
CORE_PROBABILISTIC_FORECAST_CONTRACT = "sc.predictive.probabilistic-forecast.v1"
CORE_CALIBRATION_CONTRACT = "sc.predictive.calibration-study.v1"
CORE_ENSEMBLE_CONTRACT = "sc.predictive.ensemble.v1"
CORE_REPRODUCIBLE_PACKAGE_CONTRACT = "sc.predictive.reproducible-package.v1"
CORE_VISUAL_PREDICTIVE_CONTRACT = "sc.visual-runtime.predictive-intelligence.v1"

CORE_PATHS = {
    "readiness": "/v1/predictive-intelligence/readiness",
    "models": "/v1/predictive-intelligence/models",
    "targets": "/v1/predictive-intelligence/models/{model_id}/targets",
    "features": "/v1/predictive-intelligence/models/{model_id}/features",
    "trainingWindows": "/v1/predictive-intelligence/models/{model_id}/training-windows",
    "forecastRuns": "/v1/predictive-intelligence/models/{model_id}/forecast-runs",
    "forecastObservations": "/v1/predictive-intelligence/models/{model_id}/forecast-runs/{run_id}/observations",
    "evaluations": "/v1/predictive-intelligence/models/{model_id}/evaluations",
    "handoffs": "/v1/predictive-intelligence/models/{model_id}/handoffs",
    "snapshots": "/v1/predictive-intelligence/models/{model_id}/snapshots",
    "backtestPlans": "/v1/predictive-intelligence/models/{model_id}/backtest-plans",
    "backtestFolds": "/v1/predictive-intelligence/models/{model_id}/backtest-plans/{plan_id}/folds",
    "backtestEvaluations": "/v1/predictive-intelligence/models/{model_id}/backtest-plans/{plan_id}/evaluations",
    "probabilisticForecasts": "/v1/predictive-intelligence/models/{model_id}/probabilistic-forecasts",
    "calibrationStudies": "/v1/predictive-intelligence/models/{model_id}/calibration-studies",
    "calibrationBins": "/v1/predictive-intelligence/models/{model_id}/calibration-studies/{study_id}/bins",
    "probabilisticEvaluations": "/v1/predictive-intelligence/models/{model_id}/probabilistic-evaluations",
    "ensembles": "/v1/predictive-intelligence/ensembles",
    "visualReadiness": "/v1/visual-runtime/predictive/readiness",
    "visualWorkspaces": "/v1/visual-runtime/predictive/compositions/{composition_id}/workspaces",
    "visualForecastOverlays": "/v1/visual-runtime/predictive/workspaces/{workspace_id}/forecast-overlays",
    "visualUncertaintyDisplays": "/v1/visual-runtime/predictive/workspaces/{workspace_id}/uncertainty-displays",
    "visualCalibrationDisplays": "/v1/visual-runtime/predictive/workspaces/{workspace_id}/calibration-displays",
}

SUPPORTED_METHODS = {"naive", "drift", "mean", "moving-average", "linear-trend"}
SUPPORTED_REPRESENTATIONS = {"point", "quantile", "interval", "parametric-distribution"}
router = APIRouter(tags=["workbench-v6100-predictive-intelligence-runtime"])


def _bad(exc: Exception) -> HTTPException:
    return exc if isinstance(exc, HTTPException) else HTTPException(status_code=422, detail=str(exc))


def _bounded(value: Any, limit: int = 1000) -> str:
    return str(value or "").strip()[:limit]


def _finite(values: List[float]) -> List[float]:
    out=[]
    for value in values:
        fv=float(value)
        if not math.isfinite(fv):
            raise ValueError("series values must be finite")
        out.append(fv)
    return out


def _core_request(path: str, data: Dict[str, Any], phase: str) -> Dict[str, Any]:
    out={
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


def predictive_manifest() -> Dict[str, Any]:
    out={
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
        "coreUnifiedVisualContract": CORE_UNIFIED_VISUAL_CONTRACT,
        "corePredictiveModelContract": CORE_PREDICTIVE_MODEL_CONTRACT,
        "coreForecastContract": CORE_FORECAST_CONTRACT,
        "coreBacktestContract": CORE_BACKTEST_CONTRACT,
        "coreProbabilisticForecastContract": CORE_PROBABILISTIC_FORECAST_CONTRACT,
        "coreCalibrationContract": CORE_CALIBRATION_CONTRACT,
        "coreEnsembleContract": CORE_ENSEMBLE_CONTRACT,
        "coreReproduciblePackageContract": CORE_REPRODUCIBLE_PACKAGE_CONTRACT,
        "coreVisualPredictiveContract": CORE_VISUAL_PREDICTIVE_CONTRACT,
        "corePaths": dict(CORE_PATHS),
        "forecastMethods": sorted(SUPPORTED_METHODS),
        "probabilisticRepresentations": sorted(SUPPORTED_REPRESENTATIONS),
        "capabilities": [
            "deterministic-point-forecasting",
            "linear-trend-and-drift-forecasting",
            "moving-average-forecasting",
            "forecast-residual-uncertainty-estimation",
            "quantile-and-interval-forecast-generation",
            "rolling-origin-backtesting",
            "mae-rmse-mape-evaluation",
            "binary-probability-brier-logloss-calibration",
            "reliability-bin-generation",
            "core-predictive-model-registration-planning",
            "core-forecast-provenance-registration-planning",
            "core-calibration-evidence-registration-planning",
            "v670-computation-lineage-integration",
            "v690-visual-predictive-integration",
        ],
        "boundaries": {
            "workbenchFitsAndExecutesPredictiveModels": True,
            "workbenchComputesForecastMetrics": True,
            "workbenchComputesCalibrationMetrics": True,
            "coreOwnsPredictiveRegistry": True,
            "coreOwnsForecastProvenance": True,
            "coreOwnsCalibrationEvidenceRegistry": True,
            "coreExecutesPredictiveModels": False,
            "coreRanksOrSelectsModels": False,
            "coreDeterminesTruth": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
            "arbitraryCoreCodeExecution": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


class ForecastRequest(BaseModel):
    projectEntityId: str
    modelKey: str
    modelName: str
    targetKey: str = "target"
    targetLabel: str = "Target"
    history: List[float] = Field(min_length=2)
    horizon: int = Field(default=1, ge=1, le=10000)
    method: Literal["naive", "drift", "mean", "moving-average", "linear-trend"] = "linear-trend"
    movingAverageWindow: int = Field(default=3, ge=1, le=10000)
    intervalLevel: float = Field(default=0.9, gt=0.0, lt=1.0)
    unit: str = ""
    workbenchExecutionRef: str = ""
    coreSessionId: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("projectEntityId", "modelKey", "modelName")
    @classmethod
    def required_text(cls, value: str) -> str:
        value=_bounded(value,300)
        if not value: raise ValueError("projectEntityId, modelKey, and modelName are required")
        return value


class BacktestRequest(BaseModel):
    history: List[float] = Field(min_length=4)
    method: Literal["naive", "drift", "mean", "moving-average", "linear-trend"] = "linear-trend"
    minimumTrainSize: int = Field(default=3, ge=2)
    movingAverageWindow: int = Field(default=3, ge=1)


class CalibrationRequest(BaseModel):
    probabilities: List[float] = Field(min_length=2)
    outcomes: List[int] = Field(min_length=2)
    bins: int = Field(default=10, ge=2, le=100)


class ModelPlanRequest(BaseModel):
    forecastResult: Dict[str, Any]
    modelKind: Literal["statistical", "machine-learning", "simulation", "hybrid", "rules-based", "external", "other"] = "statistical"
    visibility: Literal["private", "public"] = "private"


class ForecastCorePlanRequest(BaseModel):
    forecastResult: Dict[str, Any]
    coreModelId: str
    coreTargetId: str
    coreTrainingWindowId: str = ""

    @field_validator("coreModelId", "coreTargetId")
    @classmethod
    def core_ids_required(cls, value: str) -> str:
        value=_bounded(value,255)
        if not value: raise ValueError("Core-issued model and target IDs are required")
        return value


class CalibrationCorePlanRequest(BaseModel):
    calibrationResult: Dict[str, Any]
    coreModelId: str
    coreTargetId: str
    coreProbabilisticForecastId: str = ""
    coreCalibrationStudyId: str = ""

    @field_validator("coreModelId", "coreTargetId")
    @classmethod
    def required_ids(cls, value: str) -> str:
        value=_bounded(value,255)
        if not value: raise ValueError("Core-issued model and target IDs are required")
        return value


class VisualPredictivePlanRequest(BaseModel):
    forecastResult: Dict[str, Any]
    coreCompositionId: str
    coreForecastRunId: str = ""
    coreProbabilisticForecastId: str = ""
    coreCalibrationStudyId: str = ""
    coreWorkspaceId: str = ""
    targetViewIds: List[str] = Field(default_factory=list)

    @field_validator("coreCompositionId")
    @classmethod
    def composition_required(cls, value: str) -> str:
        value=_bounded(value,255)
        if not value: raise ValueError("coreCompositionId must be issued by Platform Core")
        return value


def _fit(history: List[float], method: str, window: int) -> Dict[str, Any]:
    y=_finite(history)
    n=len(y)
    if method == "naive":
        fitted=[None]+y[:-1]
        return {"intercept":y[-1],"slope":0.0,"fitted":fitted}
    if method == "mean":
        mu=statistics.fmean(y)
        return {"intercept":mu,"slope":0.0,"fitted":[mu]*n}
    if method == "moving-average":
        w=max(1,min(window,n)); fitted=[]
        for i in range(n):
            start=max(0,i-w)
            fitted.append(statistics.fmean(y[start:i]) if i>0 else y[0])
        return {"intercept":statistics.fmean(y[-w:]),"slope":0.0,"fitted":fitted,"window":w}
    if method == "drift":
        slope=(y[-1]-y[0])/(n-1)
        return {"intercept":y[-1],"slope":slope,"fitted":[y[0]+slope*i for i in range(n)]}
    xs=list(range(n)); xm=statistics.fmean(xs); ym=statistics.fmean(y)
    denom=sum((x-xm)**2 for x in xs)
    slope=sum((x-xm)*(v-ym) for x,v in zip(xs,y))/denom if denom else 0.0
    intercept=ym-slope*xm
    return {"intercept":intercept,"slope":slope,"fitted":[intercept+slope*x for x in xs]}


def _point_forecast(history: List[float], horizon: int, method: str, window: int) -> tuple[List[float], Dict[str,Any]]:
    y=_finite(history); fit=_fit(y,method,window); n=len(y)
    if method in {"naive","mean","moving-average"}:
        pts=[float(fit["intercept"])]*horizon
    elif method == "drift":
        pts=[y[-1]+fit["slope"]*h for h in range(1,horizon+1)]
    else:
        pts=[fit["intercept"]+fit["slope"]*(n+h) for h in range(horizon)]
    return pts,fit


def _residual_sigma(history: List[float], fit: Dict[str,Any]) -> float:
    vals=[]
    for actual,pred in zip(history,fit.get("fitted",[])):
        if pred is not None: vals.append(float(actual)-float(pred))
    if len(vals)<2: return 0.0
    return float(statistics.stdev(vals))


def execute_forecast(request: ForecastRequest) -> Dict[str, Any]:
    history=_finite(request.history)
    points,fit=_point_forecast(history,request.horizon,request.method,request.movingAverageWindow)
    sigma=_residual_sigma(history,fit)
    alpha=(1.0-request.intervalLevel)/2.0
    z=NormalDist().inv_cdf(1-alpha)
    intervals=[]
    for i,p in enumerate(points,1):
        scale=sigma*math.sqrt(i)
        intervals.append({"step":i,"point":p,"lower":p-z*scale,"upper":p+z*scale,"stddev":scale})
    out={
        "ok":True,"schema":FORECAST_SCHEMA,"version":VERSION,
        "projectEntityId":request.projectEntityId,"modelKey":request.modelKey,"modelName":request.modelName,
        "targetKey":request.targetKey,"targetLabel":request.targetLabel,"unit":request.unit,
        "method":request.method,"historyCount":len(history),"horizon":request.horizon,
        "pointForecast":points,"intervalLevel":request.intervalLevel,"intervalForecast":intervals,
        "modelState":{k:v for k,v in fit.items() if k!="fitted"},"residualStddev":sigma,
        "provenance":{"runtime_product":"workbench","workbench_version":VERSION,"workbench_execution_ref":request.workbenchExecutionRef or None,"core_session_id":request.coreSessionId or None},
        "metadata":dict(request.metadata),"calculated_by_workbench":True,"calculated_by_core":False,
    }
    out["resultHash"]=content_hash(out)
    return out


def execute_backtest(request: BacktestRequest) -> Dict[str, Any]:
    y=_finite(request.history); start=max(request.minimumTrainSize,2)
    if start>=len(y): raise ValueError("minimumTrainSize must leave at least one holdout observation")
    rows=[]
    for i in range(start,len(y)):
        pred,_=_point_forecast(y[:i],1,request.method,request.movingAverageWindow)
        p=pred[0]; a=y[i]; err=a-p
        rows.append({"index":i,"actual":a,"forecast":p,"error":err,"absoluteError":abs(err),"squaredError":err*err})
    mae=statistics.fmean(r["absoluteError"] for r in rows)
    rmse=math.sqrt(statistics.fmean(r["squaredError"] for r in rows))
    ape=[abs(r["error"]/r["actual"]) for r in rows if r["actual"]!=0]
    out={"ok":True,"schema":BACKTEST_SCHEMA,"version":VERSION,"method":request.method,"strategy":"expanding","folds":rows,"foldCount":len(rows),"metrics":{"mae":mae,"rmse":rmse,"mape":statistics.fmean(ape) if ape else None},"calculated_by_workbench":True,"calculated_by_core":False}
    out["resultHash"]=content_hash(out);return out


def execute_calibration(request: CalibrationRequest) -> Dict[str, Any]:
    if len(request.probabilities)!=len(request.outcomes): raise ValueError("probabilities and outcomes must have equal length")
    probs=[]; outcomes=[]
    for p,o in zip(request.probabilities,request.outcomes):
        p=float(p)
        if not 0<=p<=1: raise ValueError("probabilities must be between 0 and 1")
        if int(o) not in (0,1): raise ValueError("outcomes must be binary 0/1")
        probs.append(p);outcomes.append(int(o))
    eps=1e-12
    brier=statistics.fmean((p-o)**2 for p,o in zip(probs,outcomes))
    logloss=-statistics.fmean(o*math.log(max(p,eps))+(1-o)*math.log(max(1-p,eps)) for p,o in zip(probs,outcomes))
    bins=[]; ece=0.0; n=len(probs)
    for b in range(request.bins):
        lo=b/request.bins; hi=(b+1)/request.bins
        idx=[i for i,p in enumerate(probs) if (lo<=p<hi) or (b==request.bins-1 and p==1.0)]
        if not idx: continue
        meanp=statistics.fmean(probs[i] for i in idx); freq=statistics.fmean(outcomes[i] for i in idx)
        ece += len(idx)/n*abs(meanp-freq)
        bins.append({"bin_index":b,"lower_bound":lo,"upper_bound":hi,"mean_forecast":meanp,"observed_frequency":freq,"sample_count":len(idx)})
    out={"ok":True,"schema":CALIBRATION_SCHEMA,"version":VERSION,"sampleCount":n,"assessmentKind":"reliability","metrics":{"brier":brier,"logLoss":logloss,"expectedCalibrationError":ece},"bins":bins,"calculated_by_workbench":True,"calculated_by_core":False}
    out["resultHash"]=content_hash(out);return out


def _require_forecast(result: Dict[str,Any]) -> Dict[str,Any]:
    if result.get("schema")!=FORECAST_SCHEMA: raise ValueError(f"forecastResult.schema must be {FORECAST_SCHEMA}")
    return result


def build_model_plan(request: ModelPlanRequest) -> Dict[str,Any]:
    r=_require_forecast(dict(request.forecastResult))
    model={"model_key":r["modelKey"],"name":r["modelName"],"project_entity_id":r["projectEntityId"],"model_kind":request.modelKind,"runtime_product":"workbench","runtime_model_ref":f"workbench:model:{r['modelKey']}","model_version_ref":VERSION,"visibility":request.visibility,"provenance":{"workbench_result_hash":r.get("resultHash"),**dict(r.get("provenance") or {})},"metadata":{"method":r.get("method"),"horizon":r.get("horizon")}}
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"predictive-model-registration","coreRequests":[_core_request(CORE_PATHS["models"],model,"create-predictive-model")],"coreModelIdMustComeFromCore":True,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False}
    out["planHash"]=content_hash(out);return out


def build_forecast_core_plan(request: ForecastCorePlanRequest) -> Dict[str,Any]:
    r=_require_forecast(dict(request.forecastResult)); mid=request.coreModelId; tid=request.coreTargetId
    provenance={"source_product":"workbench","workbench_version":VERSION,"workbench_result_hash":r.get("resultHash"),**dict(r.get("provenance") or {})}
    reqs=[]
    target={"target_key":r.get("targetKey","target"),"label":r.get("targetLabel","Target"),"value_kind":"numeric","unit":r.get("unit") or None,"horizon":{"steps":r.get("horizon")},"source_ref":f"workbench:forecast:{r.get('resultHash')}","provenance":provenance}
    # Target request is included as an auditable template; caller may omit it when target already exists.
    reqs.append(_core_request(CORE_PATHS["targets"].format(model_id=mid),target,"ensure-predictive-target"))
    run={"run_key":f"workbench-{r.get('resultHash','')[:16]}","runtime_product":"workbench","runtime_run_ref":r.get("provenance",{}).get("workbench_execution_ref") or f"workbench:forecast:{r.get('resultHash')}","model_version_ref":VERSION,"input_manifest_hash":content_hash({"historyCount":r.get("historyCount"),"method":r.get("method")}),"status":"recorded","provenance":provenance,"metadata":{"method":r.get("method"),"horizon":r.get("horizon"),"training_window_id":request.coreTrainingWindowId or None}}
    reqs.append(_core_request(CORE_PATHS["forecastRuns"].format(model_id=mid),run,"register-forecast-run"))
    probabilistic={"model_id":mid,"target_id":tid,"representation":"interval","forecast":{"level":r.get("intervalLevel"),"intervals":r.get("intervalForecast",[]),"points":r.get("pointForecast",[])},"source_ref":f"workbench:forecast:{r.get('resultHash')}","provenance":provenance}
    reqs.append(_core_request(CORE_PATHS["probabilisticForecasts"].format(model_id=mid),probabilistic,"register-probabilistic-forecast"))
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"forecast-provenance-registration","coreModelId":mid,"coreTargetId":tid,"coreForecastRunIdMustComeFromCore":True,"coreProbabilisticForecastIdMustComeFromCore":True,"coreRequests":reqs,"requestCount":len(reqs),"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False}
    out["planHash"]=content_hash(out);return out


def build_calibration_core_plan(request: CalibrationCorePlanRequest) -> Dict[str,Any]:
    r=dict(request.calibrationResult)
    if r.get("schema")!=CALIBRATION_SCHEMA: raise ValueError(f"calibrationResult.schema must be {CALIBRATION_SCHEMA}")
    mid=request.coreModelId; tid=request.coreTargetId
    study_id=_bounded(request.coreCalibrationStudyId,255)
    study={"target_id":tid,"study_key":f"workbench-{r.get('resultHash','')[:16]}","assessment_kind":"reliability","scope":{"sample_count":r.get("sampleCount")},"expected_calibration":{"relationship":"forecast-probability-equals-observed-frequency"},"status":"recorded","provenance":{"source_product":"workbench","workbench_version":VERSION,"workbench_result_hash":r.get("resultHash")}}
    reqs=[_core_request(CORE_PATHS["calibrationStudies"].format(model_id=mid),study,"create-calibration-study")]
    if study_id:
        for b in r.get("bins",[]): reqs.append(_core_request(CORE_PATHS["calibrationBins"].format(model_id=mid,study_id=study_id),dict(b),"register-calibration-bin"))
        for name,val in r.get("metrics",{}).items():
            reqs.append(_core_request(CORE_PATHS["probabilisticEvaluations"].format(model_id=mid),{"calibration_study_id":study_id,"probabilistic_forecast_id":request.coreProbabilisticForecastId or None,"evaluation_key":f"workbench-{name}","metric_family":"proper-scoring-rule" if name in {"brier","logLoss"} else "calibration","metric_name":name,"metric_value":val,"evidence_ref":f"workbench:calibration:{r.get('resultHash')}","provenance":{"source_product":"workbench","workbench_version":VERSION}},"register-calibration-evaluation"))
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"calibration-evidence-registration","coreModelId":mid,"coreTargetId":tid,"coreCalibrationStudyIdMustComeFromCore":not bool(study_id),"coreRequests":reqs,"requestCount":len(reqs),"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False}
    out["planHash"]=content_hash(out);return out


def build_visual_predictive_plan(request: VisualPredictivePlanRequest) -> Dict[str,Any]:
    r=_require_forecast(dict(request.forecastResult)); cid=request.coreCompositionId; wid=_bounded(request.coreWorkspaceId,255)
    prov={"source_product":"workbench","workbench_version":VERSION,"workbench_result_hash":r.get("resultHash")}
    workspace={"workspace_key":"workbench-predictive","name":f"{r.get('modelName')} Predictive Workspace","purpose":"Visualize Workbench-generated forecasts and uncertainty evidence.","status":"draft","visibility":"private","settings":{"renderer_neutral":True,"source_product":"workbench"},"provenance":prov,"metadata":{"forecastMethod":r.get("method")}}
    reqs=[_core_request(CORE_PATHS["visualWorkspaces"].format(composition_id=cid),workspace,"create-visual-predictive-workspace")]
    if wid:
        if request.coreForecastRunId or request.coreProbabilisticForecastId:
            reqs.append(_core_request(CORE_PATHS["visualForecastOverlays"].format(workspace_id=wid),{"overlay_key":"workbench-forecast","forecast_run_id":request.coreForecastRunId or None,"probabilistic_forecast_id":request.coreProbabilisticForecastId or None,"ensemble_forecast_id":None,"target_view_ids":request.targetViewIds,"display_contract":{"kind":"forecast-band","renderer_neutral":True},"provenance":prov},"create-forecast-overlay"))
        if request.coreProbabilisticForecastId or request.coreCalibrationStudyId:
            reqs.append(_core_request(CORE_PATHS["visualUncertaintyDisplays"].format(workspace_id=wid),{"display_key":"workbench-uncertainty","probabilistic_forecast_id":request.coreProbabilisticForecastId or None,"calibration_study_id":request.coreCalibrationStudyId or None,"display_kind":"interval-band","interval_levels":[r.get("intervalLevel")],"quantiles":[],"target_view_ids":request.targetViewIds,"display_contract":{"renderer_neutral":True},"provenance":prov},"create-uncertainty-display"))
    out={"ok":True,"schema":SCHEMA,"version":VERSION,"phase":"visual-predictive-registration","coreCompositionId":cid,"coreWorkspaceIdMustComeFromCore":not bool(wid),"coreRequests":reqs,"requestCount":len(reqs),"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"visualRenderingByCore":False}
    out["planHash"]=content_hash(out);return out


@router.get("/integration/core/predictive-intelligence/manifest")
def manifest(x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token);return predictive_manifest()

@router.post("/predictive/forecast")
def forecast(request: ForecastRequest) -> Dict[str,Any]:
    try:return execute_forecast(request)
    except Exception as exc:raise _bad(exc)

@router.post("/predictive/backtest")
def backtest(request: BacktestRequest) -> Dict[str,Any]:
    try:return execute_backtest(request)
    except Exception as exc:raise _bad(exc)

@router.post("/predictive/calibration")
def calibration(request: CalibrationRequest) -> Dict[str,Any]:
    try:return execute_calibration(request)
    except Exception as exc:raise _bad(exc)

@router.post("/integration/core/predictive-intelligence/model/plan")
def model_plan(request: ModelPlanRequest,x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_model_plan(request)
    except Exception as exc:raise _bad(exc)

@router.post("/integration/core/predictive-intelligence/forecast/plan")
def forecast_plan(request: ForecastCorePlanRequest,x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_forecast_core_plan(request)
    except Exception as exc:raise _bad(exc)

@router.post("/integration/core/predictive-intelligence/calibration/plan")
def calibration_plan(request: CalibrationCorePlanRequest,x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_calibration_core_plan(request)
    except Exception as exc:raise _bad(exc)

@router.post("/integration/core/predictive-intelligence/visual/plan")
def visual_plan(request: VisualPredictivePlanRequest,x_sc_service_token: str | None = Header(default=None, alias="X-SC-Service-Token")) -> Dict[str,Any]:
    _authorize_core_route(x_sc_service_token)
    try:return build_visual_predictive_plan(request)
    except Exception as exc:raise _bad(exc)

@router.get("/v6100/status")
def status() -> Dict[str,Any]:
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":"Predictive Intelligence Runtime Integration","corePredictiveModelContract":CORE_PREDICTIVE_MODEL_CONTRACT,"coreProbabilisticForecastContract":CORE_PROBABILISTIC_FORECAST_CONTRACT,"coreCalibrationContract":CORE_CALIBRATION_CONTRACT,"coreVisualPredictiveContract":CORE_VISUAL_PREDICTIVE_CONTRACT,"pointForecasting":True,"probabilisticIntervals":True,"rollingOriginBacktesting":True,"calibrationMetrics":True,"v670LineageIntegration":True,"v690VisualPredictiveIntegration":True,"coreIssuedPredictiveIdsRequired":True,"automaticCoreDispatch":False,"automaticCorePersistence":False,"coreExecutesPredictiveModels":False}

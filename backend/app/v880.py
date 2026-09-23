"""Workbench v8.8.0 — Comparative Experiment & Model Analysis.

Neutral, provenance-preserving comparison over completed Workbench execution jobs.
The engine extracts comparable scalar inputs/outputs, reports structural differences,
and computes transparent pairwise deltas where both sides contain finite numeric values.
It never ranks experiments, selects a winner, infers scientific validity, or mutates the
underlying jobs/results. Platform Core integration remains explicit and plan-only.
"""
from __future__ import annotations

import math
from itertools import combinations
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v660 import CORE_PATHS, CORE_UNIFIED_RUNTIME_CONTRACT
from .v820 import ProjectCorePlanRequest, core_project_plan, load_project
from .v840 import _load_job, list_jobs

VERSION = APP_VERSION
SCHEMA = "sc-workbench-comparative-experiment-model-analysis/1.0"
COMPARISON_SCHEMA = "sc-workbench-comparative-experiment-model-comparison/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-comparative-experiment-model-core-plan/1.0"
MAX_JOBS = 20
MAX_METRICS = 250
MAX_DEPTH = 6
router = APIRouter(tags=["workbench-v880-comparative-experiment-model-analysis"])


class ComparisonRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    jobIds: List[str] = Field(min_length=2, max_length=MAX_JOBS)
    baselineJobId: str = Field(default="", max_length=255)
    includeRequestMetrics: bool = True
    includeResultMetrics: bool = True
    includePairwiseDeltas: bool = True

    @model_validator(mode="after")
    def validate_jobs(self):
        ids=[str(x).strip() for x in self.jobIds if str(x).strip()]
        if len(ids) != len(set(ids)):
            raise ValueError("jobIds must be unique")
        if len(ids) < 2:
            raise ValueError("at least two unique jobIds are required")
        if self.baselineJobId and self.baselineJobId not in ids:
            raise ValueError("baselineJobId must be included in jobIds")
        self.jobIds=ids
        return self


class CoreComparisonPlanRequest(ComparisonRequest):
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private","internal","public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def _finite_number(value: Any) -> Optional[float]:
    if isinstance(value, bool): return None
    if isinstance(value, (int,float)):
        v=float(value)
        return v if math.isfinite(v) else None
    return None


def _flatten_numbers(value: Any, prefix: str = "", depth: int = 0, out: Optional[Dict[str,float]] = None) -> Dict[str,float]:
    out = out if out is not None else {}
    if len(out) >= MAX_METRICS or depth > MAX_DEPTH: return out
    n=_finite_number(value)
    if n is not None:
        if prefix: out[prefix]=n
        return out
    if isinstance(value, dict):
        for key in sorted(value):
            if len(out) >= MAX_METRICS: break
            k=str(key).strip().replace(".","_")[:80]
            _flatten_numbers(value[key], f"{prefix}.{k}" if prefix else k, depth+1, out)
    elif isinstance(value, list):
        # only index short vectors; large arrays are summarized to avoid misleading element-wise comparison
        if len(value) <= 16:
            for i,item in enumerate(value):
                if len(out) >= MAX_METRICS: break
                _flatten_numbers(item, f"{prefix}[{i}]" if prefix else f"[{i}]", depth+1, out)
        numeric=[_finite_number(x) for x in value]
        numeric=[x for x in numeric if x is not None]
        if prefix and numeric:
            out.setdefault(prefix+".__count", float(len(numeric)))
            out.setdefault(prefix+".__min", min(numeric))
            out.setdefault(prefix+".__max", max(numeric))
            out.setdefault(prefix+".__mean", sum(numeric)/len(numeric))
    return out


def _job_record(job: Dict[str,Any], req: ComparisonRequest) -> Dict[str,Any]:
    request_metrics=_flatten_numbers(job.get("request") or {}, "request") if req.includeRequestMetrics else {}
    result_metrics=_flatten_numbers(job.get("result") or {}, "result") if req.includeResultMetrics else {}
    return {
        "jobId": job.get("jobId"), "label": job.get("label"), "runtimeKind": job.get("runtimeKind"),
        "status": job.get("status"), "jobRevision": job.get("jobRevision"),
        "requestHash": job.get("requestHash"), "resultHash": job.get("resultHash"), "jobHash": job.get("jobHash"),
        "createdAt": job.get("createdAt"), "startedAt": job.get("startedAt"), "completedAt": job.get("completedAt"),
        "tags": job.get("tags") or [], "requestMetrics": request_metrics, "resultMetrics": result_metrics,
        "requestMetricCount": len(request_metrics), "resultMetricCount": len(result_metrics),
    }


def _metric_matrix(records: List[Dict[str,Any]], field: str) -> Dict[str,Any]:
    keys=sorted(set().union(*(set(r[field].keys()) for r in records)))[:MAX_METRICS]
    rows=[]
    for key in keys:
        vals={r["jobId"]: r[field].get(key) for r in records}
        present=[v for v in vals.values() if v is not None]
        rows.append({"metric":key,"values":vals,"presentCount":len(present),"comparableAcrossAll":len(present)==len(records)})
    return {"metricCount":len(rows),"rows":rows,"fullyComparableMetricCount":sum(1 for x in rows if x["comparableAcrossAll"])}


def _pairwise(records: List[Dict[str,Any]], baseline: str = "") -> List[Dict[str,Any]]:
    by={r["jobId"]:r for r in records}; pairs=[]
    combos=((baseline,b) for b in by if b!=baseline) if baseline else combinations(by,2)
    for left_id,right_id in combos:
        left,right=by[left_id],by[right_id]
        metrics={}
        for scope in ("requestMetrics","resultMetrics"):
            common=sorted(set(left[scope]).intersection(right[scope]))
            deltas=[]
            for key in common[:MAX_METRICS]:
                a,b=left[scope][key],right[scope][key]
                delta=b-a
                pct=None if a==0 else (delta/abs(a))*100.0
                deltas.append({"metric":key,"left":a,"right":b,"deltaRightMinusLeft":delta,"percentDeltaFromLeft":pct})
            metrics[scope]={"commonMetricCount":len(common),"deltas":deltas}
        pairs.append({
            "leftJobId":left_id,"rightJobId":right_id,
            "sameRuntimeKind":left.get("runtimeKind")==right.get("runtimeKind"),
            "sameRequestHash":left.get("requestHash")==right.get("requestHash"),
            "sameResultHash":left.get("resultHash")==right.get("resultHash"),
            "metrics":metrics,
            "winnerSelected":False,"scientificValidityInferred":False,
        })
    return pairs


def compare(req: ComparisonRequest) -> Dict[str,Any]:
    load_project(req.projectKey)  # project existence + authoritative scope check
    jobs=[]
    for jid in req.jobIds:
        try: job=_load_job(jid)
        except FileNotFoundError as exc: raise FileNotFoundError(str(exc)) from exc
        except ValueError as exc: raise ValueError(str(exc)) from exc
        if job.get("projectKey") != req.projectKey: raise ValueError(f"job {jid} belongs to another project")
        if job.get("status") != "completed": raise RuntimeError(f"job {jid} is not completed")
        jobs.append(job)
    records=[_job_record(j,req) for j in jobs]
    out={
        "ok":True,"schema":COMPARISON_SCHEMA,"version":VERSION,"projectKey":req.projectKey,
        "comparisonMode":"baseline" if req.baselineJobId else "all-pairs","baselineJobId":req.baselineJobId or None,
        "jobCount":len(records),"jobs":records,
        "requestMetricMatrix":_metric_matrix(records,"requestMetrics") if req.includeRequestMetrics else {"metricCount":0,"rows":[],"fullyComparableMetricCount":0},
        "resultMetricMatrix":_metric_matrix(records,"resultMetrics") if req.includeResultMetrics else {"metricCount":0,"rows":[],"fullyComparableMetricCount":0},
        "pairwiseComparisons":_pairwise(records,req.baselineJobId) if req.includePairwiseDeltas else [],
        "structuralComparison":{
            "runtimeKinds":sorted({str(r.get('runtimeKind') or '') for r in records}),
            "requestHashes":sorted({str(r.get('requestHash') or '') for r in records}),
            "resultHashes":sorted({str(r.get('resultHash') or '') for r in records}),
            "allSameRuntimeKind":len({r.get('runtimeKind') for r in records})==1,
            "allSameRequest":len({r.get('requestHash') for r in records})==1,
            "allSameResult":len({r.get('resultHash') for r in records})==1,
        },
        "boundaries":{
            "comparisonMutatesJobs":False,"comparisonMutatesResults":False,"automaticWinnerSelectionPerformed":False,
            "scientificValidityInferred":False,"causalInferencePerformed":False,"statisticalSignificanceInferred":False,
            "automaticCoreDispatchPerformed":False,
        },
    }
    out["comparisonHash"]=content_hash(out)
    return out


def core_comparison_plan(req: CoreComparisonPlanRequest) -> Dict[str,Any]:
    result=compare(ComparisonRequest(**req.model_dump(include={"projectKey","jobIds","baselineJobId","includeRequestMetrics","includeResultMetrics","includePairwiseDeltas"})))
    project=load_project(req.projectKey); ws=project["workspace"]
    sid=str(req.coreSessionId or ws.get("coreSessionId") or "").strip()[:255]
    base=core_project_plan(ProjectCorePlanRequest(projectKey=req.projectKey,coreProjectEntityId=req.coreProjectEntityId or req.projectKey,coreSessionId=sid,visibility=req.visibility,createdBy=req.createdBy))
    out={
        "ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"phase":base.get("phase"),
        "coreSessionId":sid or None,"coreSessionIdMustComeFromCore":True,"coreUnifiedResearchContract":CORE_UNIFIED_RUNTIME_CONTRACT,
        "projectPlan":base,"comparisonHash":result["comparisonHash"],"jobIds":req.jobIds,"coreRequests":list(base.get("coreRequests") or []),
        "comparisonBindingIsAnalyticalViewOnly":True,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,
        "automaticWinnerSelectionAuthorized":False,"scientificValidityInferenceAuthorized":False,
    }
    if sid:
        out["coreRequests"].append({
            "path":CORE_PATHS["objectBindings"],"method":"POST","phase":"comparative-analysis-bind","data":{
                "session_id":sid,"object_type":"workbench.comparative-experiment-model-analysis",
                "object_ref":f"sc://workbench/comparisons/{req.projectKey}/{result['comparisonHash'][:24]}",
                "version_ref":f"sc://workbench/comparisons/{req.projectKey}@{VERSION}","content_hash":result["comparisonHash"],
                "role":"analytical-view","visibility":req.visibility,
                "metadata":{"workbenchVersion":VERSION,"projectKey":req.projectKey,"jobIds":req.jobIds,"scientificSourceOfTruth":False,"winnerSelected":False},
            },"dispatchPerformed":False,
        })
    out["planHash"]=content_hash(out); return out


def manifest() -> Dict[str,Any]:
    out={
        "ok":True,"schema":SCHEMA,"version":VERSION,"release":"Comparative Experiment & Model Analysis",
        "capabilities":{"completedRunComparison":True,"requestMetricExtraction":True,"resultMetricExtraction":True,"metricMatrices":True,"pairwiseNumericDeltas":True,"baselineComparison":True,"structuralComparison":True,"provenancePreservation":True,"coreComparisonPlanning":True},
        "authorities":{"projects":"v8.2","executionsAndResults":"v8.4","linkedViews":"v8.7"},
        "boundaries":{"comparisonIsScientificSourceOfTruth":False,"automaticWinnerSelectionAuthorized":False,"scientificValidityInferenceAuthorized":False,"causalInferenceAuthorized":False,"statisticalSignificanceInferenceAuthorized":False,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False},
    }
    out["manifestHash"]=content_hash(out); return out


@router.get("/comparative-analysis/manifest")
def manifest_route(): return manifest()

@router.get("/comparative-analysis/jobs/{project_key}")
def jobs_route(project_key: str): return list_jobs(project_key=project_key,status="completed")

@router.post("/comparative-analysis/compare")
def compare_route(req: ComparisonRequest):
    try: return compare(req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc

@router.post("/integration/core/comparative-analysis/plan")
def core_plan_route(req: CoreComparisonPlanRequest, x_sc_service_token: Optional[str]=Header(default=None,alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    try: return core_comparison_plan(req)
    except FileNotFoundError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=409,detail=str(exc)) from exc

@router.get("/v880/status")
def status_route():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":"Comparative Experiment & Model Analysis","completedRunComparison":True,"pairwiseNumericDeltas":True,"baselineComparison":True,"automaticWinnerSelection":False,"scientificValidityInference":False,"automaticCoreDispatch":False}

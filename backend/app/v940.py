"""Workbench v9.4.0 — Uncertainty & Sensitivity Study Composer.

Researcher-authored uncertainty models and deterministic sampling plans plus
neutral sensitivity diagnostics over completed computational campaigns.
Supports Monte Carlo, Latin hypercube, and Sobol sampling; uniform, normal,
lognormal, triangular, and discrete inputs; descriptive output uncertainty;
and Pearson, Spearman, and standardized-regression sensitivity statistics.

The composer does not infer causal importance, rank a preferred parameter,
choose uncertainty distributions, declare convergence, or dispatch work.
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
from scipy import stats
from scipy.stats import qmc

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v820 import load_project
from .v840 import _load_job
from .v920 import _load_state, list_campaigns, load_campaign
from .v930 import _finite_float, _nested_get

VERSION = APP_VERSION
SCHEMA = "sc-workbench-uncertainty-sensitivity-study-composer/1.0"
STUDY_SCHEMA = "sc-workbench-uncertainty-sensitivity-study/1.0"
SENSITIVITY_SCHEMA = "sc-workbench-sensitivity-analysis/1.0"
CATALOG_SCHEMA = "sc-workbench-uncertainty-sensitivity-source-catalog/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-uncertainty-sensitivity-core-plan/1.0"
router = APIRouter(tags=["workbench-v940-uncertainty-sensitivity-study-composer"])

MAX_INPUTS = 32
MAX_SAMPLES = 10000
SamplingMethod = Literal["monte-carlo", "latin-hypercube", "sobol"]
SensitivityMethod = Literal["pearson", "spearman", "standardized-regression"]
Distribution = Literal["uniform", "normal", "lognormal", "triangular", "discrete"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _study_dir(project_key: str) -> Path:
    return _store_root() / "uncertainty-sensitivity-studies" / _stable_id(project_key)


def _study_path(project_key: str, study_hash: str) -> Path:
    return _study_dir(project_key) / f"{study_hash}.json"


class UncertainInput(BaseModel):
    path: str = Field(min_length=1, max_length=240)
    label: str = Field(default="", max_length=500)
    distribution: Distribution
    minimum: float | None = None
    maximum: float | None = None
    mean: float | None = None
    stdDev: float | None = Field(default=None, gt=0)
    mode: float | None = None
    values: List[Any] = Field(default_factory=list, max_length=200)

    @model_validator(mode="after")
    def validate_distribution(self):
        self.path = self.path.strip(); self.label = self.label.strip()
        if self.distribution == "uniform":
            if self.minimum is None or self.maximum is None or not self.minimum < self.maximum:
                raise ValueError("uniform requires minimum < maximum")
        elif self.distribution in {"normal", "lognormal"}:
            if self.mean is None or self.stdDev is None:
                raise ValueError(f"{self.distribution} requires mean and stdDev")
        elif self.distribution == "triangular":
            if None in (self.minimum, self.mode, self.maximum) or not self.minimum <= self.mode <= self.maximum or self.minimum == self.maximum:
                raise ValueError("triangular requires minimum <= mode <= maximum and minimum < maximum")
        elif self.distribution == "discrete":
            if not self.values:
                raise ValueError("discrete requires values")
        return self


class UncertaintyStudyRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    studyKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    campaignHash: str = Field(default="", max_length=64)
    samplingMethod: SamplingMethod = "monte-carlo"
    sampleCount: int = Field(default=1000, ge=2, le=MAX_SAMPLES)
    seed: int = Field(default=20260925, ge=0, le=2**32-1)
    uncertainInputs: List[UncertainInput] = Field(min_length=1, max_length=MAX_INPUTS)
    confidenceLevel: float = Field(default=0.95, gt=0.5, lt=1.0)
    assumptions: List[str] = Field(default_factory=list, max_length=200)
    notes: str = Field(default="", max_length=12000)

    @model_validator(mode="after")
    def validate_study(self):
        self.projectKey=self.projectKey.strip(); self.studyKey=self.studyKey.strip(); self.title=self.title.strip()
        paths=[x.path for x in self.uncertainInputs]
        if len(paths) != len(set(paths)): raise ValueError("uncertain input paths must be unique")
        if self.campaignHash and len(self.campaignHash) != 64: raise ValueError("campaignHash must be a 64-character content hash")
        return self


class SaveUncertaintyStudyRequest(UncertaintyStudyRequest):
    createdBy: str = Field(default="workbench", max_length=160)
    recordLabel: str = Field(default="Uncertainty & sensitivity study", max_length=500)


class SensitivityAnalysisRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    campaignHash: str = Field(min_length=64, max_length=64)
    resultMetricPath: str = Field(min_length=1, max_length=300)
    parameterPaths: List[str] = Field(min_length=1, max_length=MAX_INPUTS)
    methods: List[SensitivityMethod] = Field(default_factory=lambda:["pearson","spearman"], min_length=1, max_length=3)
    confidenceLevel: float = Field(default=0.95, gt=0.5, lt=1.0)

    @model_validator(mode="after")
    def validate_paths(self):
        self.parameterPaths=[x.strip() for x in self.parameterPaths if x.strip()]
        if len(self.parameterPaths) != len(set(self.parameterPaths)): raise ValueError("parameterPaths must be unique")
        self.methods=list(dict.fromkeys(self.methods))
        return self


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    studyHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private","internal","public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)


def manifest() -> Dict[str, Any]:
    out={
        "ok":True,"schema":SCHEMA,"version":VERSION,"release":"Uncertainty & Sensitivity Study Composer",
        "product":PRODUCT_KEY,"runtime":RUNTIME_KIND,
        "samplingMethods":["monte-carlo","latin-hypercube","sobol"],
        "distributions":["uniform","normal","lognormal","triangular","discrete"],
        "sensitivityMethods":["pearson","spearman","standardized-regression"],
        "capabilities":{
            "researcherAuthoredUncertaintyModels":True,"deterministicSamplingPlans":True,
            "monteCarloSampling":True,"latinHypercubeSampling":True,"sobolSampling":True,
            "distributionTransforms":True,"campaignResultSensitivityAnalysis":True,
            "outputUncertaintySummaries":True,"correlationSensitivity":True,
            "standardizedRegressionSensitivity":True,"contentAddressedStudies":True,
            "provenancePreservation":True,"platformCoreUncertaintyPlanning":True,
        },
        "boundaries":{
            "automaticDistributionSelection":False,"automaticParameterImportanceRanking":False,
            "automaticCausalImportanceInference":False,"automaticConvergenceDeclaration":False,
            "automaticScientificValidityInference":False,"automaticModelSelection":False,
            "automaticJobExecution":False,"automaticCoreDispatch":False,"platformCoreGovernanceReplaced":False,
        },
    }
    out["manifestHash"]=content_hash(out); return out


def _unit_matrix(req: UncertaintyStudyRequest) -> np.ndarray:
    d=len(req.uncertainInputs); n=req.sampleCount
    if req.samplingMethod == "monte-carlo":
        return np.random.default_rng(req.seed).random((n,d))
    if req.samplingMethod == "latin-hypercube":
        return qmc.LatinHypercube(d=d, seed=req.seed).random(n=n)
    # Sobol supports arbitrary n via random(); deterministic scrambling prevents zero/one endpoints.
    return qmc.Sobol(d=d, scramble=True, seed=req.seed).random(n=n)


def _transform(u: np.ndarray, spec: UncertainInput) -> List[Any]:
    eps=np.finfo(float).eps; u=np.clip(u,eps,1-eps)
    if spec.distribution == "uniform": return (spec.minimum + u*(spec.maximum-spec.minimum)).tolist()
    if spec.distribution == "normal": return stats.norm.ppf(u,loc=spec.mean,scale=spec.stdDev).tolist()
    if spec.distribution == "lognormal": return np.exp(stats.norm.ppf(u,loc=spec.mean,scale=spec.stdDev)).tolist()
    if spec.distribution == "triangular":
        c=(spec.mode-spec.minimum)/(spec.maximum-spec.minimum)
        return stats.triang.ppf(u,c=c,loc=spec.minimum,scale=spec.maximum-spec.minimum).tolist()
    vals=spec.values; idx=np.minimum((u*len(vals)).astype(int),len(vals)-1); return [vals[int(i)] for i in idx]


def compose_study(req: UncertaintyStudyRequest) -> Dict[str, Any]:
    load_project(req.projectKey)
    campaign=None
    if req.campaignHash: campaign=load_campaign(req.projectKey,req.campaignHash)
    unit=_unit_matrix(req); cols={}
    for j,spec in enumerate(req.uncertainInputs): cols[spec.path]=_transform(unit[:,j],spec)
    samples=[]
    for i in range(req.sampleCount):
        values={p:cols[p][i] for p in cols}; samples.append({"sampleIndex":i,"sampleId":content_hash({"studyKey":req.studyKey,"seed":req.seed,"index":i,"values":values}),"values":values})
    seed={"projectKey":req.projectKey,"studyKey":req.studyKey,"title":req.title,"campaignHash":req.campaignHash or None,"samplingMethod":req.samplingMethod,"sampleCount":req.sampleCount,"seed":req.seed,"uncertainInputs":[x.model_dump() for x in req.uncertainInputs],"confidenceLevel":req.confidenceLevel,"assumptions":req.assumptions,"notes":req.notes,"sampleManifestHash":content_hash(samples)}
    out={"ok":True,"schema":STUDY_SCHEMA,"version":VERSION,**seed,"samples":samples,"campaignRef":campaign.get("campaignRef") if campaign else None,"boundaries":manifest()["boundaries"]}
    out["studyHash"]=content_hash(seed); out["studyRef"]=f"sc://workbench/uncertainty-sensitivity-study/{req.projectKey}/{out['studyHash']}"; return out


def save_study(req: SaveUncertaintyStudyRequest) -> Dict[str, Any]:
    fields=set(UncertaintyStudyRequest.model_fields); result=compose_study(UncertaintyStudyRequest(**req.model_dump(include=fields)))
    rec={**result,"createdBy":req.createdBy,"recordLabel":req.recordLabel,"createdAt":_now()}
    rec["recordHash"]=content_hash({k:v for k,v in rec.items() if k not in {"createdAt","recordHash","idempotent"}})
    path=_study_path(req.projectKey,result["studyHash"])
    if path.exists():
        old=_json_read(path); expected=content_hash({k:v for k,v in old.items() if k not in {"createdAt","recordHash","idempotent"}})
        if old.get("recordHash") != expected: raise ValueError("stored uncertainty study failed integrity validation")
        old["idempotent"]=True; return old
    path.parent.mkdir(parents=True,exist_ok=True); _atomic_json_write(path,rec); rec["idempotent"]=False; return rec


def load_study(project_key:str, study_hash:str)->Dict[str,Any]:
    load_project(project_key); path=_study_path(project_key,study_hash)
    if not path.exists(): raise FileNotFoundError("uncertainty study not found")
    rec=_json_read(path)
    if rec.get("projectKey") != project_key or rec.get("studyHash") != study_hash: raise ValueError("uncertainty study identity mismatch")
    expected=content_hash({k:v for k,v in rec.items() if k not in {"createdAt","recordHash","idempotent"}})
    if rec.get("recordHash") != expected: raise ValueError("uncertainty study failed integrity validation")
    return rec


def list_studies(project_key:str)->Dict[str,Any]:
    load_project(project_key); rows=[]; root=_study_dir(project_key)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r=_json_read(p)
                if r.get("projectKey")==project_key: rows.append({k:r.get(k) for k in ("studyHash","studyRef","studyKey","title","campaignHash","samplingMethod","sampleCount","createdBy","createdAt","recordHash")})
            except Exception: pass
    rows.sort(key=lambda x:str(x.get("createdAt") or ""),reverse=True)
    return {"ok":True,"schema":STUDY_SCHEMA,"version":VERSION,"projectKey":project_key,"studyCount":len(rows),"studies":rows}


def _campaign_rows(req:SensitivityAnalysisRequest):
    campaign=load_campaign(req.projectKey,req.campaignHash); state=_load_state(req.projectKey,req.campaignHash)
    rows=[]; excluded=[]
    for item in state.get("jobs", {}).values():
        jid=item.get("jobId")
        if not jid: continue
        try: job=_load_job(jid)
        except Exception: continue
        if job.get("status") != "completed": continue
        try: y=_finite_float(_nested_get(job.get("result") or {},req.resultMetricPath))
        except KeyError: y=None
        params=(job.get("metadata") or {}).get("parameterValues") or {}
        vals={}; good=y is not None
        for path in req.parameterPaths:
            try: v=_finite_float(_nested_get(params,path))
            except KeyError: v=_finite_float(params.get(path))
            vals[path]=v; good=good and v is not None
        if good: rows.append({"jobId":jid,"result":y,"parameters":vals,"resultHash":job.get("resultHash")})
        else: excluded.append({"jobId":jid,"reason":"missing-or-nonnumeric-result-or-parameter"})
    return campaign,state,rows,excluded


def analyze_sensitivity(req:SensitivityAnalysisRequest)->Dict[str,Any]:
    load_project(req.projectKey); campaign,state,rows,excluded=_campaign_rows(req)
    if len(rows) < 3: raise ValueError("at least 3 complete numeric observations are required")
    y=np.array([r["result"] for r in rows],dtype=float); alpha=1-req.confidenceLevel
    output={"count":len(y),"mean":float(np.mean(y)),"stdDev":float(np.std(y,ddof=1)) if len(y)>1 else 0.0,"min":float(np.min(y)),"max":float(np.max(y)),"quantiles":{"lower":float(np.quantile(y,alpha/2)),"median":float(np.quantile(y,0.5)),"upper":float(np.quantile(y,1-alpha/2))}}
    results={}
    if "pearson" in req.methods:
        results["pearson"]={p:{"coefficient":float(stats.pearsonr([r['parameters'][p] for r in rows],y).statistic),"pValue":float(stats.pearsonr([r['parameters'][p] for r in rows],y).pvalue),"importanceRankGenerated":False,"causalImportanceInferred":False} for p in req.parameterPaths}
    if "spearman" in req.methods:
        results["spearman"]={p:{"coefficient":float(stats.spearmanr([r['parameters'][p] for r in rows],y).statistic),"pValue":float(stats.spearmanr([r['parameters'][p] for r in rows],y).pvalue),"importanceRankGenerated":False,"causalImportanceInferred":False} for p in req.parameterPaths}
    if "standardized-regression" in req.methods:
        X=np.array([[r["parameters"][p] for p in req.parameterPaths] for r in rows],dtype=float); sx=X.std(axis=0,ddof=1); sy=y.std(ddof=1)
        if np.any(sx==0) or sy==0: raise ValueError("standardized regression requires non-zero variance in all parameters and result")
        Xz=(X-X.mean(axis=0))/sx; yz=(y-y.mean())/sy; beta=np.linalg.lstsq(np.column_stack([np.ones(len(Xz)),Xz]),yz,rcond=None)[0][1:]
        pred=Xz@beta; ss_res=float(np.sum((yz-pred)**2)); ss_tot=float(np.sum((yz-yz.mean())**2)); r2=1-ss_res/ss_tot if ss_tot else None
        results["standardized-regression"]={"coefficients":{p:float(beta[i]) for i,p in enumerate(req.parameterPaths)},"rSquared":r2,"importanceRankGenerated":False,"causalImportanceInferred":False,"modelValidityInferred":False}
    seed={"projectKey":req.projectKey,"campaignHash":req.campaignHash,"resultMetricPath":req.resultMetricPath,"parameterPaths":req.parameterPaths,"methods":req.methods,"confidenceLevel":req.confidenceLevel,"campaignStateHash":state.get("stateHash"),"results":results,"outputUncertainty":output}
    out={"ok":True,"schema":SENSITIVITY_SCHEMA,"version":VERSION,**seed,"observationCount":len(rows),"excludedObservationCount":len(excluded),"excludedObservations":excluded,"provenance":{"campaignRef":campaign.get("campaignRef"),"resultHashes":{r['jobId']:r.get('resultHash') for r in rows}},"boundaries":manifest()["boundaries"]}; out["analysisHash"]=content_hash(seed); return out


def source_catalog(project_key:str)->Dict[str,Any]:
    load_project(project_key); c=list_campaigns(project_key); s=list_studies(project_key)
    out={"ok":True,"schema":CATALOG_SCHEMA,"version":VERSION,"projectKey":project_key,"campaignCount":c.get("campaignCount",0),"campaigns":c.get("campaigns",[]),"studyCount":s.get("studyCount",0),"studies":s.get("studies",[]),"boundaries":{"catalogExecutesJobs":False,"catalogRunsSensitivityAnalysis":False,"catalogInfersValidity":False}}; out["catalogHash"]=content_hash(out); return out


def core_plan(req:CorePlanRequest)->Dict[str,Any]:
    study=load_study(req.projectKey,req.studyHash); cfg=core_config()
    out={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"studyHash":req.studyHash,"studyRef":study.get("studyRef"),"coreProjectEntityId":req.coreProjectEntityId or req.projectKey,"coreSessionId":req.coreSessionId,"visibility":req.visibility,"createdBy":req.createdBy,"coreEnabled":bool(cfg.get("enabled")),"coreTarget":cfg.get("baseUrl") or "","bindingPlan":{"objectType":"workbench.uncertainty-sensitivity-study","objectRef":study.get("studyRef"),"objectHash":req.studyHash,"campaignHash":study.get("campaignHash"),"samplingMethod":study.get("samplingMethod"),"sampleManifestHash":study.get("sampleManifestHash"),"role":"uncertainty-sensitivity-plan"},"boundaries":{"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"coreGovernanceAuthorityPreserved":True,"scientificValidityInferred":False,"causalImportanceInferred":False}}; out["planHash"]=content_hash(out); return out


def _wrap(fn,*args):
    try: return fn(*args)
    except FileNotFoundError as exc: raise HTTPException(status_code=404,detail=str(exc)) from exc
    except (ValueError,RuntimeError) as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc

@router.get("/uncertainty-sensitivity/manifest")
def route_manifest(): return manifest()
@router.get("/uncertainty-sensitivity/source-catalog/{project_key}")
def route_catalog(project_key:str): return _wrap(source_catalog,project_key)
@router.post("/uncertainty-sensitivity/compose")
def route_compose(req:UncertaintyStudyRequest): return _wrap(compose_study,req)
@router.post("/uncertainty-sensitivity/studies")
def route_save(req:SaveUncertaintyStudyRequest): return _wrap(save_study,req)
@router.get("/uncertainty-sensitivity/studies/{project_key}")
def route_list(project_key:str): return _wrap(list_studies,project_key)
@router.get("/uncertainty-sensitivity/studies/{project_key}/{study_hash}")
def route_get(project_key:str,study_hash:str): return _wrap(load_study,project_key,study_hash)
@router.post("/uncertainty-sensitivity/analyze")
def route_analyze(req:SensitivityAnalysisRequest): return _wrap(analyze_sensitivity,req)
@router.post("/integration/core/uncertainty-sensitivity/plan")
def route_core(req:CorePlanRequest): return _wrap(core_plan,req)
@router.get("/v940/status")
def status():
    m=manifest(); return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":m["release"],"uncertaintySensitivityStudyComposer":True,"monteCarloSampling":True,"latinHypercubeSampling":True,"sobolSampling":True,"campaignSensitivityAnalysis":True,"automaticParameterImportanceRanking":False,"automaticCausalImportanceInference":False,"automaticCoreDispatch":False,"manifestHash":m["manifestHash"]}

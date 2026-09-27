"""Workbench v10.3.0 — AI Evaluation & Benchmark Workspace.

Registry-backed, content-addressed benchmark suites and immutable evaluation results for
Sustainable Catalyst Workbench. The workspace defines researcher-authored metrics, evaluation
datasets, diagnostic slices, reproducibility settings, explicit execution plans, model/run
result records, baseline-relative regression diagnostics, and Platform Core handoff plans.

v10.3.0 intentionally does not execute inference automatically, download models or datasets,
select a preferred model, collapse metrics into an automatic winner, infer scientific validity,
interpret causal meaning, approve production deployment, or create governed Platform Core
objects automatically.
"""
from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import core_config
from .v810 import _atomic_json_write, _json_read, _store_root
from .v1010 import _load_record as load_registry_record
from .v1020 import _load_training_result

VERSION = APP_VERSION
SCHEMA = "sc-workbench-ai-evaluation-benchmark-workspace/1.0"
BENCHMARK_SCHEMA = "sc-workbench-ai-benchmark-suite/1.0"
RESULT_SCHEMA = "sc-workbench-ai-evaluation-result/1.0"
EXECUTION_PLAN_SCHEMA = "sc-workbench-ai-evaluation-execution-plan/1.0"
COMPARISON_SCHEMA = "sc-workbench-ai-evaluation-comparison/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-ai-evaluation-core-plan/1.0"
router = APIRouter(tags=["workbench-v1030-ai-evaluation-benchmark-workspace"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
MetricDirection = Literal["higher-is-better", "lower-is-better", "report-only"]
MetricKind = Literal[
    "accuracy", "precision", "recall", "f1", "auc", "mae", "mse", "rmse", "r2",
    "log-loss", "perplexity", "latency-ms", "throughput", "cost-usd", "custom"
]
SliceOperator = Literal["eq", "ne", "lt", "lte", "gt", "gte", "contains", "in", "custom"]
CoreEvaluationKind = Literal["benchmark-suite", "evaluation-result", "comparison"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


def _project_root(project_key: str) -> Path:
    return _store_root() / "ai-evaluation-benchmarks" / _stable_id(project_key)


def _benchmark_dir(project_key: str) -> Path:
    return _project_root(project_key) / "benchmarks"


def _benchmark_path(project_key: str, benchmark_hash: str) -> Path:
    return _benchmark_dir(project_key) / f"{benchmark_hash}.json"


def _result_dir(project_key: str, benchmark_hash: str) -> Path:
    return _project_root(project_key) / "results" / benchmark_hash


def _result_path(project_key: str, benchmark_hash: str, evaluation_hash: str) -> Path:
    return _result_dir(project_key, benchmark_hash) / f"{evaluation_hash}.json"


class BenchmarkMetric(BaseModel):
    metricKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    kind: MetricKind = "custom"
    direction: MetricDirection = "report-only"
    unit: str = Field(default="", max_length=80)
    regressionTolerance: float = Field(default=0.0, ge=0.0)
    targetValue: Optional[float] = None
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def normalize(self):
        self.metricKey = self.metricKey.strip()
        self.title = self.title.strip()
        self.unit = self.unit.strip()
        return self


class BenchmarkSlice(BaseModel):
    sliceKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    field: str = Field(min_length=1, max_length=240)
    operator: SliceOperator = "eq"
    value: Any = None
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def normalize(self):
        self.sliceKey = self.sliceKey.strip()
        self.title = self.title.strip()
        self.field = self.field.strip()
        return self


class BenchmarkReproducibility(BaseModel):
    seed: int = Field(default=0, ge=0, le=2**31 - 1)
    repeats: int = Field(default=1, ge=1, le=10000)
    environmentRef: str = Field(default="", max_length=1000)
    dependencyLockHash: str = Field(default="", max_length=64)
    deterministicRequested: bool = True
    networkAccessAllowed: bool = False

    @model_validator(mode="after")
    def validate_hash(self):
        self.environmentRef = self.environmentRef.strip()
        self.dependencyLockHash = self.dependencyLockHash.strip().lower()
        if self.dependencyLockHash and not _is_hash(self.dependencyLockHash):
            raise ValueError("dependencyLockHash must be a SHA-256 hash")
        return self


class BenchmarkSuiteRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    benchmarkKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    task: str = Field(min_length=1, max_length=160)
    datasetRecordHashes: List[str] = Field(min_length=1, max_length=100)
    metrics: List[BenchmarkMetric] = Field(min_length=1, max_length=100)
    slices: List[BenchmarkSlice] = Field(default_factory=list, max_length=100)
    baselineModelRecordHash: str = Field(default="", max_length=64)
    reproducibility: BenchmarkReproducibility = Field(default_factory=BenchmarkReproducibility)
    tags: List[str] = Field(default_factory=list, max_length=64)
    notes: str = Field(default="", max_length=12000)
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("projectKey", "benchmarkKey", "title", "task"):
            setattr(self, attr, getattr(self, attr).strip())
        cleaned=[]
        for value in self.datasetRecordHashes:
            value=value.strip().lower()
            if not _is_hash(value):
                raise ValueError("datasetRecordHashes must contain SHA-256 hashes")
            cleaned.append(value)
        self.datasetRecordHashes=sorted(set(cleaned))
        self.baselineModelRecordHash=self.baselineModelRecordHash.strip().lower()
        if self.baselineModelRecordHash and not _is_hash(self.baselineModelRecordHash):
            raise ValueError("baselineModelRecordHash must be a SHA-256 hash")
        metric_keys=[x.metricKey for x in self.metrics]
        if len(metric_keys)!=len(set(metric_keys)):
            raise ValueError("metricKey values must be unique")
        slice_keys=[x.sliceKey for x in self.slices]
        if len(slice_keys)!=len(set(slice_keys)):
            raise ValueError("sliceKey values must be unique")
        self.tags=sorted({x.strip() for x in self.tags if x.strip()})
        return self


class BenchmarkExecutionPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    benchmarkHash: str = Field(min_length=64, max_length=64)
    modelRecordHashes: List[str] = Field(min_length=1, max_length=100)
    requestedBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def validate_hashes(self):
        self.benchmarkHash=self.benchmarkHash.lower()
        if not _is_hash(self.benchmarkHash): raise ValueError("benchmarkHash must be a SHA-256 hash")
        vals=[]
        for value in self.modelRecordHashes:
            value=value.lower()
            if not _is_hash(value): raise ValueError("modelRecordHashes must contain SHA-256 hashes")
            vals.append(value)
        self.modelRecordHashes=sorted(set(vals))
        return self


class EvaluationResultRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    benchmarkHash: str = Field(min_length=64, max_length=64)
    evaluationKey: str = Field(min_length=1, max_length=160)
    modelRecordHash: str = Field(min_length=64, max_length=64)
    sourceTrainingResultHash: str = Field(default="", max_length=64)
    metrics: Dict[str, float] = Field(min_length=1, max_length=100)
    datasetMetrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    sliceMetrics: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    sampleCount: int = Field(default=0, ge=0)
    sourceJobId: str = Field(default="", max_length=255)
    sourceResultHash: str = Field(default="", max_length=64)
    notes: str = Field(default="", max_length=12000)
    recordedBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        self.benchmarkHash=self.benchmarkHash.lower(); self.modelRecordHash=self.modelRecordHash.lower()
        if not _is_hash(self.benchmarkHash) or not _is_hash(self.modelRecordHash):
            raise ValueError("benchmarkHash/modelRecordHash must be SHA-256 hashes")
        for attr in ("sourceTrainingResultHash", "sourceResultHash"):
            value=getattr(self,attr).strip().lower()
            if value and not _is_hash(value): raise ValueError(f"{attr} must be a SHA-256 hash")
            setattr(self,attr,value)
        self.evaluationKey=self.evaluationKey.strip()
        return self


class EvaluationComparisonRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    benchmarkHash: str = Field(min_length=64, max_length=64)
    evaluationHashes: List[str] = Field(min_length=2, max_length=100)
    baselineEvaluationHash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_hashes(self):
        self.benchmarkHash=self.benchmarkHash.lower(); self.baselineEvaluationHash=self.baselineEvaluationHash.lower()
        if not _is_hash(self.benchmarkHash) or not _is_hash(self.baselineEvaluationHash): raise ValueError("invalid SHA-256 hash")
        vals=[]
        for value in self.evaluationHashes:
            value=value.lower()
            if not _is_hash(value): raise ValueError("evaluationHashes must contain SHA-256 hashes")
            vals.append(value)
        self.evaluationHashes=sorted(set(vals))
        if len(self.evaluationHashes)<2: raise ValueError("at least two unique evaluation hashes are required")
        if self.baselineEvaluationHash not in self.evaluationHashes: raise ValueError("baselineEvaluationHash must be included in evaluationHashes")
        return self


class CoreEvaluationPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    kind: CoreEvaluationKind
    sourceHash: str = Field(min_length=64, max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def validate_hash(self):
        self.sourceHash=self.sourceHash.lower()
        if not _is_hash(self.sourceHash): raise ValueError("sourceHash must be a SHA-256 hash")
        return self


def manifest() -> Dict[str, Any]:
    out={
        "ok":True,"schema":SCHEMA,"version":VERSION,"release":"AI Evaluation & Benchmark Workspace",
        "product":PRODUCT_KEY,"runtime":RUNTIME_KIND,"benchmarkSchema":BENCHMARK_SCHEMA,"resultSchema":RESULT_SCHEMA,
        "capabilities":{
            "aiEvaluationBenchmarkWorkspace":True,"registryBackedBenchmarkSuites":True,
            "researcherDefinedMetrics":True,"evaluationDatasetBinding":True,"diagnosticSlices":True,
            "deterministicEvaluationManifests":True,"immutableEvaluationResults":True,
            "baselineRelativeRegressionDiagnostics":True,"datasetAndSliceDiagnostics":True,
            "multiModelComparison":True,"platformCoreEvaluationPlanning":True,
        },
        "boundaries":{
            "automaticInferenceExecution":False,"automaticModelDownload":False,"automaticDatasetDownload":False,
            "automaticExternalProviderCall":False,"automaticCompositeRanking":False,"automaticWinnerSelection":False,
            "automaticPreferredModelPromotion":False,"automaticProductionApproval":False,
            "automaticScientificInterpretation":False,"scientificValidityInferred":False,
            "automaticCoreDispatch":False,"automaticCorePersistence":False,"governedCoreObjectCreated":False,
        },
        "metricKinds":["accuracy","precision","recall","f1","auc","mae","mse","rmse","r2","log-loss","perplexity","latency-ms","throughput","cost-usd","custom"],
    }
    out["manifestHash"]=content_hash(out)
    return out


def _load_benchmark(project_key:str, benchmark_hash:str)->Dict[str,Any]:
    if not _is_hash(benchmark_hash): raise HTTPException(status_code=422,detail="invalid benchmark hash")
    p=_benchmark_path(project_key,benchmark_hash.lower())
    if not p.exists(): raise HTTPException(status_code=404,detail="benchmark suite not found")
    row=_json_read(p); expected=content_hash({"schema":BENCHMARK_SCHEMA,"benchmark":row.get("benchmark") or {}})
    if row.get("benchmarkHash")!=expected: raise HTTPException(status_code=409,detail="benchmark integrity failure")
    return row


def compose_benchmark(req:BenchmarkSuiteRequest)->Dict[str,Any]:
    issues=[]; datasets=[]
    for h in req.datasetRecordHashes:
        try:
            row=load_registry_record(req.projectKey,"dataset",h)
            datasets.append({"datasetRecordHash":h,"recordRef":row.get("recordRef"),"datasetKey":row.get("datasetKey"),"versionLabel":row.get("versionLabel"),"datasetHash":row.get("datasetHash"),"format":row.get("format")})
        except HTTPException as exc:
            issues.append({"code":"dataset-record-unresolved","datasetRecordHash":h,"detail":str(exc.detail)})
    baseline=None
    if req.baselineModelRecordHash:
        try:
            row=load_registry_record(req.projectKey,"model",req.baselineModelRecordHash)
            baseline={"modelRecordHash":req.baselineModelRecordHash,"recordRef":row.get("recordRef"),"modelKey":row.get("modelKey"),"versionLabel":row.get("versionLabel"),"modelId":row.get("modelId")}
        except HTTPException as exc:
            issues.append({"code":"baseline-model-unresolved","modelRecordHash":req.baselineModelRecordHash,"detail":str(exc.detail)})
    benchmark={
        "projectKey":req.projectKey,"benchmarkKey":req.benchmarkKey,"title":req.title,"task":req.task,
        "datasets":sorted(datasets,key=lambda x:x["datasetRecordHash"]),
        "metrics":[x.model_dump(mode="json") for x in req.metrics],"slices":[x.model_dump(mode="json") for x in req.slices],
        "baselineModel":baseline,"reproducibility":req.reproducibility.model_dump(mode="json"),"tags":req.tags,"notes":req.notes,
    }
    h=content_hash({"schema":BENCHMARK_SCHEMA,"benchmark":benchmark})
    return {"ok":True,"schema":BENCHMARK_SCHEMA,"version":VERSION,"benchmarkHash":h,"benchmarkRef":f"sc://workbench/ai-evaluation/benchmark/{h}","benchmark":benchmark,"benchmarkReady":not issues,"issues":issues,
            "boundaries":{"automaticInferenceExecution":False,"automaticCompositeRanking":False,"automaticWinnerSelection":False,"scientificValidityInferred":False}}


def save_benchmark(req:BenchmarkSuiteRequest)->Dict[str,Any]:
    row=compose_benchmark(req)
    if not row["benchmarkReady"]: raise HTTPException(status_code=409,detail={"message":"benchmark suite is not ready","issues":row["issues"]})
    p=_benchmark_path(req.projectKey,row["benchmarkHash"]); idem=p.exists()
    if not idem: _atomic_json_write(p,{**row,"createdAt":_now(),"createdBy":req.createdBy,"immutability":{"contentAddressed":True,"replacementAllowed":False}})
    stored=_load_benchmark(req.projectKey,row["benchmarkHash"])
    return {**stored,"idempotent":idem}


def list_benchmarks(project_key:str)->Dict[str,Any]:
    rows=[]; root=_benchmark_dir(project_key)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r=_load_benchmark(project_key,p.stem); b=r["benchmark"]
                rows.append({"benchmarkHash":r["benchmarkHash"],"benchmarkRef":r["benchmarkRef"],"benchmarkKey":b.get("benchmarkKey"),"title":b.get("title"),"task":b.get("task"),"datasetCount":len(b.get("datasets") or []),"metricCount":len(b.get("metrics") or []),"createdAt":r.get("createdAt")})
            except Exception: rows.append({"benchmarkHash":p.stem,"integrityError":True})
    return {"ok":True,"schema":BENCHMARK_SCHEMA,"version":VERSION,"projectKey":project_key,"benchmarkCount":len(rows),"benchmarks":rows}


def evaluation_execution_plan(req:BenchmarkExecutionPlanRequest)->Dict[str,Any]:
    b=_load_benchmark(req.projectKey,req.benchmarkHash); models=[]; issues=[]
    for h in req.modelRecordHashes:
        try:
            r=load_registry_record(req.projectKey,"model",h); models.append({"modelRecordHash":h,"recordRef":r.get("recordRef"),"modelKey":r.get("modelKey"),"versionLabel":r.get("versionLabel"),"provider":r.get("provider"),"modelId":r.get("modelId")})
        except HTTPException as exc: issues.append({"code":"model-record-unresolved","modelRecordHash":h,"detail":str(exc.detail)})
    out={"ok":True,"schema":EXECUTION_PLAN_SCHEMA,"version":VERSION,"benchmarkHash":req.benchmarkHash,"benchmarkRef":b["benchmarkRef"],"authorized":False,"ready":not issues,
         "models":models,"datasets":b["benchmark"].get("datasets"),"metrics":b["benchmark"].get("metrics"),"slices":b["benchmark"].get("slices"),"reproducibility":b["benchmark"].get("reproducibility"),"issues":issues,"requestedBy":req.requestedBy,
         "boundaries":{"executionRequiresExplicitAuthorization":True,"automaticInferenceExecution":False,"automaticExternalProviderCall":False,"automaticWinnerSelection":False,"automaticProductionApproval":False}}
    out["planHash"]=content_hash(out); return out


def _load_result(project_key:str,benchmark_hash:str,evaluation_hash:str)->Dict[str,Any]:
    if not _is_hash(evaluation_hash): raise HTTPException(status_code=422,detail="invalid evaluation hash")
    p=_result_path(project_key,benchmark_hash,evaluation_hash.lower())
    if not p.exists(): raise HTTPException(status_code=404,detail="evaluation result not found")
    row=_json_read(p); expected=content_hash({"schema":RESULT_SCHEMA,"result":row.get("result") or {}})
    if row.get("evaluationHash")!=expected: raise HTTPException(status_code=409,detail="evaluation result integrity failure")
    return row


def save_evaluation_result(req:EvaluationResultRequest)->Dict[str,Any]:
    b=_load_benchmark(req.projectKey,req.benchmarkHash); model=load_registry_record(req.projectKey,"model",req.modelRecordHash)
    if req.sourceTrainingResultHash:
        # Verify the referenced training result exists in this project. Training results are indexed by run,
        # so search the v10.2 result tree deterministically rather than trusting a supplied hash.
        root=_store_root()/"ai-training-finetuning"/_stable_id(req.projectKey)/"results"
        matches=list(root.glob(f"*/{req.sourceTrainingResultHash}.json")) if root.exists() else []
        if not matches: raise HTTPException(status_code=409,detail="source training result hash could not be resolved")
    metric_defs={x["metricKey"]:x for x in b["benchmark"].get("metrics") or []}
    unknown=sorted(set(req.metrics)-set(metric_defs))
    if unknown: raise HTTPException(status_code=409,detail={"message":"evaluation result contains metrics not declared by benchmark","unknownMetrics":unknown})
    slice_defs={x["sliceKey"] for x in b["benchmark"].get("slices") or []}
    unknown_slices=sorted(set(req.sliceMetrics)-slice_defs)
    if unknown_slices: raise HTTPException(status_code=409,detail={"message":"evaluation result contains slices not declared by benchmark","unknownSlices":unknown_slices})
    dataset_hashes={x["datasetRecordHash"] for x in b["benchmark"].get("datasets") or []}
    unknown_ds=sorted(set(req.datasetMetrics)-dataset_hashes)
    if unknown_ds: raise HTTPException(status_code=409,detail={"message":"evaluation result contains datasets not declared by benchmark","unknownDatasets":unknown_ds})
    canonical=req.model_dump(mode="json"); canonical.pop("recordedBy",None)
    result={**canonical,"benchmarkRef":b["benchmarkRef"],"modelRecordRef":model.get("recordRef"),"model":{"modelKey":model.get("modelKey"),"versionLabel":model.get("versionLabel"),"provider":model.get("provider"),"modelId":model.get("modelId")}}
    h=content_hash({"schema":RESULT_SCHEMA,"result":result}); p=_result_path(req.projectKey,req.benchmarkHash,h); idem=p.exists()
    if not idem: _atomic_json_write(p,{"ok":True,"schema":RESULT_SCHEMA,"version":VERSION,"evaluationHash":h,"evaluationRef":f"sc://workbench/ai-evaluation/result/{h}","result":result,"recordedAt":_now(),"recordedBy":req.recordedBy,"immutability":{"contentAddressed":True,"replacementAllowed":False},"boundaries":{"automaticWinnerSelection":False,"automaticPreferredModelPromotion":False,"scientificValidityInferred":False}})
    stored=_load_result(req.projectKey,req.benchmarkHash,h); return {**stored,"idempotent":idem}


def list_evaluation_results(project_key:str,benchmark_hash:str)->Dict[str,Any]:
    _load_benchmark(project_key,benchmark_hash); rows=[]; root=_result_dir(project_key,benchmark_hash)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r=_load_result(project_key,benchmark_hash,p.stem); x=r["result"]
                rows.append({"evaluationHash":r["evaluationHash"],"evaluationRef":r["evaluationRef"],"evaluationKey":x.get("evaluationKey"),"modelRecordHash":x.get("modelRecordHash"),"model":x.get("model"),"metrics":x.get("metrics"),"sampleCount":x.get("sampleCount"),"recordedAt":r.get("recordedAt")})
            except Exception: rows.append({"evaluationHash":p.stem,"integrityError":True})
    return {"ok":True,"schema":RESULT_SCHEMA,"version":VERSION,"projectKey":project_key,"benchmarkHash":benchmark_hash,"evaluationCount":len(rows),"evaluations":rows}


def compare_evaluations(req:EvaluationComparisonRequest)->Dict[str,Any]:
    b=_load_benchmark(req.projectKey,req.benchmarkHash); rows={h:_load_result(req.projectKey,req.benchmarkHash,h) for h in req.evaluationHashes}; base=rows[req.baselineEvaluationHash]
    defs={x["metricKey"]:x for x in b["benchmark"].get("metrics") or []}; comparisons=[]; regressions=[]
    base_metrics=base["result"].get("metrics") or {}
    for h in req.evaluationHashes:
        r=rows[h]; metrics=r["result"].get("metrics") or {}; metric_rows=[]
        for key,d in defs.items():
            if key not in base_metrics or key not in metrics: continue
            bv=float(base_metrics[key]); ov=float(metrics[key]); delta=ov-bv; direction=d.get("direction","report-only"); tol=float(d.get("regressionTolerance") or 0.0); reg=False
            if h!=req.baselineEvaluationHash:
                if direction=="higher-is-better": reg=delta < -tol
                elif direction=="lower-is-better": reg=delta > tol
            item={"metricKey":key,"baselineValue":bv,"observedValue":ov,"delta":delta,"direction":direction,"regressionTolerance":tol,"regressionDetected":reg}
            metric_rows.append(item)
            if reg: regressions.append({"evaluationHash":h,**item})
        comparisons.append({"evaluationHash":h,"modelRecordHash":r["result"].get("modelRecordHash"),"metrics":metric_rows,"sliceMetrics":r["result"].get("sliceMetrics") or {},"datasetMetrics":r["result"].get("datasetMetrics") or {}})
    out={"ok":True,"schema":COMPARISON_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"benchmarkHash":req.benchmarkHash,"baselineEvaluationHash":req.baselineEvaluationHash,"comparisons":comparisons,"regressionCount":len(regressions),"regressions":regressions,
         "boundaries":{"regressionIsMetricThresholdOnly":True,"automaticCompositeRanking":False,"automaticWinnerSelection":False,"automaticPreferredModelPromotion":False,"scientificValidityInferred":False}}
    out["comparisonHash"]=content_hash(out); return out


def core_plan(req:CoreEvaluationPlanRequest)->Dict[str,Any]:
    if req.kind=="benchmark-suite": src=_load_benchmark(req.projectKey,req.sourceHash); ref=src["benchmarkRef"]; object_type="workbench.ai-benchmark-suite"
    elif req.kind=="evaluation-result":
        root=_project_root(req.projectKey)/"results"; matches=list(root.glob(f"*/{req.sourceHash}.json")) if root.exists() else []
        if not matches: raise HTTPException(status_code=404,detail="evaluation result not found")
        src=_json_read(matches[0]); ref=src.get("evaluationRef"); object_type="workbench.ai-evaluation-result"
    else:
        # Comparisons are intentionally ephemeral/content-addressed plans unless a future release adds persistence.
        ref=f"sc://workbench/ai-evaluation/comparison/{req.sourceHash}"; object_type="workbench.ai-evaluation-comparison"
    cfg=core_config()
    out={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"sourceHash":req.sourceHash,"sourceRef":ref,"bindingPlan":{"objectType":object_type,"role":"ai-evaluation-benchmark-evidence","coreProjectEntityId":req.coreProjectEntityId,"coreSessionId":req.coreSessionId,"visibility":req.visibility,"coreConfigured":bool(cfg.get("baseUrl"))},"createdBy":req.createdBy,
         "boundaries":{"automaticCoreDispatch":False,"automaticCorePersistence":False,"governedCoreObjectCreated":False,"automaticScientificInterpretation":False,"scientificValidityInferred":False}}
    out["planHash"]=content_hash(out); return out


@router.get("/ai-evaluation/manifest")
def manifest_endpoint(): return manifest()

@router.post("/ai-evaluation/benchmarks/compose")
def compose_endpoint(req:BenchmarkSuiteRequest): return compose_benchmark(req)

@router.post("/ai-evaluation/benchmarks")
def save_benchmark_endpoint(req:BenchmarkSuiteRequest): return save_benchmark(req)

@router.get("/ai-evaluation/benchmarks/{project_key}")
def list_benchmarks_endpoint(project_key:str): return list_benchmarks(project_key)

@router.get("/ai-evaluation/benchmarks/{project_key}/{benchmark_hash}")
def get_benchmark_endpoint(project_key:str,benchmark_hash:str): return _load_benchmark(project_key,benchmark_hash)

@router.post("/ai-evaluation/execution-plan")
def execution_plan_endpoint(req:BenchmarkExecutionPlanRequest): return evaluation_execution_plan(req)

@router.post("/ai-evaluation/results")
def save_result_endpoint(req:EvaluationResultRequest): return save_evaluation_result(req)

@router.get("/ai-evaluation/results/{project_key}/{benchmark_hash}")
def list_results_endpoint(project_key:str,benchmark_hash:str): return list_evaluation_results(project_key,benchmark_hash)

@router.get("/ai-evaluation/results/{project_key}/{benchmark_hash}/{evaluation_hash}")
def get_result_endpoint(project_key:str,benchmark_hash:str,evaluation_hash:str): return _load_result(project_key,benchmark_hash,evaluation_hash)

@router.post("/ai-evaluation/compare")
def compare_endpoint(req:EvaluationComparisonRequest): return compare_evaluations(req)

@router.post("/integration/core/ai-evaluation/plan")
def core_plan_endpoint(req:CoreEvaluationPlanRequest): return core_plan(req)

@router.get("/v1030/status")
def status_endpoint():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"aiEvaluationBenchmarkWorkspace":True,"registryBackedBenchmarkSuites":True,"immutableEvaluationResults":True,"baselineRelativeRegressionDiagnostics":True,"automaticInferenceExecution":False,"automaticCompositeRanking":False,"automaticWinnerSelection":False,"scientificValidityInferred":False}

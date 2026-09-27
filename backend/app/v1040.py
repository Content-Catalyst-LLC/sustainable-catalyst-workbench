"""Workbench v10.4.0 — Hyperparameter Optimization & Search Engine.

Content-addressed hyperparameter search studies built on immutable v10.2 training-run templates
and v10.3 benchmark objectives. The engine defines explicit parameter domains, deterministic
trial manifests, resource/search budgets, append-only trial observations, resumable search
state, and neutral objective diagnostics. It can generate grid, seeded random, and Latin-
hypercube trial manifests locally; Bayesian/custom strategies are represented as explicit
adapter contracts and are never executed implicitly.

v10.4.0 intentionally does not launch training, call external optimizers/providers, promote a
trial/model, declare a preferred model, approve deployment, infer scientific validity, or create
governed Platform Core objects automatically.
"""
from __future__ import annotations

import hashlib
import itertools
import math
import random
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
from .v1020 import _load_run as load_training_run
from .v1030 import _load_benchmark as load_benchmark

VERSION = APP_VERSION
SCHEMA = "sc-workbench-hyperparameter-optimization-search-engine/1.0"
SEARCH_SCHEMA = "sc-workbench-ai-hyperparameter-search/1.0"
TRIAL_MANIFEST_SCHEMA = "sc-workbench-ai-search-trial-manifest/1.0"
TRIAL_RESULT_SCHEMA = "sc-workbench-ai-search-trial-result/1.0"
ANALYSIS_SCHEMA = "sc-workbench-ai-search-analysis/1.0"
EXECUTION_PLAN_SCHEMA = "sc-workbench-ai-search-execution-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-ai-search-core-plan/1.0"
router = APIRouter(tags=["workbench-v1040-hyperparameter-optimization-search-engine"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ParameterKind = Literal["float", "int", "categorical", "boolean"]
ParameterScale = Literal["linear", "log"]
SearchStrategy = Literal["grid", "random", "latin-hypercube", "bayesian-contract", "custom"]
ObjectiveDirection = Literal["maximize", "minimize"]
TrialStatus = Literal["completed", "failed", "cancelled", "pruned"]
CoreSearchKind = Literal["search-study", "trial-result", "analysis"]

_ALLOWED_PATHS = {
    "hyperparameters.epochs", "hyperparameters.maxSteps", "hyperparameters.batchSize",
    "hyperparameters.gradientAccumulationSteps", "hyperparameters.learningRate",
    "hyperparameters.weightDecay", "hyperparameters.warmupSteps", "hyperparameters.maxGradientNorm",
    "fineTuning.loraRank", "fineTuning.loraAlpha", "fineTuning.loraDropout",
    "fineTuning.quantizationBits", "checkpoints.everySteps", "evaluation.everySteps",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


def _project_root(project_key: str) -> Path:
    return _store_root() / "ai-hyperparameter-search" / _stable_id(project_key)


def _search_dir(project_key: str) -> Path:
    return _project_root(project_key) / "searches"


def _search_path(project_key: str, search_hash: str) -> Path:
    return _search_dir(project_key) / f"{search_hash}.json"


def _result_dir(project_key: str, search_hash: str) -> Path:
    return _project_root(project_key) / "trial-results" / search_hash


def _result_path(project_key: str, search_hash: str, trial_hash: str) -> Path:
    return _result_dir(project_key, search_hash) / f"{trial_hash}.json"


class SearchParameter(BaseModel):
    parameterKey: str = Field(min_length=1, max_length=160)
    path: str = Field(min_length=1, max_length=240)
    kind: ParameterKind
    scale: ParameterScale = "linear"
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = Field(default=None, gt=0.0)
    choices: List[Any] = Field(default_factory=list, max_length=1000)
    gridValues: List[Any] = Field(default_factory=list, max_length=10000)
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def validate_domain(self):
        self.parameterKey = self.parameterKey.strip()
        self.path = self.path.strip()
        if self.path not in _ALLOWED_PATHS:
            raise ValueError(f"unsupported tunable path: {self.path}")
        if self.kind in {"float", "int"}:
            if self.minimum is None or self.maximum is None:
                raise ValueError("numeric parameters require minimum and maximum")
            if self.minimum >= self.maximum:
                raise ValueError("minimum must be less than maximum")
            if self.scale == "log" and self.minimum <= 0:
                raise ValueError("log-scaled parameters require minimum > 0")
            if self.choices:
                raise ValueError("numeric parameters must not define choices")
        elif self.kind == "categorical":
            if not self.choices:
                raise ValueError("categorical parameters require choices")
            if self.minimum is not None or self.maximum is not None:
                raise ValueError("categorical parameters must not define numeric bounds")
            if self.scale != "linear":
                raise ValueError("categorical parameters support linear scale only")
        elif self.kind == "boolean":
            if self.minimum is not None or self.maximum is not None or self.choices:
                raise ValueError("boolean parameters do not accept bounds or choices")
            if self.scale != "linear":
                raise ValueError("boolean parameters support linear scale only")
        return self


class SearchObjective(BaseModel):
    metricKey: str = Field(min_length=1, max_length=160)
    direction: ObjectiveDirection
    datasetRecordHash: str = Field(default="", max_length=64)
    sliceKey: str = Field(default="", max_length=160)
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def normalize(self):
        self.metricKey = self.metricKey.strip()
        self.datasetRecordHash = self.datasetRecordHash.strip().lower()
        self.sliceKey = self.sliceKey.strip()
        if self.datasetRecordHash and not _is_hash(self.datasetRecordHash):
            raise ValueError("datasetRecordHash must be a SHA-256 hash")
        return self


class SearchBudget(BaseModel):
    maxTrials: int = Field(default=20, ge=1, le=100000)
    maxConcurrentTrials: int = Field(default=1, ge=1, le=10000)
    maxWallMinutes: int = Field(default=1440, ge=1, le=5256000)
    maxCpuHours: float = Field(default=0.0, ge=0.0)
    maxGpuHours: float = Field(default=0.0, ge=0.0)
    maxCostUsd: float = Field(default=0.0, ge=0.0)
    failureBudget: int = Field(default=10, ge=0, le=100000)


class SearchStudyRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    searchKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    baseTrainingRunHash: str = Field(min_length=64, max_length=64)
    benchmarkHash: str = Field(min_length=64, max_length=64)
    objective: SearchObjective
    parameters: List[SearchParameter] = Field(min_length=1, max_length=128)
    strategy: SearchStrategy = "random"
    seed: int = Field(default=0, ge=0, le=2**31 - 1)
    budget: SearchBudget = Field(default_factory=SearchBudget)
    externalOptimizerRef: str = Field(default="", max_length=1000)
    tags: List[str] = Field(default_factory=list, max_length=64)
    notes: str = Field(default="", max_length=12000)
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("projectKey", "searchKey", "title"):
            setattr(self, attr, getattr(self, attr).strip())
        for attr in ("baseTrainingRunHash", "benchmarkHash"):
            value = getattr(self, attr).strip().lower()
            if not _is_hash(value):
                raise ValueError(f"{attr} must be a SHA-256 hash")
            setattr(self, attr, value)
        keys = [p.parameterKey for p in self.parameters]
        paths = [p.path for p in self.parameters]
        if len(keys) != len(set(keys)):
            raise ValueError("parameterKey values must be unique")
        if len(paths) != len(set(paths)):
            raise ValueError("parameter paths must be unique")
        self.externalOptimizerRef = self.externalOptimizerRef.strip()
        if self.strategy in {"bayesian-contract", "custom"} and not self.externalOptimizerRef:
            raise ValueError("bayesian-contract/custom strategies require externalOptimizerRef")
        self.tags = sorted({x.strip() for x in self.tags if x.strip()})
        return self


class TrialManifestRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    searchHash: str = Field(min_length=64, max_length=64)
    trialCount: Optional[int] = Field(default=None, ge=1, le=100000)

    @model_validator(mode="after")
    def validate_hash(self):
        self.searchHash = self.searchHash.lower()
        if not _is_hash(self.searchHash):
            raise ValueError("searchHash must be a SHA-256 hash")
        return self


class SearchExecutionPlanRequest(TrialManifestRequest):
    requestedBy: str = Field(default="workbench", max_length=160)


class TrialResultRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    searchHash: str = Field(min_length=64, max_length=64)
    trialHash: str = Field(min_length=64, max_length=64)
    status: TrialStatus
    objectiveValue: Optional[float] = None
    metrics: Dict[str, float] = Field(default_factory=dict, max_length=500)
    trainingRunHash: str = Field(default="", max_length=64)
    trainingResultHash: str = Field(default="", max_length=64)
    evaluationHash: str = Field(default="", max_length=64)
    modelRecordHash: str = Field(default="", max_length=64)
    resourceUsage: Dict[str, float] = Field(default_factory=dict, max_length=100)
    notes: str = Field(default="", max_length=12000)
    recordedBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("searchHash", "trialHash"):
            value = getattr(self, attr).lower()
            if not _is_hash(value):
                raise ValueError(f"{attr} must be a SHA-256 hash")
            setattr(self, attr, value)
        for attr in ("trainingRunHash", "trainingResultHash", "evaluationHash", "modelRecordHash"):
            value = getattr(self, attr).strip().lower()
            if value and not _is_hash(value):
                raise ValueError(f"{attr} must be a SHA-256 hash")
            setattr(self, attr, value)
        if self.status == "completed" and self.objectiveValue is None:
            raise ValueError("completed trials require objectiveValue")
        return self


class SearchAnalysisRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    searchHash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def validate_hash(self):
        self.searchHash = self.searchHash.lower()
        if not _is_hash(self.searchHash):
            raise ValueError("searchHash must be a SHA-256 hash")
        return self


class CoreSearchPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    kind: CoreSearchKind
    sourceHash: str = Field(min_length=64, max_length=64)
    searchHash: str = Field(default="", max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def validate_hashes(self):
        self.sourceHash = self.sourceHash.lower()
        if not _is_hash(self.sourceHash):
            raise ValueError("sourceHash must be a SHA-256 hash")
        self.searchHash = self.searchHash.strip().lower()
        if self.searchHash and not _is_hash(self.searchHash):
            raise ValueError("searchHash must be a SHA-256 hash")
        return self


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True, "schema": SCHEMA, "version": VERSION,
        "release": "Hyperparameter Optimization & Search Engine", "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "searchSchema": SEARCH_SCHEMA, "trialManifestSchema": TRIAL_MANIFEST_SCHEMA,
        "trialResultSchema": TRIAL_RESULT_SCHEMA,
        "capabilities": {
            "hyperparameterOptimizationSearchEngine": True,
            "trainingRunTemplateBinding": True,
            "benchmarkObjectiveBinding": True,
            "typedSearchSpaces": True,
            "gridSearch": True,
            "seededRandomSearch": True,
            "latinHypercubeSearch": True,
            "externalBayesianOptimizerContract": True,
            "deterministicTrialManifests": True,
            "searchBudgets": True,
            "resumableTrialState": True,
            "immutableTrialResults": True,
            "objectiveDiagnostics": True,
            "platformCoreSearchPlanning": True,
        },
        "boundaries": {
            "automaticTrainingExecution": False,
            "automaticInferenceExecution": False,
            "automaticExternalOptimizerCall": False,
            "automaticModelDownload": False,
            "automaticDatasetDownload": False,
            "automaticPreferredModelPromotion": False,
            "automaticProductionApproval": False,
            "objectiveOrderingIsModelPreference": False,
            "scientificValidityInferred": False,
            "automaticCoreDispatch": False,
            "automaticCorePersistence": False,
            "governedCoreObjectCreated": False,
        },
        "strategies": ["grid", "random", "latin-hypercube", "bayesian-contract", "custom"],
        "locallyGeneratedStrategies": ["grid", "random", "latin-hypercube"],
        "tunablePaths": sorted(_ALLOWED_PATHS),
    }
    out["manifestHash"] = content_hash(out)
    return out


def _load_search(project_key: str, search_hash: str) -> Dict[str, Any]:
    if not _is_hash(search_hash):
        raise HTTPException(status_code=422, detail="invalid search hash")
    p = _search_path(project_key, search_hash.lower())
    if not p.exists():
        raise HTTPException(status_code=404, detail="search study not found")
    row = _json_read(p)
    expected = content_hash({"schema": SEARCH_SCHEMA, "search": row.get("search") or {}})
    if row.get("searchHash") != expected:
        raise HTTPException(status_code=409, detail="search study integrity failure")
    return row


def compose_search(req: SearchStudyRequest) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    try:
        training = load_training_run(req.projectKey, req.baseTrainingRunHash)
    except HTTPException as exc:
        training = None
        issues.append({"code": "training-run-unresolved", "detail": str(exc.detail)})
    try:
        benchmark = load_benchmark(req.projectKey, req.benchmarkHash)
    except HTTPException as exc:
        benchmark = None
        issues.append({"code": "benchmark-unresolved", "detail": str(exc.detail)})

    if benchmark:
        metric_keys = {m.get("metricKey") for m in benchmark.get("benchmark", {}).get("metrics", [])}
        if req.objective.metricKey not in metric_keys:
            issues.append({"code": "objective-metric-not-declared", "metricKey": req.objective.metricKey})
        if req.objective.datasetRecordHash:
            dataset_hashes = {d.get("datasetRecordHash") for d in benchmark.get("benchmark", {}).get("datasets", [])}
            if req.objective.datasetRecordHash not in dataset_hashes:
                issues.append({"code": "objective-dataset-not-declared", "datasetRecordHash": req.objective.datasetRecordHash})
        if req.objective.sliceKey:
            slice_keys = {s.get("sliceKey") for s in benchmark.get("benchmark", {}).get("slices", [])}
            if req.objective.sliceKey not in slice_keys:
                issues.append({"code": "objective-slice-not-declared", "sliceKey": req.objective.sliceKey})

    search = {
        "projectKey": req.projectKey, "searchKey": req.searchKey, "title": req.title,
        "baseTrainingRunHash": req.baseTrainingRunHash,
        "baseTrainingRunRef": training.get("runRef") if training else None,
        "benchmarkHash": req.benchmarkHash,
        "benchmarkRef": benchmark.get("benchmarkRef") if benchmark else None,
        "objective": req.objective.model_dump(mode="json"),
        "parameters": [p.model_dump(mode="json") for p in req.parameters],
        "strategy": req.strategy, "seed": req.seed, "budget": req.budget.model_dump(mode="json"),
        "externalOptimizerRef": req.externalOptimizerRef, "tags": req.tags, "notes": req.notes,
    }
    h = content_hash({"schema": SEARCH_SCHEMA, "search": search})
    return {
        "ok": True, "schema": SEARCH_SCHEMA, "version": VERSION,
        "searchHash": h, "searchRef": f"sc://workbench/ai-optimization/search/{h}",
        "search": search, "searchReady": not issues, "issues": issues,
        "boundaries": {
            "automaticTrainingExecution": False, "automaticExternalOptimizerCall": False,
            "automaticPreferredModelPromotion": False, "scientificValidityInferred": False,
        },
    }


def save_search(req: SearchStudyRequest) -> Dict[str, Any]:
    row = compose_search(req)
    if not row["searchReady"]:
        raise HTTPException(status_code=409, detail={"message": "search study is not ready", "issues": row["issues"]})
    p = _search_path(req.projectKey, row["searchHash"])
    idem = p.exists()
    if not idem:
        _atomic_json_write(p, {**row, "createdAt": _now(), "createdBy": req.createdBy,
                               "immutability": {"contentAddressed": True, "replacementAllowed": False}})
    return {**_load_search(req.projectKey, row["searchHash"]), "idempotent": idem}


def list_searches(project_key: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    root = _search_dir(project_key)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r = _load_search(project_key, p.stem); s = r["search"]
                rows.append({"searchHash": r["searchHash"], "searchRef": r["searchRef"],
                             "searchKey": s.get("searchKey"), "title": s.get("title"),
                             "strategy": s.get("strategy"), "parameterCount": len(s.get("parameters") or []),
                             "maxTrials": (s.get("budget") or {}).get("maxTrials"), "createdAt": r.get("createdAt")})
            except Exception:
                rows.append({"searchHash": p.stem, "integrityError": True})
    return {"ok": True, "schema": SEARCH_SCHEMA, "version": VERSION, "projectKey": project_key,
            "searchCount": len(rows), "searches": rows}


def _numeric_value(p: Dict[str, Any], u: float) -> Any:
    lo = float(p["minimum"]); hi = float(p["maximum"])
    if p.get("scale") == "log":
        value = math.exp(math.log(lo) + u * (math.log(hi) - math.log(lo)))
    else:
        value = lo + u * (hi - lo)
    if p["kind"] == "int":
        return int(round(value))
    step = p.get("step")
    if step:
        value = lo + round((value - lo) / float(step)) * float(step)
        value = min(max(value, lo), hi)
    return float(value)


def _grid_values(p: Dict[str, Any]) -> List[Any]:
    if p.get("gridValues"):
        vals = p["gridValues"]
    elif p["kind"] == "categorical":
        vals = p["choices"]
    elif p["kind"] == "boolean":
        vals = [False, True]
    else:
        lo = float(p["minimum"]); hi = float(p["maximum"]); step = p.get("step")
        if step:
            n = int(math.floor((hi - lo) / float(step))) + 1
            vals = [lo + i * float(step) for i in range(n)]
            if vals[-1] < hi and len(vals) < 10000:
                vals.append(hi)
        else:
            vals = [lo, hi]
        if p["kind"] == "int": vals = [int(round(v)) for v in vals]
    # stable de-duplication
    out=[]
    for v in vals:
        if v not in out: out.append(v)
    return out


def _sample_parameter(p: Dict[str, Any], rng: random.Random, u: Optional[float] = None) -> Any:
    if p["kind"] == "categorical":
        return p["choices"][rng.randrange(len(p["choices"]))]
    if p["kind"] == "boolean":
        return bool(rng.randrange(2))
    if u is None: u = rng.random()
    return _numeric_value(p, float(u))


def generate_trial_manifest(req: TrialManifestRequest) -> Dict[str, Any]:
    row = _load_search(req.projectKey, req.searchHash); search = row["search"]
    budget_n = int((search.get("budget") or {}).get("maxTrials") or 1)
    n = min(req.trialCount or budget_n, budget_n)
    strategy = search["strategy"]; params = search["parameters"]; trials: List[Dict[str, Any]] = []
    external_required = strategy in {"bayesian-contract", "custom"}

    if strategy == "grid":
        spaces = [_grid_values(p) for p in params]
        for values in itertools.islice(itertools.product(*spaces), n):
            assignment = {p["path"]: v for p, v in zip(params, values)}
            th = content_hash({"searchHash": req.searchHash, "parameters": assignment})
            trials.append({"trialIndex": len(trials), "trialHash": th, "parameters": assignment})
    elif strategy in {"random", "latin-hypercube"}:
        rng = random.Random(int(search.get("seed") or 0))
        # independent random permutations per numeric dimension for Latin hypercube
        strata: Dict[str, List[float]] = {}
        if strategy == "latin-hypercube":
            for p in params:
                if p["kind"] in {"float", "int"}:
                    vals = [(i + rng.random()) / n for i in range(n)]
                    rng.shuffle(vals); strata[p["path"]] = vals
        seen=set(); attempts=0
        while len(trials) < n and attempts < max(1000, n * 100):
            i=len(trials); assignment={}
            for p in params:
                u = strata.get(p["path"], [None] * n)[i] if p["path"] in strata else None
                assignment[p["path"]] = _sample_parameter(p, rng, u)
            key=content_hash(assignment); attempts += 1
            if key in seen: continue
            seen.add(key); th=content_hash({"searchHash":req.searchHash,"parameters":assignment})
            trials.append({"trialIndex":i,"trialHash":th,"parameters":assignment})
    else:
        # External adaptive optimizers are intentionally represented as a contract only.
        trials=[]

    out={"ok":True,"schema":TRIAL_MANIFEST_SCHEMA,"version":VERSION,"projectKey":req.projectKey,
         "searchHash":req.searchHash,"searchRef":row["searchRef"],"strategy":strategy,
         "seed":search.get("seed"),"requestedTrialCount":n,"generatedTrialCount":len(trials),
         "trials":trials,"externalOptimizerRequired":external_required,
         "externalOptimizerRef":search.get("externalOptimizerRef") or "",
         "boundaries":{"automaticTrainingExecution":False,"automaticExternalOptimizerCall":False,
                       "automaticPreferredModelPromotion":False,"objectiveOrderingIsModelPreference":False}}
    out["manifestHash"]=content_hash(out)
    return out


def execution_plan(req: SearchExecutionPlanRequest) -> Dict[str, Any]:
    row=_load_search(req.projectKey,req.searchHash); manifest_row=generate_trial_manifest(TrialManifestRequest(projectKey=req.projectKey,searchHash=req.searchHash,trialCount=req.trialCount))
    out={"ok":True,"schema":EXECUTION_PLAN_SCHEMA,"version":VERSION,"projectKey":req.projectKey,
         "searchHash":req.searchHash,"baseTrainingRunHash":row["search"]["baseTrainingRunHash"],
         "benchmarkHash":row["search"]["benchmarkHash"],"trialManifestHash":manifest_row["manifestHash"],
         "trials":manifest_row["trials"],"authorized":False,"requestedBy":req.requestedBy,
         "budget":row["search"].get("budget"),"externalOptimizerRequired":manifest_row["externalOptimizerRequired"],
         "boundaries":{"executionRequiresExplicitAuthorization":True,"automaticTrainingExecution":False,
                       "automaticExternalOptimizerCall":False,"automaticPreferredModelPromotion":False}}
    out["planHash"]=content_hash(out); return out


def _trial_lookup(project_key: str, search_hash: str, trial_hash: str) -> Dict[str, Any]:
    manifest_row=generate_trial_manifest(TrialManifestRequest(projectKey=project_key,searchHash=search_hash))
    for t in manifest_row["trials"]:
        if t["trialHash"] == trial_hash: return t
    raise HTTPException(status_code=409, detail="trialHash is not part of the deterministic search manifest")


def save_trial_result(req: TrialResultRequest) -> Dict[str, Any]:
    search=_load_search(req.projectKey,req.searchHash); trial=_trial_lookup(req.projectKey,req.searchHash,req.trialHash)
    canonical=req.model_dump(mode="json"); canonical.pop("recordedBy",None)
    result={**canonical,"trialParameters":trial["parameters"],"objective":search["search"]["objective"]}
    record_hash=content_hash({"schema":TRIAL_RESULT_SCHEMA,"result":result})
    p=_result_path(req.projectKey,req.searchHash,req.trialHash); idem=p.exists()
    if idem:
        existing=_json_read(p)
        if existing.get("recordHash") != record_hash:
            raise HTTPException(status_code=409,detail="trial result already exists with different content")
        return {**existing,"idempotent":True}
    _atomic_json_write(p,{"ok":True,"schema":TRIAL_RESULT_SCHEMA,"version":VERSION,"recordHash":record_hash,
                          "resultRef":f"sc://workbench/ai-optimization/trial-result/{record_hash}","result":result,
                          "recordedAt":_now(),"recordedBy":req.recordedBy,
                          "immutability":{"contentAddressed":True,"trialResultReplacementAllowed":False},
                          "boundaries":{"automaticPreferredModelPromotion":False,"scientificValidityInferred":False}})
    return {**_json_read(p),"idempotent":False}


def list_trial_results(project_key: str, search_hash: str) -> Dict[str, Any]:
    _load_search(project_key,search_hash); rows=[]; root=_result_dir(project_key,search_hash)
    if root.exists():
        for p in sorted(root.glob("*.json")):
            try:
                r=_json_read(p); rows.append({"trialHash":r["result"]["trialHash"],"recordHash":r["recordHash"],
                                              "status":r["result"]["status"],"objectiveValue":r["result"].get("objectiveValue"),
                                              "recordedAt":r.get("recordedAt")})
            except Exception: rows.append({"trialHash":p.stem,"integrityError":True})
    return {"ok":True,"schema":TRIAL_RESULT_SCHEMA,"version":VERSION,"projectKey":project_key,"searchHash":search_hash,
            "resultCount":len(rows),"results":rows}


def analyze_search(req: SearchAnalysisRequest) -> Dict[str, Any]:
    search=_load_search(req.projectKey,req.searchHash); listing=list_trial_results(req.projectKey,req.searchHash)
    complete=[]; status_counts={"completed":0,"failed":0,"cancelled":0,"pruned":0}
    for item in listing["results"]:
        if item.get("integrityError"): continue
        status_counts[item["status"]]=status_counts.get(item["status"],0)+1
        if item["status"]=="completed" and item.get("objectiveValue") is not None:
            p=_result_path(req.projectKey,req.searchHash,item["trialHash"]); row=_json_read(p)
            complete.append({"trialHash":item["trialHash"],"recordHash":item["recordHash"],"objectiveValue":float(item["objectiveValue"]),"parameters":row["result"].get("trialParameters") or {}})
    direction=search["search"]["objective"]["direction"]
    complete.sort(key=lambda x:x["objectiveValue"],reverse=(direction=="maximize"))
    max_trials=int(search["search"]["budget"]["maxTrials"])
    out={"ok":True,"schema":ANALYSIS_SCHEMA,"version":VERSION,"projectKey":req.projectKey,"searchHash":req.searchHash,
         "objective":search["search"]["objective"],"statusCounts":status_counts,"recordedTrialCount":listing["resultCount"],
         "remainingTrialBudget":max(0,max_trials-listing["resultCount"]),"objectiveOrdering":complete,
         "observedMinimum":min((x["objectiveValue"] for x in complete),default=None),
         "observedMaximum":max((x["objectiveValue"] for x in complete),default=None),
         "boundaries":{"objectiveOrderingIsResearcherDefinedMetricOnly":True,"automaticWinnerSelection":False,
                       "automaticPreferredModelPromotion":False,"automaticProductionApproval":False,
                       "scientificValidityInferred":False}}
    out["analysisHash"]=content_hash(out); return out


def core_plan(req: CoreSearchPlanRequest) -> Dict[str, Any]:
    if req.kind=="search-study":
        src=_load_search(req.projectKey,req.sourceHash); ref=src["searchRef"]; object_type="workbench.ai-hyperparameter-search"
    elif req.kind=="trial-result":
        if not req.searchHash: raise HTTPException(status_code=422,detail="searchHash is required for trial-result plans")
        root=_result_dir(req.projectKey,req.searchHash); matches=[]
        if root.exists():
            for p in root.glob("*.json"):
                r=_json_read(p)
                if r.get("recordHash")==req.sourceHash: matches.append(r)
        if not matches: raise HTTPException(status_code=404,detail="trial result not found")
        ref=matches[0]["resultRef"]; object_type="workbench.ai-search-trial-result"
    else:
        ref=f"sc://workbench/ai-optimization/analysis/{req.sourceHash}"; object_type="workbench.ai-search-analysis"
    cfg=core_config()
    out={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"sourceHash":req.sourceHash,"sourceRef":ref,
         "bindingPlan":{"objectType":object_type,"role":"ai-hyperparameter-search-evidence","coreProjectEntityId":req.coreProjectEntityId,
                        "coreSessionId":req.coreSessionId,"visibility":req.visibility,"coreConfigured":bool(cfg.get("baseUrl"))},
         "createdBy":req.createdBy,
         "boundaries":{"automaticCoreDispatch":False,"automaticCorePersistence":False,"governedCoreObjectCreated":False,
                       "automaticPreferredModelPromotion":False,"scientificValidityInferred":False}}
    out["planHash"]=content_hash(out); return out


@router.get("/ai-optimization/manifest")
def manifest_endpoint(): return manifest()

@router.post("/ai-optimization/searches/compose")
def compose_endpoint(req: SearchStudyRequest): return compose_search(req)

@router.post("/ai-optimization/searches")
def save_endpoint(req: SearchStudyRequest): return save_search(req)

@router.get("/ai-optimization/searches/{project_key}")
def list_endpoint(project_key: str): return list_searches(project_key)

@router.get("/ai-optimization/searches/{project_key}/{search_hash}")
def get_endpoint(project_key: str, search_hash: str): return _load_search(project_key,search_hash)

@router.post("/ai-optimization/trials/generate")
def trials_endpoint(req: TrialManifestRequest): return generate_trial_manifest(req)

@router.post("/ai-optimization/execution-plan")
def execution_endpoint(req: SearchExecutionPlanRequest): return execution_plan(req)

@router.post("/ai-optimization/trial-results")
def result_endpoint(req: TrialResultRequest): return save_trial_result(req)

@router.get("/ai-optimization/trial-results/{project_key}/{search_hash}")
def list_results_endpoint(project_key: str, search_hash: str): return list_trial_results(project_key,search_hash)

@router.post("/ai-optimization/analyze")
def analyze_endpoint(req: SearchAnalysisRequest): return analyze_search(req)

@router.post("/integration/core/ai-optimization/plan")
def core_plan_endpoint(req: CoreSearchPlanRequest): return core_plan(req)

@router.get("/v1040/status")
def status_endpoint():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"hyperparameterOptimizationSearchEngine":True,
            "gridSearch":True,"seededRandomSearch":True,"latinHypercubeSearch":True,
            "externalBayesianOptimizerContract":True,"immutableTrialResults":True,
            "automaticTrainingExecution":False,"automaticWinnerSelection":False,
            "automaticPreferredModelPromotion":False,"scientificValidityInferred":False}

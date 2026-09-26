"""Workbench v10.0.0 — Scientific AI Engineering Runtime Foundation.

A governed foundation for AI/ML engineering inside Sustainable Catalyst Workbench.
The runtime defines content-addressed AI experiment specifications, explicit model
and dataset bindings, deterministic training/inference configuration, environment
and resource budgets, evaluation hooks, neutral execution plans, and Platform Core
handoff plans.

v10.0.0 intentionally does not download models, launch training, call external model
providers, execute arbitrary code, select a preferred model, infer scientific
validity, or create governed Platform Core objects automatically. Later v10 builds
can implement concrete adapters against these contracts.
"""
from __future__ import annotations

import hashlib
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

VERSION = APP_VERSION
SCHEMA = "sc-workbench-scientific-ai-engineering-runtime-foundation/1.0"
EXPERIMENT_SCHEMA = "sc-workbench-ai-engineering-experiment/1.0"
CATALOG_SCHEMA = "sc-workbench-ai-engineering-source-catalog/1.0"
EXECUTION_PLAN_SCHEMA = "sc-workbench-ai-engineering-execution-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-ai-engineering-core-plan/1.0"
RUNTIME_CONTRACT_SCHEMA = "sc-workbench-ai-runtime-contract/1.0"
router = APIRouter(tags=["workbench-v1000-scientific-ai-engineering-runtime-foundation"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")

AIProvider = Literal["local", "openai-compatible", "huggingface", "workspace-ml", "custom"]
AITask = Literal[
    "text-generation", "classification", "regression", "embedding", "forecasting",
    "surrogate-modeling", "multimodal", "custom"
]
ExperimentMode = Literal["training", "inference", "evaluation", "hybrid", "scientific-ml"]
DatasetRole = Literal["train", "validation", "test", "inference", "reference"]
Accelerator = Literal["cpu", "cuda", "mps", "tpu", "external", "unspecified"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _experiment_dir(project_key: str) -> Path:
    return _store_root() / "ai-engineering-experiments" / _stable_id(project_key)


def _experiment_path(project_key: str, experiment_hash: str) -> Path:
    return _experiment_dir(project_key) / f"{experiment_hash}.json"


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


class ModelReference(BaseModel):
    modelKey: str = Field(min_length=1, max_length=160)
    provider: AIProvider = "local"
    modelId: str = Field(min_length=1, max_length=500)
    modelVersion: str = Field(default="", max_length=160)
    task: AITask = "custom"
    artifactHash: str = Field(default="", max_length=64)
    license: str = Field(default="", max_length=500)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def normalize(self):
        self.modelKey = self.modelKey.strip()
        self.modelId = self.modelId.strip()
        self.modelVersion = self.modelVersion.strip()
        self.artifactHash = self.artifactHash.strip().lower()
        if self.artifactHash and not _is_hash(self.artifactHash):
            raise ValueError("artifactHash must be a 64-character hexadecimal SHA-256 hash")
        return self


class DatasetBinding(BaseModel):
    role: DatasetRole
    datasetRef: str = Field(min_length=1, max_length=1000)
    datasetHash: str = Field(default="", max_length=64)
    schemaRef: str = Field(default="", max_length=1000)
    immutable: bool = True
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def normalize(self):
        self.datasetRef = self.datasetRef.strip()
        self.datasetHash = self.datasetHash.strip().lower()
        if self.datasetHash and not _is_hash(self.datasetHash):
            raise ValueError("datasetHash must be a 64-character hexadecimal SHA-256 hash")
        return self


class AIEnvironment(BaseModel):
    pythonVersion: str = Field(default="", max_length=80)
    framework: str = Field(default="", max_length=160)
    frameworkVersion: str = Field(default="", max_length=160)
    containerImage: str = Field(default="", max_length=500)
    dependencyLockHash: str = Field(default="", max_length=64)
    accelerator: Accelerator = "unspecified"
    precision: str = Field(default="", max_length=80)
    networkAccessAllowed: bool = False

    @model_validator(mode="after")
    def validate_lock_hash(self):
        self.dependencyLockHash = self.dependencyLockHash.strip().lower()
        if self.dependencyLockHash and not _is_hash(self.dependencyLockHash):
            raise ValueError("dependencyLockHash must be a 64-character hexadecimal SHA-256 hash")
        return self


class TrainingConfiguration(BaseModel):
    enabled: bool = False
    seed: int = Field(default=0, ge=0, le=2**31 - 1)
    epochs: int = Field(default=1, ge=1, le=100000)
    batchSize: int = Field(default=1, ge=1, le=1000000)
    learningRate: float = Field(default=0.001, gt=0.0)
    optimizer: str = Field(default="", max_length=160)
    deterministicRequested: bool = True
    checkpointEverySteps: int = Field(default=0, ge=0)
    gradientAccumulationSteps: int = Field(default=1, ge=1)


class InferenceConfiguration(BaseModel):
    enabled: bool = True
    seed: int = Field(default=0, ge=0, le=2**31 - 1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    topP: float = Field(default=1.0, gt=0.0, le=1.0)
    maxOutputTokens: int = Field(default=1024, ge=1, le=1000000)
    deterministicRequested: bool = True
    toolUseAllowed: bool = False
    externalNetworkAllowed: bool = False
    responseSchema: Dict[str, Any] = Field(default_factory=dict)


class EvaluationHook(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    metric: str = Field(min_length=1, max_length=240)
    datasetRole: DatasetRole = "test"
    direction: Literal["minimize", "maximize", "report-only"] = "report-only"
    threshold: Optional[float] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)


class ResourceBudget(BaseModel):
    maxWallMinutes: int = Field(default=60, ge=1, le=525600)
    maxCpuHours: float = Field(default=24.0, ge=0.0)
    maxGpuHours: float = Field(default=0.0, ge=0.0)
    maxCostUsd: float = Field(default=0.0, ge=0.0)
    maxRuns: int = Field(default=1, ge=1, le=100000)
    notes: str = Field(default="", max_length=4000)


class AIExperimentRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    experimentKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    mode: ExperimentMode
    model: ModelReference
    datasets: List[DatasetBinding] = Field(default_factory=list, max_length=100)
    environment: AIEnvironment = Field(default_factory=AIEnvironment)
    training: TrainingConfiguration = Field(default_factory=TrainingConfiguration)
    inference: InferenceConfiguration = Field(default_factory=InferenceConfiguration)
    evaluationHooks: List[EvaluationHook] = Field(default_factory=list, max_length=100)
    budget: ResourceBudget = Field(default_factory=ResourceBudget)
    inputContract: Dict[str, Any] = Field(default_factory=dict)
    outputContract: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list, max_length=64)
    notes: str = Field(default="", max_length=12000)
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def validate_mode(self):
        self.projectKey = self.projectKey.strip()
        self.experimentKey = self.experimentKey.strip()
        self.title = self.title.strip()
        roles = [d.role for d in self.datasets]
        if self.mode in {"training", "hybrid", "scientific-ml"}:
            if not self.training.enabled:
                raise ValueError("training configuration must be enabled for training/hybrid/scientific-ml mode")
            if "train" not in roles:
                raise ValueError("a train dataset binding is required for training/hybrid/scientific-ml mode")
        if self.mode in {"inference", "hybrid", "scientific-ml"} and not self.inference.enabled:
            raise ValueError("inference configuration must be enabled for inference/hybrid/scientific-ml mode")
        if self.mode == "evaluation" and not self.evaluationHooks:
            raise ValueError("evaluation mode requires at least one evaluation hook")
        dedupe = set()
        for d in self.datasets:
            key = (d.role, d.datasetRef, d.datasetHash)
            if key in dedupe:
                raise ValueError("duplicate dataset binding")
            dedupe.add(key)
        self.tags = sorted({t.strip() for t in self.tags if t.strip()})
        return self


class SaveAIExperimentRequest(AIExperimentRequest):
    pass


class ExecutionPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    experimentHash: str = Field(min_length=64, max_length=64)
    requestedBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def validate_hash(self):
        self.experimentHash = self.experimentHash.lower()
        if not _is_hash(self.experimentHash):
            raise ValueError("experimentHash must be a 64-character hexadecimal SHA-256 hash")
        return self


class CoreAIPlanRequest(ExecutionPlanRequest):
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"


def runtime_contracts() -> Dict[str, Any]:
    contracts = [
        {
            "adapterKind": "local-model",
            "providers": ["local", "workspace-ml", "custom"],
            "modes": ["training", "inference", "evaluation", "hybrid", "scientific-ml"],
            "executionImplemented": False,
            "notes": "Contract reserved for explicit local/Workspace ML adapters in later v10 builds.",
        },
        {
            "adapterKind": "provider-api",
            "providers": ["openai-compatible", "huggingface", "custom"],
            "modes": ["inference", "evaluation", "hybrid"],
            "executionImplemented": False,
            "notes": "Network/provider execution is not authorized by the v10.0 foundation.",
        },
    ]
    out = {"ok": True, "schema": RUNTIME_CONTRACT_SCHEMA, "version": VERSION, "contracts": contracts}
    out["contractHash"] = content_hash(out)
    return out


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Scientific AI Engineering Runtime Foundation",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "experimentSchema": EXPERIMENT_SCHEMA,
        "providerKinds": list(AIProvider.__args__),
        "taskKinds": list(AITask.__args__),
        "experimentModes": list(ExperimentMode.__args__),
        "datasetRoles": list(DatasetRole.__args__),
        "capabilities": {
            "scientificAIEngineeringRuntimeFoundation": True,
            "contentAddressedAIExperimentSpecifications": True,
            "explicitModelProviderRuntimeContracts": True,
            "datasetLineageBindings": True,
            "deterministicSeedConfiguration": True,
            "trainingConfigurationContracts": True,
            "inferenceConfigurationContracts": True,
            "evaluationHookContracts": True,
            "resourceBudgetContracts": True,
            "environmentReproducibilityMetadata": True,
            "neutralAIExecutionPlanning": True,
            "platformCoreAIExperimentPlanning": True,
        },
        "boundaries": {
            "automaticModelDownload": False,
            "automaticTrainingExecution": False,
            "automaticInferenceExecution": False,
            "externalProviderCallsAuthorized": False,
            "arbitraryCodeExecutionAuthorized": False,
            "hiddenAgentExecutionAuthorized": False,
            "automaticModelSelection": False,
            "automaticScientificInterpretation": False,
            "scientificValidityInferred": False,
            "automaticCoreDispatch": False,
            "automaticCorePersistence": False,
            "governedCoreObjectCreated": False,
        },
    }
    out["manifestHash"] = content_hash(out)
    return out


def _canonical_experiment(req: AIExperimentRequest) -> Dict[str, Any]:
    payload = req.model_dump(mode="json")
    payload["datasets"] = sorted(
        payload["datasets"],
        key=lambda x: (x.get("role", ""), x.get("datasetRef", ""), x.get("datasetHash", "")),
    )
    payload["evaluationHooks"] = sorted(
        payload["evaluationHooks"], key=lambda x: (x.get("name", ""), x.get("metric", ""), x.get("datasetRole", ""))
    )
    payload["tags"] = sorted(set(payload.get("tags", [])))
    return payload


def compose_experiment(req: AIExperimentRequest) -> Dict[str, Any]:
    canonical = _canonical_experiment(req)
    experiment_hash = content_hash({"schema": EXPERIMENT_SCHEMA, "experiment": canonical})
    deterministic = bool(req.training.deterministicRequested and req.inference.deterministicRequested)
    return {
        "ok": True,
        "schema": EXPERIMENT_SCHEMA,
        "version": VERSION,
        "experimentHash": experiment_hash,
        "experimentRef": f"sc://workbench/ai-engineering-experiment/{experiment_hash}",
        "projectKey": req.projectKey,
        "experimentKey": req.experimentKey,
        "title": req.title,
        "mode": req.mode,
        "experiment": canonical,
        "lineage": {
            "modelArtifactHash": req.model.artifactHash or None,
            "datasetHashes": [d.datasetHash for d in req.datasets if d.datasetHash],
            "dependencyLockHash": req.environment.dependencyLockHash or None,
        },
        "reproducibility": {
            "explicitTrainingSeed": req.training.seed,
            "explicitInferenceSeed": req.inference.seed,
            "deterministicRequested": deterministic,
            "contentAddressedSpecification": True,
            "environmentFullyPinned": bool(req.environment.containerImage or req.environment.dependencyLockHash),
        },
        "boundaries": manifest()["boundaries"],
    }


def save_experiment(req: SaveAIExperimentRequest) -> Dict[str, Any]:
    record = compose_experiment(req)
    path = _experiment_path(req.projectKey, record["experimentHash"])
    idempotent = path.exists()
    if not idempotent:
        stored = {**record, "createdAt": _now(), "createdBy": req.createdBy}
        stored["recordHash"] = content_hash({k: v for k, v in stored.items() if k != "recordHash"})
        _atomic_json_write(path, stored)
    else:
        stored = load_experiment(req.projectKey, record["experimentHash"])
    return {**stored, "idempotent": idempotent}


def load_experiment(project_key: str, experiment_hash: str) -> Dict[str, Any]:
    if not _is_hash(experiment_hash):
        raise HTTPException(status_code=422, detail="invalid experiment hash")
    path = _experiment_path(project_key, experiment_hash.lower())
    if not path.exists():
        raise HTTPException(status_code=404, detail="AI engineering experiment not found")
    record = _json_read(path)
    expected = record.get("recordHash")
    computed = content_hash({k: v for k, v in record.items() if k != "recordHash"})
    if expected != computed:
        raise HTTPException(status_code=409, detail="AI engineering experiment record integrity failure")
    return record


def list_experiments(project_key: str) -> Dict[str, Any]:
    root = _experiment_dir(project_key)
    rows: List[Dict[str, Any]] = []
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                d = load_experiment(project_key, path.stem)
                rows.append({
                    "experimentHash": d.get("experimentHash"), "experimentKey": d.get("experimentKey"),
                    "title": d.get("title"), "mode": d.get("mode"), "createdAt": d.get("createdAt"),
                    "modelId": d.get("experiment", {}).get("model", {}).get("modelId"),
                    "provider": d.get("experiment", {}).get("model", {}).get("provider"),
                    "recordHash": d.get("recordHash"),
                })
            except Exception:
                rows.append({"experimentHash": path.stem, "integrityError": True})
    return {"ok": True, "schema": CATALOG_SCHEMA, "version": VERSION, "projectKey": project_key,
            "experimentCount": len(rows), "experiments": rows}


def execution_plan(req: ExecutionPlanRequest) -> Dict[str, Any]:
    record = load_experiment(req.projectKey, req.experimentHash)
    exp = record["experiment"]
    mode = record["mode"]
    operations: List[Dict[str, Any]] = []
    if mode in {"training", "hybrid", "scientific-ml"}:
        operations.append({
            "operation": "train-model", "adapterKind": "local-model",
            "configuration": exp["training"], "datasetRoles": [d["role"] for d in exp["datasets"] if d["role"] in {"train", "validation"}],
            "authorized": False,
        })
    if mode in {"inference", "hybrid", "scientific-ml"}:
        operations.append({
            "operation": "run-inference", "adapterKind": "provider-or-local-model",
            "configuration": exp["inference"], "datasetRoles": [d["role"] for d in exp["datasets"] if d["role"] in {"inference", "test", "reference"}],
            "authorized": False,
        })
    if mode == "evaluation" or exp["evaluationHooks"]:
        operations.append({
            "operation": "evaluate-model", "adapterKind": "evaluation-runtime",
            "hooks": exp["evaluationHooks"], "authorized": False,
        })
    out = {
        "ok": True, "schema": EXECUTION_PLAN_SCHEMA, "version": VERSION,
        "projectKey": req.projectKey, "experimentHash": req.experimentHash,
        "experimentRef": record["experimentRef"], "requestedBy": req.requestedBy,
        "runtimeKind": "ai-engineering", "operations": operations,
        "budget": exp["budget"], "environment": exp["environment"],
        "model": exp["model"], "datasets": exp["datasets"],
        "executionAuthorized": False,
        "boundaries": {
            "automaticExecution": False, "providerCallPerformed": False, "modelDownloadPerformed": False,
            "trainingPerformed": False, "inferencePerformed": False, "scientificValidityInferred": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


def core_plan(req: CoreAIPlanRequest) -> Dict[str, Any]:
    record = load_experiment(req.projectKey, req.experimentHash)
    cfg = core_config()
    out = {
        "ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION,
        "bindingPlan": {
            "objectType": "workbench.ai-engineering-experiment",
            "sourceRef": record["experimentRef"], "sourceHash": record["experimentHash"],
            "recordHash": record.get("recordHash"), "projectKey": req.projectKey,
            "modelProvider": record["experiment"]["model"]["provider"],
            "modelId": record["experiment"]["model"]["modelId"], "mode": record["mode"],
            "coreProjectEntityId": req.coreProjectEntityId, "coreSessionId": req.coreSessionId,
            "visibility": req.visibility, "createdBy": req.requestedBy,
        },
        "coreConfiguration": {
            "enabled": cfg.get("enabled"), "required": cfg.get("required"),
            "outboundDispatchEnabled": cfg.get("outboundDispatchEnabled"),
        },
        "boundaries": {
            "automaticCoreDispatch": False, "automaticCorePersistence": False,
            "governedCoreObjectCreated": False, "scientificValidityInferred": False,
            "automaticModelSelection": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


@router.get("/ai-engineering/manifest")
def ai_manifest() -> Dict[str, Any]:
    return manifest()


@router.get("/ai-engineering/runtime-contracts")
def ai_runtime_contracts() -> Dict[str, Any]:
    return runtime_contracts()


@router.post("/ai-engineering/compose")
def ai_compose(req: AIExperimentRequest) -> Dict[str, Any]:
    return compose_experiment(req)


@router.post("/ai-engineering/experiments")
def ai_save(req: SaveAIExperimentRequest) -> Dict[str, Any]:
    return save_experiment(req)


@router.get("/ai-engineering/experiments/{project_key}")
def ai_list(project_key: str) -> Dict[str, Any]:
    return list_experiments(project_key)


@router.get("/ai-engineering/experiments/{project_key}/{experiment_hash}")
def ai_get(project_key: str, experiment_hash: str) -> Dict[str, Any]:
    return load_experiment(project_key, experiment_hash)


@router.post("/ai-engineering/execution-plan")
def ai_execution_plan(req: ExecutionPlanRequest) -> Dict[str, Any]:
    return execution_plan(req)


@router.post("/integration/core/ai-engineering/plan")
def ai_core_plan(req: CoreAIPlanRequest) -> Dict[str, Any]:
    return core_plan(req)


@router.get("/v1000/status")
def status() -> Dict[str, Any]:
    m = manifest()
    return {
        "ok": True, "schema": SCHEMA, "version": VERSION, "release": m["release"],
        "scientificAIEngineeringRuntimeFoundation": True,
        "contentAddressedAIExperimentSpecifications": True,
        "neutralAIExecutionPlanning": True,
        "automaticTrainingExecution": False,
        "automaticInferenceExecution": False,
        "hiddenAgentExecutionAuthorized": False,
        "scientificValidityInferred": False,
        "automaticCoreDispatch": False,
        "manifestHash": m["manifestHash"],
    }

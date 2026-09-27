"""Workbench v10.2.0 — Training & Fine-Tuning Experiment Runtime.

Registry-backed, content-addressed training/fine-tuning run specifications for Sustainable
Catalyst Workbench. The runtime validates v10.0 AI experiment intent against v10.1 model
and dataset registry bindings, captures deterministic training hyperparameters, fine-tuning
method configuration, runtime/environment identity, checkpoint policy, evaluation schedule,
resource budgets, append-only progress events, immutable training results, derived-model
registration plans, and Platform Core handoff plans.

v10.2.0 intentionally does not download models or datasets, execute arbitrary code, start
training automatically, call external providers automatically, promote checkpoints/models,
select a preferred model, infer scientific validity, or create governed Platform Core
objects automatically. Concrete execution adapters can consume the explicit plan contract.
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
from .v1000 import DatasetRole, load_experiment
from .v1010 import _load_record as load_registry_record

VERSION = APP_VERSION
SCHEMA = "sc-workbench-training-finetuning-experiment-runtime/1.0"
RUN_SCHEMA = "sc-workbench-ai-training-run/1.0"
EVENT_SCHEMA = "sc-workbench-ai-training-progress-event/1.0"
RESULT_SCHEMA = "sc-workbench-ai-training-result/1.0"
EXECUTION_PLAN_SCHEMA = "sc-workbench-ai-training-execution-plan/1.0"
REGISTRY_PLAN_SCHEMA = "sc-workbench-derived-model-registry-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-ai-training-core-plan/1.0"
router = APIRouter(tags=["workbench-v1020-training-finetuning-experiment-runtime"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")
FineTuneMethod = Literal[
    "full-finetune", "supervised-finetuning", "continued-pretraining", "lora", "qlora",
    "adapter", "prompt-tuning", "linear-probe", "custom"
]
RuntimeAdapter = Literal["local-python", "workspace-ml", "container", "external", "custom"]
TrainingEventType = Literal[
    "start", "progress", "evaluation", "checkpoint", "warning", "failure", "completion", "cancelled"
]
TrainingResultStatus = Literal["completed", "failed", "cancelled"]
CoreTrainingKind = Literal["training-run", "training-result"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


def _project_root(project_key: str) -> Path:
    return _store_root() / "ai-training-finetuning" / _stable_id(project_key)


def _run_dir(project_key: str) -> Path:
    return _project_root(project_key) / "runs"


def _run_path(project_key: str, run_hash: str) -> Path:
    return _run_dir(project_key) / f"{run_hash}.json"


def _events_dir(project_key: str, run_hash: str) -> Path:
    return _project_root(project_key) / "events" / run_hash


def _results_dir(project_key: str, run_hash: str) -> Path:
    return _project_root(project_key) / "results" / run_hash


class FineTuningConfiguration(BaseModel):
    method: FineTuneMethod = "supervised-finetuning"
    trainableParameterPolicy: Literal["all", "adapters-only", "head-only", "prompt-only", "custom"] = "all"
    targetModules: List[str] = Field(default_factory=list, max_length=256)
    loraRank: int = Field(default=8, ge=1, le=4096)
    loraAlpha: float = Field(default=16.0, gt=0.0)
    loraDropout: float = Field(default=0.0, ge=0.0, le=1.0)
    quantizationBits: Optional[Literal[4, 8, 16]] = None
    freezeBaseModel: bool = False
    customConfiguration: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_method(self):
        self.targetModules = sorted({x.strip() for x in self.targetModules if x.strip()})
        if self.method in {"lora", "qlora", "adapter", "prompt-tuning", "linear-probe"} and self.trainableParameterPolicy == "all":
            raise ValueError("parameter-efficient fine-tuning methods must not use trainableParameterPolicy=all")
        if self.method == "qlora" and self.quantizationBits not in {4, 8}:
            raise ValueError("qlora requires quantizationBits of 4 or 8")
        if self.method == "full-finetune" and self.freezeBaseModel:
            raise ValueError("full-finetune cannot freeze the base model")
        return self


class TrainingHyperparameters(BaseModel):
    seed: int = Field(default=0, ge=0, le=2**31 - 1)
    epochs: int = Field(default=1, ge=1, le=100000)
    maxSteps: int = Field(default=0, ge=0, le=10**9)
    batchSize: int = Field(default=1, ge=1, le=1000000)
    gradientAccumulationSteps: int = Field(default=1, ge=1, le=1000000)
    learningRate: float = Field(default=0.0001, gt=0.0)
    optimizer: str = Field(default="adamw", max_length=160)
    scheduler: str = Field(default="constant", max_length=160)
    weightDecay: float = Field(default=0.0, ge=0.0)
    warmupSteps: int = Field(default=0, ge=0)
    maxGradientNorm: float = Field(default=1.0, gt=0.0)
    gradientCheckpointing: bool = False
    deterministicRequested: bool = True


class EvaluationSchedule(BaseModel):
    enabled: bool = True
    everySteps: int = Field(default=100, ge=1)
    datasetRole: DatasetRole = "validation"
    metrics: List[str] = Field(default_factory=list, max_length=100)
    trackingMetric: str = Field(default="", max_length=240)
    direction: Literal["minimize", "maximize", "report-only"] = "report-only"
    automaticEarlyStopping: bool = False

    @model_validator(mode="after")
    def normalize(self):
        self.metrics = sorted({x.strip() for x in self.metrics if x.strip()})
        self.trackingMetric = self.trackingMetric.strip()
        return self


class CheckpointPolicy(BaseModel):
    enabled: bool = True
    everySteps: int = Field(default=500, ge=1)
    maxRetained: int = Field(default=5, ge=1, le=10000)
    saveOptimizerState: bool = True
    artifactPrefix: str = Field(default="checkpoint", max_length=160)
    finalCheckpointRequired: bool = True


class TrainingEnvironment(BaseModel):
    adapter: RuntimeAdapter = "workspace-ml"
    environmentRef: str = Field(default="", max_length=1000)
    containerImage: str = Field(default="", max_length=1000)
    dependencyLockHash: str = Field(default="", max_length=64)
    accelerator: Literal["cpu", "cuda", "mps", "tpu", "external", "unspecified"] = "unspecified"
    precision: str = Field(default="", max_length=80)
    networkAccessAllowed: bool = False

    @model_validator(mode="after")
    def validate_hash(self):
        self.environmentRef = self.environmentRef.strip()
        self.containerImage = self.containerImage.strip()
        self.dependencyLockHash = self.dependencyLockHash.strip().lower()
        if self.dependencyLockHash and not _is_hash(self.dependencyLockHash):
            raise ValueError("dependencyLockHash must be a 64-character hexadecimal SHA-256 hash")
        return self


class TrainingBudget(BaseModel):
    maxWallMinutes: int = Field(default=120, ge=1, le=525600)
    maxCpuHours: float = Field(default=24.0, ge=0.0)
    maxGpuHours: float = Field(default=0.0, ge=0.0)
    maxCostUsd: float = Field(default=0.0, ge=0.0)
    maxCheckpoints: int = Field(default=20, ge=1, le=100000)
    notes: str = Field(default="", max_length=4000)


class TrainingRunRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    trainingKey: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=500)
    experimentHash: str = Field(min_length=64, max_length=64)
    registryBindingHash: str = Field(min_length=64, max_length=64)
    baseModelRecordHash: str = Field(min_length=64, max_length=64)
    fineTuning: FineTuningConfiguration = Field(default_factory=FineTuningConfiguration)
    hyperparameters: TrainingHyperparameters = Field(default_factory=TrainingHyperparameters)
    evaluation: EvaluationSchedule = Field(default_factory=EvaluationSchedule)
    checkpoints: CheckpointPolicy = Field(default_factory=CheckpointPolicy)
    environment: TrainingEnvironment = Field(default_factory=TrainingEnvironment)
    budget: TrainingBudget = Field(default_factory=TrainingBudget)
    outputModelKey: str = Field(min_length=1, max_length=160)
    outputVersionLabel: str = Field(min_length=1, max_length=160)
    tags: List[str] = Field(default_factory=list, max_length=64)
    notes: str = Field(default="", max_length=12000)
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        for attr in ("projectKey", "trainingKey", "title", "outputModelKey", "outputVersionLabel"):
            setattr(self, attr, getattr(self, attr).strip())
        for attr in ("experimentHash", "registryBindingHash", "baseModelRecordHash"):
            value = getattr(self, attr).strip().lower()
            if not _is_hash(value):
                raise ValueError(f"{attr} must be a 64-character hexadecimal SHA-256 hash")
            setattr(self, attr, value)
        self.tags = sorted({x.strip() for x in self.tags if x.strip()})
        return self


class TrainingExecutionPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    runHash: str = Field(min_length=64, max_length=64)
    requestedBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def validate_hash(self):
        self.runHash = self.runHash.lower()
        if not _is_hash(self.runHash):
            raise ValueError("runHash must be a SHA-256 hash")
        return self


class TrainingProgressEventRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    runHash: str = Field(min_length=64, max_length=64)
    sequence: int = Field(ge=1, le=10**9)
    eventType: TrainingEventType
    step: Optional[int] = Field(default=None, ge=0)
    epoch: Optional[float] = Field(default=None, ge=0.0)
    metrics: Dict[str, float] = Field(default_factory=dict)
    checkpointArtifactHash: str = Field(default="", max_length=64)
    sourceJobId: str = Field(default="", max_length=255)
    sourceResultHash: str = Field(default="", max_length=64)
    message: str = Field(default="", max_length=8000)
    recordedBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        self.runHash = self.runHash.lower()
        if not _is_hash(self.runHash):
            raise ValueError("runHash must be a SHA-256 hash")
        self.checkpointArtifactHash = self.checkpointArtifactHash.strip().lower()
        self.sourceResultHash = self.sourceResultHash.strip().lower()
        if self.checkpointArtifactHash and not _is_hash(self.checkpointArtifactHash):
            raise ValueError("checkpointArtifactHash must be a SHA-256 hash")
        if self.sourceResultHash and not _is_hash(self.sourceResultHash):
            raise ValueError("sourceResultHash must be a SHA-256 hash")
        if self.eventType == "checkpoint" and not self.checkpointArtifactHash:
            raise ValueError("checkpoint events require checkpointArtifactHash")
        return self


class TrainingResultRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    runHash: str = Field(min_length=64, max_length=64)
    status: TrainingResultStatus
    finalModelArtifactHash: str = Field(default="", max_length=64)
    finalCheckpointArtifactHash: str = Field(default="", max_length=64)
    metrics: Dict[str, float] = Field(default_factory=dict)
    sourceJobId: str = Field(default="", max_length=255)
    sourceResultHash: str = Field(default="", max_length=64)
    notes: str = Field(default="", max_length=12000)
    completedBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def normalize(self):
        self.runHash = self.runHash.lower()
        if not _is_hash(self.runHash):
            raise ValueError("runHash must be a SHA-256 hash")
        for attr in ("finalModelArtifactHash", "finalCheckpointArtifactHash", "sourceResultHash"):
            value = getattr(self, attr).strip().lower()
            if value and not _is_hash(value):
                raise ValueError(f"{attr} must be a SHA-256 hash")
            setattr(self, attr, value)
        if self.status == "completed" and not self.finalModelArtifactHash:
            raise ValueError("completed training result requires finalModelArtifactHash")
        return self


class DerivedModelPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    runHash: str = Field(min_length=64, max_length=64)
    resultHash: str = Field(min_length=64, max_length=64)
    title: str = Field(min_length=1, max_length=500)
    license: str = Field(default="", max_length=500)
    licenseUri: str = Field(default="", max_length=1000)
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def validate_hashes(self):
        for attr in ("runHash", "resultHash"):
            value = getattr(self, attr).lower()
            if not _is_hash(value):
                raise ValueError(f"{attr} must be a SHA-256 hash")
            setattr(self, attr, value)
        return self


class CoreTrainingPlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=160)
    kind: CoreTrainingKind
    sourceHash: str = Field(min_length=64, max_length=64)
    runHash: str = Field(default="", max_length=64)
    coreProjectEntityId: str = Field(default="", max_length=255)
    coreSessionId: str = Field(default="", max_length=255)
    visibility: Literal["private", "internal", "public"] = "internal"
    createdBy: str = Field(default="workbench", max_length=160)

    @model_validator(mode="after")
    def validate_hashes(self):
        self.sourceHash = self.sourceHash.lower()
        self.runHash = self.runHash.lower()
        if not _is_hash(self.sourceHash):
            raise ValueError("sourceHash must be a SHA-256 hash")
        if self.runHash and not _is_hash(self.runHash):
            raise ValueError("runHash must be a SHA-256 hash")
        return self


def manifest() -> Dict[str, Any]:
    out = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Training & Fine-Tuning Experiment Runtime",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "runSchema": RUN_SCHEMA,
        "eventSchema": EVENT_SCHEMA,
        "resultSchema": RESULT_SCHEMA,
        "capabilities": {
            "trainingFineTuningExperimentRuntime": True,
            "registryBackedTrainingRuns": True,
            "fullAndParameterEfficientFineTuning": True,
            "loraAndQloraConfiguration": True,
            "deterministicTrainingManifests": True,
            "trainingResourceBudgets": True,
            "checkpointLineage": True,
            "appendOnlyTrainingProgressEvents": True,
            "immutableTrainingResults": True,
            "externalJobAndResultLineage": True,
            "derivedModelRegistrationPlanning": True,
            "platformCoreTrainingPlanning": True,
        },
        "boundaries": {
            "automaticModelDownload": False,
            "automaticDatasetDownload": False,
            "automaticTrainingExecution": False,
            "arbitraryCodeExecution": False,
            "automaticExternalProviderCall": False,
            "automaticCheckpointPromotion": False,
            "automaticRegistryPromotion": False,
            "automaticPreferredModelSelection": False,
            "automaticScientificInterpretation": False,
            "scientificValidityInferred": False,
            "automaticCoreDispatch": False,
            "automaticCorePersistence": False,
            "governedCoreObjectCreated": False,
        },
        "fineTuningMethods": [
            "full-finetune", "supervised-finetuning", "continued-pretraining", "lora", "qlora",
            "adapter", "prompt-tuning", "linear-probe", "custom"
        ],
        "runtimeAdapters": ["local-python", "workspace-ml", "container", "external", "custom"],
    }
    out["manifestHash"] = content_hash(out)
    return out


def _load_run(project_key: str, run_hash: str) -> Dict[str, Any]:
    if not _is_hash(run_hash):
        raise HTTPException(status_code=422, detail="invalid training run hash")
    path = _run_path(project_key, run_hash.lower())
    if not path.exists():
        raise HTTPException(status_code=404, detail="training run not found")
    row = _json_read(path)
    expected = content_hash({"schema": RUN_SCHEMA, "run": row.get("run") or {}})
    if row.get("runHash") != expected:
        raise HTTPException(status_code=409, detail="training run integrity failure")
    return row


def _canonical_run(req: TrainingRunRequest) -> Dict[str, Any]:
    exp = load_experiment(req.projectKey, req.experimentHash)
    binding = load_registry_record(req.projectKey, "experiment-binding", req.registryBindingHash)
    model = load_registry_record(req.projectKey, "model", req.baseModelRecordHash)
    issues: List[Dict[str, Any]] = []

    experiment = exp.get("experiment") or {}
    if experiment.get("mode") not in {"training", "hybrid", "scientific-ml"}:
        issues.append({"code": "experiment-mode-not-training-capable", "mode": experiment.get("mode")})
    if not (experiment.get("training") or {}).get("enabled"):
        issues.append({"code": "experiment-training-disabled"})

    b = binding.get("binding") or {}
    if b.get("experimentHash") != req.experimentHash:
        issues.append({"code": "registry-binding-experiment-mismatch"})
    if b.get("modelRecordHash") != req.baseModelRecordHash:
        issues.append({"code": "registry-binding-model-mismatch"})
    if model.get("recordHash") != req.baseModelRecordHash:
        issues.append({"code": "base-model-record-mismatch"})

    datasets = b.get("datasets") or []
    train_datasets = [x for x in datasets if x.get("role") == "train"]
    if not train_datasets:
        issues.append({"code": "training-dataset-binding-missing"})
    if req.evaluation.enabled:
        eval_matches = [x for x in datasets if x.get("role") == req.evaluation.datasetRole]
        if not eval_matches and req.evaluation.datasetRole != "train":
            issues.append({"code": "evaluation-dataset-binding-missing", "role": req.evaluation.datasetRole})

    run = {
        "projectKey": req.projectKey,
        "trainingKey": req.trainingKey,
        "title": req.title,
        "experimentHash": req.experimentHash,
        "experimentRef": exp.get("experimentRef"),
        "registryBindingHash": req.registryBindingHash,
        "registryBindingRef": binding.get("recordRef"),
        "baseModelRecordHash": req.baseModelRecordHash,
        "baseModelRecordRef": model.get("recordRef"),
        "baseModel": {
            "modelKey": model.get("modelKey"), "versionLabel": model.get("versionLabel"),
            "provider": model.get("provider"), "modelId": model.get("modelId"),
            "task": model.get("task"), "artifactHash": model.get("artifactHash"),
        },
        "datasets": sorted(datasets, key=lambda x: (str(x.get("role") or ""), str(x.get("datasetRecordHash") or ""))),
        "fineTuning": req.fineTuning.model_dump(mode="json"),
        "hyperparameters": req.hyperparameters.model_dump(mode="json"),
        "evaluation": req.evaluation.model_dump(mode="json"),
        "checkpoints": req.checkpoints.model_dump(mode="json"),
        "environment": req.environment.model_dump(mode="json"),
        "budget": req.budget.model_dump(mode="json"),
        "outputModelKey": req.outputModelKey,
        "outputVersionLabel": req.outputVersionLabel,
        "tags": req.tags,
        "notes": req.notes,
    }
    return {"run": run, "issues": issues}


def compose_training_run(req: TrainingRunRequest) -> Dict[str, Any]:
    built = _canonical_run(req)
    run = built["run"]
    run_hash = content_hash({"schema": RUN_SCHEMA, "run": run})
    return {
        "ok": True, "schema": RUN_SCHEMA, "version": VERSION,
        "runHash": run_hash, "runRef": f"sc://workbench/ai-training/run/{run_hash}",
        "run": run, "trainingReady": not built["issues"], "issues": built["issues"],
        "boundaries": {
            "automaticTrainingExecution": False, "arbitraryCodeExecution": False,
            "automaticModelDownload": False, "automaticDatasetDownload": False,
            "automaticRegistryPromotion": False, "scientificValidityInferred": False,
        },
    }


def save_training_run(req: TrainingRunRequest) -> Dict[str, Any]:
    record = compose_training_run(req)
    if not record["trainingReady"]:
        raise HTTPException(status_code=409, detail={"message": "training run is not ready", "issues": record["issues"]})
    path = _run_path(req.projectKey, record["runHash"])
    idempotent = path.exists()
    if not idempotent:
        stored = {
            **record, "createdAt": _now(), "createdBy": req.createdBy,
            "immutability": {"contentAddressed": True, "runSpecMutable": False, "progressEventsAppendOnly": True},
        }
        _atomic_json_write(path, stored)
    else:
        stored = _load_run(req.projectKey, record["runHash"])
    return {**stored, "idempotent": idempotent}


def list_training_runs(project_key: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    root = _run_dir(project_key)
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                r = _load_run(project_key, path.stem)
                x = r.get("run") or {}
                rows.append({
                    "runHash": r["runHash"], "runRef": r["runRef"], "trainingKey": x.get("trainingKey"),
                    "title": x.get("title"), "experimentHash": x.get("experimentHash"),
                    "baseModelRecordHash": x.get("baseModelRecordHash"), "fineTuningMethod": (x.get("fineTuning") or {}).get("method"),
                    "outputModelKey": x.get("outputModelKey"), "outputVersionLabel": x.get("outputVersionLabel"),
                    "createdAt": r.get("createdAt"),
                })
            except Exception:
                rows.append({"runHash": path.stem, "integrityError": True})
    return {"ok": True, "schema": RUN_SCHEMA, "version": VERSION, "projectKey": project_key,
            "runCount": len(rows), "runs": rows}


def training_execution_plan(req: TrainingExecutionPlanRequest) -> Dict[str, Any]:
    stored = _load_run(req.projectKey, req.runHash)
    run = stored["run"]
    out = {
        "ok": True, "schema": EXECUTION_PLAN_SCHEMA, "version": VERSION,
        "runHash": req.runHash, "runRef": stored["runRef"],
        "authorized": False,
        "adapterContract": {
            "adapter": (run.get("environment") or {}).get("adapter"),
            "environment": run.get("environment"),
            "baseModel": run.get("baseModel"),
            "datasets": run.get("datasets"),
            "fineTuning": run.get("fineTuning"),
            "hyperparameters": run.get("hyperparameters"),
            "evaluation": run.get("evaluation"),
            "checkpoints": run.get("checkpoints"),
            "budget": run.get("budget"),
            "output": {"modelKey": run.get("outputModelKey"), "versionLabel": run.get("outputVersionLabel")},
        },
        "requestedBy": req.requestedBy,
        "boundaries": {
            "automaticTrainingExecution": False, "executionRequiresExplicitAuthorization": True,
            "arbitraryCodeExecution": False, "automaticExternalProviderCall": False,
            "automaticRegistryPromotion": False, "automaticPreferredModelSelection": False,
            "scientificValidityInferred": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


def append_training_event(req: TrainingProgressEventRequest) -> Dict[str, Any]:
    _load_run(req.projectKey, req.runHash)
    canonical = req.model_dump(mode="json")
    canonical.pop("recordedBy", None)
    event_hash = content_hash({"schema": EVENT_SCHEMA, "event": canonical})
    root = _events_dir(req.projectKey, req.runHash)
    root.mkdir(parents=True, exist_ok=True)
    prefix = f"{req.sequence:010d}-"
    existing = sorted(root.glob(prefix + "*.json"))
    if existing:
        row = _json_read(existing[0])
        if row.get("eventHash") != event_hash:
            raise HTTPException(status_code=409, detail="training event sequence already exists with different immutable content")
        return {**row, "idempotent": True}
    path = root / f"{prefix}{event_hash}.json"
    row = {
        "ok": True, "schema": EVENT_SCHEMA, "version": VERSION,
        "eventHash": event_hash, "eventRef": f"sc://workbench/ai-training/event/{event_hash}",
        "event": canonical, "recordedAt": _now(), "recordedBy": req.recordedBy,
        "immutability": {"appendOnly": True, "sequenceCollisionProtected": True},
    }
    _atomic_json_write(path, row)
    return {**row, "idempotent": False}


def list_training_events(project_key: str, run_hash: str) -> Dict[str, Any]:
    _load_run(project_key, run_hash)
    rows: List[Dict[str, Any]] = []
    root = _events_dir(project_key, run_hash)
    if root.exists():
        for path in sorted(root.glob("*.json")):
            try:
                row = _json_read(path)
                rows.append(row)
            except Exception:
                rows.append({"file": path.name, "integrityError": True})
    return {"ok": True, "schema": EVENT_SCHEMA, "version": VERSION, "projectKey": project_key,
            "runHash": run_hash, "eventCount": len(rows), "events": rows}


def _load_training_result(project_key: str, run_hash: str, result_hash: Optional[str] = None) -> Dict[str, Any]:
    _load_run(project_key, run_hash)
    root = _results_dir(project_key, run_hash)
    if not root.exists():
        raise HTTPException(status_code=404, detail="training result not found")
    files = sorted(root.glob("*.json"))
    if result_hash:
        if not _is_hash(result_hash):
            raise HTTPException(status_code=422, detail="invalid training result hash")
        files = [root / f"{result_hash.lower()}.json"]
    if not files or not files[0].exists():
        raise HTTPException(status_code=404, detail="training result not found")
    row = _json_read(files[0])
    expected = content_hash({"schema": RESULT_SCHEMA, "result": row.get("result") or {}})
    if row.get("resultHash") != expected:
        raise HTTPException(status_code=409, detail="training result integrity failure")
    return row


def save_training_result(req: TrainingResultRequest) -> Dict[str, Any]:
    stored_run = _load_run(req.projectKey, req.runHash)
    canonical = req.model_dump(mode="json")
    canonical.pop("completedBy", None)
    result = {
        **canonical,
        "runRef": stored_run["runRef"],
        "outputModelKey": stored_run["run"].get("outputModelKey"),
        "outputVersionLabel": stored_run["run"].get("outputVersionLabel"),
    }
    result_hash = content_hash({"schema": RESULT_SCHEMA, "result": result})
    root = _results_dir(req.projectKey, req.runHash)
    root.mkdir(parents=True, exist_ok=True)
    existing = sorted(root.glob("*.json"))
    if existing:
        row = _load_training_result(req.projectKey, req.runHash)
        if row.get("resultHash") != result_hash:
            raise HTTPException(status_code=409, detail="training run already has a different immutable result")
        return {**row, "idempotent": True}
    path = root / f"{result_hash}.json"
    row = {
        "ok": True, "schema": RESULT_SCHEMA, "version": VERSION,
        "resultHash": result_hash, "resultRef": f"sc://workbench/ai-training/result/{result_hash}",
        "result": result, "completedAt": _now(), "completedBy": req.completedBy,
        "immutability": {"contentAddressed": True, "replacementAllowed": False},
        "boundaries": {"automaticRegistryPromotion": False, "automaticPreferredModelSelection": False,
                       "scientificValidityInferred": False, "automaticCoreDispatch": False},
    }
    _atomic_json_write(path, row)
    return {**row, "idempotent": False}


def derived_model_registration_plan(req: DerivedModelPlanRequest) -> Dict[str, Any]:
    run = _load_run(req.projectKey, req.runHash)
    result = _load_training_result(req.projectKey, req.runHash, req.resultHash)
    rr = result.get("result") or {}
    if rr.get("status") != "completed" or not rr.get("finalModelArtifactHash"):
        raise HTTPException(status_code=409, detail="completed training result with finalModelArtifactHash is required")
    spec = run.get("run") or {}
    base = spec.get("baseModel") or {}
    model_record = {
        "projectKey": req.projectKey,
        "modelKey": spec.get("outputModelKey"),
        "versionLabel": spec.get("outputVersionLabel"),
        "title": req.title,
        "provider": base.get("provider") or "local",
        "modelId": f"sc://workbench/ai-training/result/{req.resultHash}",
        "task": base.get("task") or "custom",
        "artifactHash": rr.get("finalModelArtifactHash"),
        "sourceRevision": req.resultHash,
        "sourceUri": result.get("resultRef"),
        "license": req.license,
        "licenseUri": req.licenseUri,
        "provenance": {
            "derivedFromModelRecordHash": spec.get("baseModelRecordHash"),
            "trainingRunHash": req.runHash,
            "trainingResultHash": req.resultHash,
            "experimentHash": spec.get("experimentHash"),
            "registryBindingHash": spec.get("registryBindingHash"),
        },
        "tags": sorted(set((spec.get("tags") or []) + ["trained-model", "workbench-v10.2"])),
        "notes": "Registration plan generated by Workbench v10.2.0. Explicit v10.1 registry save is still required.",
        "createdBy": req.createdBy,
    }
    out = {
        "ok": True, "schema": REGISTRY_PLAN_SCHEMA, "version": VERSION,
        "runHash": req.runHash, "resultHash": req.resultHash,
        "modelRegistryRequest": model_record,
        "authorized": False,
        "boundaries": {
            "automaticRegistryPromotion": False, "automaticPreferredModelSelection": False,
            "automaticModelDeployment": False, "scientificValidityInferred": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


def core_training_plan(req: CoreTrainingPlanRequest) -> Dict[str, Any]:
    if req.kind == "training-run":
        source = _load_run(req.projectKey, req.sourceHash)
        source_ref = source.get("runRef")
        object_type = "workbench.ai-training-run"
        run_hash = req.sourceHash
    else:
        run_hash = req.runHash
        if not run_hash:
            raise HTTPException(status_code=422, detail="runHash is required for training-result Core plan")
        source = _load_training_result(req.projectKey, run_hash, req.sourceHash)
        source_ref = source.get("resultRef")
        object_type = "workbench.ai-training-result"
    cfg = core_config()
    out = {
        "ok": True, "schema": CORE_PLAN_SCHEMA, "version": VERSION,
        "bindingPlan": {
            "objectType": object_type, "sourceRef": source_ref, "sourceHash": req.sourceHash,
            "runHash": run_hash, "projectKey": req.projectKey,
            "coreProjectEntityId": req.coreProjectEntityId, "coreSessionId": req.coreSessionId,
            "visibility": req.visibility, "createdBy": req.createdBy,
        },
        "coreConfiguration": {"enabled": cfg.get("enabled"), "required": cfg.get("required"),
                              "outboundDispatchEnabled": cfg.get("outboundDispatchEnabled")},
        "boundaries": {
            "automaticCoreDispatch": False, "automaticCorePersistence": False,
            "governedCoreObjectCreated": False, "scientificValidityInferred": False,
            "automaticPreferredModelSelection": False,
        },
    }
    out["planHash"] = content_hash(out)
    return out


@router.get("/ai-training/manifest")
def ai_training_manifest() -> Dict[str, Any]: return manifest()

@router.post("/ai-training/compose")
def ai_training_compose(req: TrainingRunRequest) -> Dict[str, Any]: return compose_training_run(req)

@router.post("/ai-training/runs")
def ai_training_save_run(req: TrainingRunRequest) -> Dict[str, Any]: return save_training_run(req)

@router.get("/ai-training/runs/{project_key}")
def ai_training_list_runs(project_key: str) -> Dict[str, Any]: return list_training_runs(project_key)

@router.get("/ai-training/runs/{project_key}/{run_hash}")
def ai_training_get_run(project_key: str, run_hash: str) -> Dict[str, Any]: return _load_run(project_key, run_hash)

@router.post("/ai-training/execution-plan")
def ai_training_execution_plan(req: TrainingExecutionPlanRequest) -> Dict[str, Any]: return training_execution_plan(req)

@router.post("/ai-training/events")
def ai_training_append_event(req: TrainingProgressEventRequest) -> Dict[str, Any]: return append_training_event(req)

@router.get("/ai-training/events/{project_key}/{run_hash}")
def ai_training_list_events(project_key: str, run_hash: str) -> Dict[str, Any]: return list_training_events(project_key, run_hash)

@router.post("/ai-training/results")
def ai_training_save_result(req: TrainingResultRequest) -> Dict[str, Any]: return save_training_result(req)

@router.get("/ai-training/results/{project_key}/{run_hash}")
def ai_training_get_result(project_key: str, run_hash: str) -> Dict[str, Any]: return _load_training_result(project_key, run_hash)

@router.post("/ai-training/derived-model-plan")
def ai_training_derived_model_plan(req: DerivedModelPlanRequest) -> Dict[str, Any]: return derived_model_registration_plan(req)

@router.post("/integration/core/ai-training/plan")
def ai_training_core_plan(req: CoreTrainingPlanRequest) -> Dict[str, Any]: return core_training_plan(req)

@router.get("/v1020/status")
def status() -> Dict[str, Any]:
    m = manifest()
    return {
        "ok": True, "schema": SCHEMA, "version": VERSION, "release": m["release"],
        "trainingFineTuningExperimentRuntime": True, "registryBackedTrainingRuns": True,
        "checkpointLineage": True, "appendOnlyTrainingProgressEvents": True,
        "immutableTrainingResults": True, "derivedModelRegistrationPlanning": True,
        "automaticTrainingExecution": False, "automaticRegistryPromotion": False,
        "scientificValidityInferred": False, "automaticCoreDispatch": False,
        "manifestHash": m["manifestHash"],
    }

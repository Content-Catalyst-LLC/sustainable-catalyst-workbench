"""Workbench v10.8.0 — Scientific ML Workspace.

Defines reproducible scientific-machine-learning study specifications and result records:
surrogate/emulator models, physics/constraint-aware ML contracts, simulation-to-ML lineage,
hybrid mechanistic+ML workflows, scientific benchmark binding, uncertainty handoffs,
and Platform Core promotion planning.

This release is intentionally declarative. It does not train models automatically, execute
simulations, choose a preferred model, claim physical validity, or dispatch governed
Platform Core objects automatically.
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
from .v810 import _atomic_json_write, _json_read, _store_root

VERSION = APP_VERSION
SCHEMA = "sc-workbench-scientific-ml-workspace/1.0"
STUDY_SCHEMA = "sc-workbench-scientific-ml-study/1.0"
RESULT_SCHEMA = "sc-workbench-scientific-ml-result/1.0"
COMPARISON_SCHEMA = "sc-workbench-scientific-ml-comparison/1.0"
DIAGNOSTIC_SCHEMA = "sc-workbench-scientific-ml-diagnostic/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-scientific-ml-core-plan/1.0"

router = APIRouter(tags=["workbench-v1080-scientific-ml-workspace"])

_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")

TaskKind = Literal["regression", "classification", "forecasting", "field-prediction", "inverse-problem", "other"]
ScientificMLKind = Literal[
    "surrogate-model",
    "emulator",
    "physics-informed-contract",
    "constraint-aware-contract",
    "operator-learning-contract",
    "reduced-order-model",
    "hybrid-mechanistic-ml",
    "simulation-calibrated-ml",
]
ConstraintKind = Literal[
    "range",
    "monotonicity",
    "conservation",
    "symmetry",
    "boundary-condition",
    "initial-condition",
    "dimensional-consistency",
    "custom",
]
CoreObjectKind = Literal["study", "result", "comparison", "diagnostic"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _stable_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_hash(value: str) -> bool:
    return bool(_HASH_RE.match(value or ""))


def _project_root(project_key: str) -> Path:
    return _store_root() / "scientific-ml" / _stable_id(project_key)


def _study_dir(project_key: str) -> Path:
    return _project_root(project_key) / "studies"


def _study_path(project_key: str, study_hash: str) -> Path:
    return _study_dir(project_key) / f"{study_hash}.json"


def _result_dir(project_key: str, study_hash: str) -> Path:
    return _project_root(project_key) / "results" / study_hash


def _result_path(project_key: str, study_hash: str, result_hash: str) -> Path:
    return _result_dir(project_key, study_hash) / f"{result_hash}.json"


class ScientificVariable(BaseModel):
    key: str = Field(min_length=1, max_length=300)
    role: Literal["feature", "target", "parameter", "state", "coordinate", "control"]
    units: Optional[str] = Field(default=None, max_length=200)
    physicalQuantity: Optional[str] = Field(default=None, max_length=300)
    description: str = Field(default="", max_length=3000)


class ConstraintSpec(BaseModel):
    kind: ConstraintKind
    variableKeys: List[str] = Field(default_factory=list, max_length=1000)
    expression: Optional[str] = Field(default=None, max_length=10000)
    lower: Optional[float] = None
    upper: Optional[float] = None
    tolerance: Optional[float] = Field(default=None, ge=0.0)
    sourceReference: Optional[str] = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.lower is not None and self.upper is not None and self.upper < self.lower:
            raise ValueError("constraint upper must be >= lower")
        if self.kind == "range" and self.lower is None and self.upper is None:
            raise ValueError("range constraint requires lower and/or upper")
        return self


class SimulationBinding(BaseModel):
    simulationRecordHash: str
    simulatorName: Optional[str] = Field(default=None, max_length=300)
    simulatorVersion: Optional[str] = Field(default=None, max_length=300)
    parameterRecordHash: Optional[str] = None
    outputRecordHash: Optional[str] = None
    sampleCount: Optional[int] = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_hashes(self):
        for name in ("simulationRecordHash", "parameterRecordHash", "outputRecordHash"):
            value = getattr(self, name)
            if value is not None and not _is_hash(value):
                raise ValueError(f"{name} must be a SHA-256 digest")
        return self


class MechanisticBinding(BaseModel):
    modelRecordHash: str
    modelKind: Literal["ode", "pde", "algebraic", "network", "agent-based", "state-space", "custom"]
    equationReference: Optional[str] = Field(default=None, max_length=10000)
    parameterRecordHash: Optional[str] = None

    @model_validator(mode="after")
    def validate_hashes(self):
        for name in ("modelRecordHash", "parameterRecordHash"):
            value = getattr(self, name)
            if value is not None and not _is_hash(value):
                raise ValueError(f"{name} must be a SHA-256 digest")
        return self


class TrainingPlan(BaseModel):
    runtime: Optional[str] = Field(default=None, max_length=300)
    library: Optional[str] = Field(default=None, max_length=300)
    libraryVersion: Optional[str] = Field(default=None, max_length=300)
    optimizer: Optional[str] = Field(default=None, max_length=300)
    lossFunction: Optional[str] = Field(default=None, max_length=1000)
    epochs: Optional[int] = Field(default=None, ge=1)
    batchSize: Optional[int] = Field(default=None, ge=1)
    randomSeed: Optional[int] = None
    notes: str = Field(default="", max_length=10000)


class StudyRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    studyKey: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=500)

    scientificMLKind: ScientificMLKind
    taskKind: TaskKind

    datasetRecordHash: str
    representationHash: Optional[str] = None
    benchmarkRecordHash: Optional[str] = None
    sourceModelRecordHash: Optional[str] = None

    variables: List[ScientificVariable] = Field(default_factory=list, min_length=1, max_length=10000)
    constraints: List[ConstraintSpec] = Field(default_factory=list, max_length=10000)
    simulations: List[SimulationBinding] = Field(default_factory=list, max_length=10000)
    mechanisticModel: Optional[MechanisticBinding] = None

    trainingPlan: TrainingPlan = Field(default_factory=TrainingPlan)
    uncertaintyStudyHash: Optional[str] = None
    explainabilityStudyHash: Optional[str] = None

    objective: str = Field(default="", max_length=10000)
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_contract(self):
        for name in (
            "datasetRecordHash", "representationHash", "benchmarkRecordHash",
            "sourceModelRecordHash", "uncertaintyStudyHash", "explainabilityStudyHash"
        ):
            value = getattr(self, name)
            if value is not None and not _is_hash(value):
                raise ValueError(f"{name} must be a SHA-256 digest")

        keys = [v.key for v in self.variables]
        if len(set(keys)) != len(keys):
            raise ValueError("scientific variable keys must be unique")

        defined = set(keys)
        for constraint in self.constraints:
            unknown = [k for k in constraint.variableKeys if k not in defined]
            if unknown:
                raise ValueError(f"constraint references undefined variables: {unknown}")

        if self.scientificMLKind in {"simulation-calibrated-ml", "surrogate-model", "emulator"} and not self.simulations:
            raise ValueError(f"{self.scientificMLKind} requires at least one simulation binding")

        if self.scientificMLKind == "hybrid-mechanistic-ml" and self.mechanisticModel is None:
            raise ValueError("hybrid-mechanistic-ml requires mechanisticModel")

        if self.scientificMLKind in {"physics-informed-contract", "constraint-aware-contract"} and not self.constraints:
            raise ValueError(f"{self.scientificMLKind} requires at least one explicit constraint")

        return self


class ScientificMetric(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    value: float
    units: Optional[str] = Field(default=None, max_length=200)
    split: Optional[str] = Field(default=None, max_length=200)
    notes: str = Field(default="", max_length=2000)


class ConstraintCheck(BaseModel):
    kind: ConstraintKind
    passed: bool
    value: Optional[float] = None
    tolerance: Optional[float] = Field(default=None, ge=0.0)
    details: str = Field(default="", max_length=5000)


class ResultRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    studyHash: str
    runtime: str = Field(min_length=1, max_length=300)
    runtimeVersion: Optional[str] = Field(default=None, max_length=300)

    executionRecordHash: Optional[str] = None
    trainedModelRecordHash: Optional[str] = None
    predictionRecordHash: Optional[str] = None
    simulationOutputHash: Optional[str] = None

    metrics: List[ScientificMetric] = Field(default_factory=list, max_length=10000)
    constraintChecks: List[ConstraintCheck] = Field(default_factory=list, max_length=10000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list, max_length=1000)
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_hashes(self):
        for name in (
            "studyHash", "executionRecordHash", "trainedModelRecordHash",
            "predictionRecordHash", "simulationOutputHash"
        ):
            value = getattr(self, name)
            if value is not None and not _is_hash(value):
                raise ValueError(f"{name} must be a SHA-256 digest")
        return self


class ComparisonRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    resultHashes: List[str] = Field(min_length=2, max_length=100)
    comparisonKey: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=1, max_length=500)
    notes: str = Field(default="", max_length=10000)

    @model_validator(mode="after")
    def validate_hashes(self):
        if len(set(self.resultHashes)) != len(self.resultHashes):
            raise ValueError("resultHashes must be unique")
        if not all(_is_hash(v) for v in self.resultHashes):
            raise ValueError("resultHashes must contain SHA-256 digests")
        return self


class CorePlanRequest(BaseModel):
    projectKey: str = Field(min_length=1, max_length=300)
    objectKind: CoreObjectKind
    objectHash: str
    requestedBy: str = Field(default="user", max_length=200)

    @model_validator(mode="after")
    def validate_hash(self):
        if not _is_hash(self.objectHash):
            raise ValueError("objectHash must be a SHA-256 digest")
        return self


def _issues_for(req: StudyRequest) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []

    if req.scientificMLKind in {"physics-informed-contract", "constraint-aware-contract"}:
        issues.append({
            "severity": "warning",
            "code": "constraints-do-not-prove-validity",
            "message": "Encoding physical or scientific constraints does not by itself validate scientific correctness.",
        })

    if req.simulations:
        issues.append({
            "severity": "info",
            "code": "simulation-derived-training-data",
            "message": "Simulation-derived data inherits assumptions, parameterizations, and numerical limitations from the simulator.",
        })

    if req.scientificMLKind in {"surrogate-model", "emulator", "reduced-order-model"}:
        issues.append({
            "severity": "warning",
            "code": "surrogate-domain-limit",
            "message": "Surrogate and reduced-order models should not be assumed valid outside their supported training/design domain.",
        })

    if req.scientificMLKind == "hybrid-mechanistic-ml":
        issues.append({
            "severity": "info",
            "code": "hybrid-model-lineage",
            "message": "Mechanistic and learned components must remain separately traceable in provenance.",
        })

    issues.append({
        "severity": "warning",
        "code": "scientific-ml-not-physical-proof",
        "message": "Predictive performance does not establish physical truth, mechanism, or causal validity.",
    })
    return issues


def _study_payload(req: StudyRequest) -> Dict[str, Any]:
    payload = req.model_dump(mode="json")
    payload.update({
        "schema": STUDY_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "issues": _issues_for(req),
        "automaticTrainingExecuted": False,
        "automaticSimulationExecuted": False,
        "automaticModelSelection": False,
        "physicalValidityCertified": False,
    })
    return payload


def compose_study(req: StudyRequest) -> Dict[str, Any]:
    payload = _study_payload(req)
    study_hash = content_hash(payload)
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "studyHash": study_hash,
        "study": payload,
        "issues": payload["issues"],
        "studyReady": True,
    }


def save_study(req: StudyRequest) -> Dict[str, Any]:
    row = compose_study(req)
    path = _study_path(req.projectKey, row["studyHash"])
    existing = _json_read(path) if path.exists() else None
    if existing is not None:
        return {**row, "saved": True, "idempotent": True}
    record = {**row["study"], "studyHash": row["studyHash"], "createdAt": _now()}
    _atomic_json_write(path, record)
    return {**row, "saved": True, "idempotent": False}


def list_studies(project_key: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    directory = _study_dir(project_key)
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            row = _json_read(path)
            if isinstance(row, dict):
                rows.append(row)
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "projectKey": project_key, "studies": rows}


def get_study(project_key: str, study_hash: str) -> Dict[str, Any]:
    path = _study_path(project_key, study_hash)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Scientific ML study not found")
    return {"ok": True, "schema": SCHEMA, "version": VERSION, "study": _json_read(path)}


def record_result(req: ResultRequest) -> Dict[str, Any]:
    study_path = _study_path(req.projectKey, req.studyHash)
    if not study_path.exists():
        raise HTTPException(status_code=404, detail="Scientific ML study not found")

    study = _json_read(study_path)
    payload = req.model_dump(mode="json")
    payload.update({
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "scientificMLKind": study["scientificMLKind"],
        "taskKind": study["taskKind"],
        "datasetRecordHash": study["datasetRecordHash"],
        "sourceStudyHash": req.studyHash,
        "physicalValidityCertified": False,
    })

    result_hash = content_hash(payload)
    path = _result_path(req.projectKey, req.studyHash, result_hash)
    existing = _json_read(path) if path.exists() else None

    if existing is None:
        payload.update({"resultHash": result_hash, "recordedAt": _now()})
        _atomic_json_write(path, payload)

    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "resultHash": result_hash,
        "result": existing or payload,
        "idempotent": existing is not None,
    }


def list_results(project_key: str, study_hash: str) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    directory = _result_dir(project_key, study_hash)
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            row = _json_read(path)
            if isinstance(row, dict):
                rows.append(row)
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "projectKey": project_key,
        "studyHash": study_hash,
        "results": rows,
    }


def _find_result(project_key: str, result_hash: str) -> Optional[Dict[str, Any]]:
    root = _project_root(project_key) / "results"
    if not root.exists():
        return None
    for path in root.glob(f"*/{result_hash}.json"):
        row = _json_read(path)
        if isinstance(row, dict):
            return row
    return None


def compare_results(req: ComparisonRequest) -> Dict[str, Any]:
    rows = []
    for result_hash in req.resultHashes:
        row = _find_result(req.projectKey, result_hash)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Scientific ML result not found: {result_hash}")
        rows.append(row)

    metric_names = sorted(set(
        metric["name"]
        for row in rows
        for metric in row.get("metrics", [])
    ))

    metric_comparison = []
    for name in metric_names:
        values = []
        for row in rows:
            found = next((m for m in row.get("metrics", []) if m.get("name") == name), None)
            values.append(found.get("value") if found else None)
        present = [v for v in values if v is not None]
        metric_comparison.append({
            "metric": name,
            "values": values,
            "min": min(present) if present else None,
            "max": max(present) if present else None,
            "range": (max(present) - min(present)) if present else None,
        })

    payload = {
        "schema": COMPARISON_SCHEMA,
        "version": VERSION,
        "projectKey": req.projectKey,
        "comparisonKey": req.comparisonKey,
        "title": req.title,
        "resultHashes": req.resultHashes,
        "metricComparison": metric_comparison,
        "notes": req.notes,
        "automaticWinnerSelection": False,
        "interpretationBoundary": "Metric differences do not automatically establish scientific validity or a preferred model.",
    }
    comparison_hash = content_hash(payload)

    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "comparisonHash": comparison_hash,
        "comparison": payload,
    }


def diagnose(req: StudyRequest) -> Dict[str, Any]:
    issues = _issues_for(req)
    return {
        "ok": True,
        "schema": DIAGNOSTIC_SCHEMA,
        "version": VERSION,
        "issues": issues,
        "blocking": any(i["severity"] == "error" for i in issues),
    }


def core_plan(req: CorePlanRequest) -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "plan": {
            "objectKind": req.objectKind,
            "objectHash": req.objectHash,
            "requestedBy": req.requestedBy,
            "governedCoreObjectCreated": False,
            "automaticDispatch": False,
            "requiredAction": "Submit through a governed Platform Core handoff after explicit review.",
        },
    }


def manifest() -> Dict[str, Any]:
    body = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Scientific ML Workspace",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "studySchema": STUDY_SCHEMA,
        "resultSchema": RESULT_SCHEMA,
        "capabilities": {
            "contentAddressedScientificMLStudies": True,
            "surrogateModelContracts": True,
            "emulatorContracts": True,
            "physicsInformedContracts": True,
            "constraintAwareContracts": True,
            "operatorLearningContracts": True,
            "reducedOrderModelContracts": True,
            "hybridMechanisticMLContracts": True,
            "simulationToMLLineage": True,
            "scientificVariableMetadata": True,
            "scientificConstraintMetadata": True,
            "scientificBenchmarkBinding": True,
            "uncertaintyStudyHandoffs": True,
            "explainabilityStudyHandoffs": True,
            "constraintCheckResults": True,
            "crossResultComparison": True,
            "platformCorePromotionPlanning": True,
        },
        "boundaries": {
            "automaticModelTraining": False,
            "automaticSimulationExecution": False,
            "automaticScientificModelSelection": False,
            "automaticPhysicalValidityCertification": False,
            "automaticCoreDispatch": False,
            "governedCoreObjectCreated": False,
        },
        "scientificMLKinds": [
            "surrogate-model",
            "emulator",
            "physics-informed-contract",
            "constraint-aware-contract",
            "operator-learning-contract",
            "reduced-order-model",
            "hybrid-mechanistic-ml",
            "simulation-calibrated-ml",
        ],
        "constraintKinds": [
            "range",
            "monotonicity",
            "conservation",
            "symmetry",
            "boundary-condition",
            "initial-condition",
            "dimensional-consistency",
            "custom",
        ],
    }

    body["manifestHash"] = content_hash({
        k: v for k, v in body.items()
        if k not in {"ok", "manifestHash"}
    })
    return body


@router.get("/v1080/status")
def status_route():
    return manifest()


@router.post("/scientific-ml/studies/compose")
def compose_route(req: StudyRequest):
    return compose_study(req)


@router.post("/scientific-ml/studies")
def save_route(req: StudyRequest):
    return save_study(req)


@router.get("/scientific-ml/studies/{project_key}")
def list_route(project_key: str):
    return list_studies(project_key)


@router.get("/scientific-ml/studies/{project_key}/{study_hash}")
def get_route(project_key: str, study_hash: str):
    return get_study(project_key, study_hash)


@router.post("/scientific-ml/results")
def result_route(req: ResultRequest):
    return record_result(req)


@router.get("/scientific-ml/results/{project_key}/{study_hash}")
def result_list_route(project_key: str, study_hash: str):
    return list_results(project_key, study_hash)


@router.post("/scientific-ml/compare")
def compare_route(req: ComparisonRequest):
    return compare_results(req)


@router.post("/scientific-ml/diagnose")
def diagnose_route(req: StudyRequest):
    return diagnose(req)


@router.post("/scientific-ml/core-plan")
def core_plan_route(req: CorePlanRequest):
    return core_plan(req)

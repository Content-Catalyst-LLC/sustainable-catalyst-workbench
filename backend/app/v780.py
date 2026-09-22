"""Workbench v7.8.0 — Model Validation & Verification Framework.

Reproducible validation/verification evidence over Workbench scientific and
engineering results.  The framework evaluates declared benchmarks, compares
observed and predicted datasets, inspects numerical convergence evidence, and
assembles content-addressed V&V reports.  Passing declared checks means only
that the supplied evidence satisfied the supplied tolerance policy; it does not
certify scientific truth, fitness for purpose, safety, code compliance, or
regulatory acceptance.
"""
from __future__ import annotations

from copy import deepcopy
from math import isfinite, sqrt
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v670 import (
    CORE_COMPUTATION_LINEAGE_CONTRACT,
    CORE_PATHS,
    VerificationItem,
    _request,
    _verification_data,
)

VERSION = APP_VERSION
SCHEMA = "sc-workbench-model-validation-verification-framework/1.0"
BENCHMARK_SCHEMA = "sc-workbench-vv-benchmark-evaluation/1.0"
DATASET_SCHEMA = "sc-workbench-vv-dataset-comparison/1.0"
CONVERGENCE_SCHEMA = "sc-workbench-vv-convergence-evaluation/1.0"
REPORT_SCHEMA = "sc-workbench-vv-report/1.0"
VALIDATION_SCHEMA = "sc-workbench-vv-report-validation/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-vv-core-lineage-plan/1.0"
FRAMEWORK_REF = "workbench:/runtime/model-validation-verification"
CORE_LINEAGE_CONTRACT_LITERAL = "sc.research.computation-analysis-execution-lineage.v1"
MAX_CASES = 100
MAX_SERIES_POINTS = 10000
MAX_EVIDENCE = 200
router = APIRouter(tags=["workbench-v780-model-validation-verification"])


class ScalarBenchmarkCase(BaseModel):
    caseKey: str = Field(min_length=1, max_length=160)
    actualPath: str = Field(min_length=1, max_length=600)
    expected: float
    absoluteTolerance: float = Field(default=1e-8, ge=0, le=1e12)
    relativeTolerance: float = Field(default=1e-6, ge=0, le=1e6)
    unit: str = Field(default="", max_length=128)
    required: bool = True
    label: str = Field(default="", max_length=400)

    @field_validator("expected")
    @classmethod
    def finite_expected(cls, value: float) -> float:
        if not isfinite(float(value)):
            raise ValueError("expected must be finite")
        return float(value)


class BenchmarkEvaluationRequest(BaseModel):
    targetResult: Dict[str, Any]
    cases: List[ScalarBenchmarkCase] = Field(min_length=1, max_length=MAX_CASES)
    targetRef: str = Field(default="", max_length=1000)


class DatasetComparisonRequest(BaseModel):
    comparisonKey: str = Field(default="dataset-comparison", min_length=1, max_length=160)
    observed: List[float] = Field(min_length=2, max_length=MAX_SERIES_POINTS)
    predicted: List[float] = Field(min_length=2, max_length=MAX_SERIES_POINTS)
    maxRMSE: Optional[float] = Field(default=None, ge=0)
    maxMAE: Optional[float] = Field(default=None, ge=0)
    maxAbsoluteError: Optional[float] = Field(default=None, ge=0)
    minR2: Optional[float] = Field(default=None, ge=-1e12, le=1.0)
    maxAbsoluteBias: Optional[float] = Field(default=None, ge=0)
    unit: str = Field(default="", max_length=128)
    targetRef: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def validate_series(self):
        if len(self.observed) != len(self.predicted):
            raise ValueError("observed and predicted must have equal length")
        for value in [*self.observed, *self.predicted]:
            if not isfinite(float(value)):
                raise ValueError("series values must be finite")
        return self


class ConvergenceEvaluationRequest(BaseModel):
    study: Dict[str, Any]
    finalChangeTolerance: Optional[float] = Field(default=None, ge=0)
    requireMonotoneRefinement: bool = True
    required: bool = True


class VVReportRequest(BaseModel):
    reportKey: str = Field(default="validation-verification-report", min_length=1, max_length=180)
    targetKind: Literal[
        "solver", "simulation", "engineering", "design-space", "predictive",
        "forensic", "workflow", "model", "other"
    ] = "model"
    targetResult: Dict[str, Any]
    evidence: List[Dict[str, Any]] = Field(default_factory=list, max_length=MAX_EVIDENCE)
    assumptions: List[str] = Field(default_factory=list, max_length=100)
    limitations: List[str] = Field(default_factory=list, max_length=100)
    methodRefs: List[str] = Field(default_factory=list, max_length=100)
    datasetRefs: List[str] = Field(default_factory=list, max_length=100)
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    performedBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReportValidationRequest(BaseModel):
    report: Dict[str, Any]


class CoreVVLineagePlanRequest(BaseModel):
    report: Dict[str, Any]
    coreExecutionId: str = Field(default="", max_length=128)
    performedBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if not part:
            raise ValueError("actualPath contains an empty component")
        if isinstance(current, dict):
            if part not in current:
                raise ValueError(f"path component not found: {part}")
            current = current[part]
        elif isinstance(current, list):
            try:
                index = int(part)
            except ValueError as exc:
                raise ValueError(f"list path component must be an integer: {part}") from exc
            if index < 0 or index >= len(current):
                raise ValueError(f"list index out of range: {index}")
            current = current[index]
        else:
            raise ValueError(f"cannot descend through path component: {part}")
    return current


def _finite_number(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must resolve to a number") from exc
    if not isfinite(number):
        raise ValueError(f"{label} must resolve to a finite number")
    return number


def benchmark_evaluate(request: BenchmarkEvaluationRequest) -> Dict[str, Any]:
    case_results = []
    required_failed = False
    for case in request.cases:
        actual = _finite_number(_get_path(request.targetResult, case.actualPath), case.caseKey)
        expected = float(case.expected)
        abs_error = abs(actual - expected)
        scale = max(abs(expected), 1e-30)
        rel_error = abs_error / scale
        threshold = max(float(case.absoluteTolerance), float(case.relativeTolerance) * abs(expected))
        passed = abs_error <= threshold
        required_failed = required_failed or (case.required and not passed)
        case_results.append({
            "caseKey": case.caseKey,
            "label": case.label,
            "actualPath": case.actualPath,
            "actual": actual,
            "expected": expected,
            "unit": case.unit,
            "absoluteError": abs_error,
            "relativeError": rel_error,
            "effectiveTolerance": threshold,
            "absoluteTolerance": case.absoluteTolerance,
            "relativeTolerance": case.relativeTolerance,
            "required": case.required,
            "passed": passed,
        })
    record = {
        "ok": True,
        "schema": BENCHMARK_SCHEMA,
        "version": VERSION,
        "evidenceKind": "scalar-benchmark",
        "targetRef": request.targetRef,
        "targetHash": content_hash(request.targetResult),
        "caseCount": len(case_results),
        "passedCaseCount": sum(1 for x in case_results if x["passed"]),
        "failedCaseCount": sum(1 for x in case_results if not x["passed"]),
        "outcome": "fail" if required_failed else "pass",
        "cases": case_results,
        "scientificValidityCertified": False,
        "truthDeterminationPerformed": False,
    }
    record["evidenceHash"] = content_hash(record)
    return record


def dataset_compare(request: DatasetComparisonRequest) -> Dict[str, Any]:
    obs = [float(x) for x in request.observed]
    pred = [float(x) for x in request.predicted]
    residuals = [p - o for o, p in zip(obs, pred)]
    n = len(obs)
    mae = sum(abs(x) for x in residuals) / n
    mse = sum(x * x for x in residuals) / n
    rmse = sqrt(mse)
    max_abs = max(abs(x) for x in residuals)
    bias = sum(residuals) / n
    mean_obs = sum(obs) / n
    ss_tot = sum((x - mean_obs) ** 2 for x in obs)
    ss_res = sum((o - p) ** 2 for o, p in zip(obs, pred))
    r2 = None if ss_tot <= 1e-30 else 1.0 - (ss_res / ss_tot)
    checks = []
    def add(name: str, observed: Optional[float], relation: str, threshold: Optional[float], passed: Optional[bool]):
        if threshold is not None:
            checks.append({"metric": name, "observed": observed, "relation": relation, "threshold": threshold, "passed": bool(passed)})
    add("rmse", rmse, "<=", request.maxRMSE, rmse <= request.maxRMSE if request.maxRMSE is not None else None)
    add("mae", mae, "<=", request.maxMAE, mae <= request.maxMAE if request.maxMAE is not None else None)
    add("maxAbsoluteError", max_abs, "<=", request.maxAbsoluteError, max_abs <= request.maxAbsoluteError if request.maxAbsoluteError is not None else None)
    add("r2", r2, ">=", request.minR2, r2 is not None and r2 >= request.minR2 if request.minR2 is not None else None)
    add("absoluteBias", abs(bias), "<=", request.maxAbsoluteBias, abs(bias) <= request.maxAbsoluteBias if request.maxAbsoluteBias is not None else None)
    outcome = "incomplete" if not checks else ("pass" if all(x["passed"] for x in checks) else "fail")
    record = {
        "ok": True,
        "schema": DATASET_SCHEMA,
        "version": VERSION,
        "evidenceKind": "dataset-comparison",
        "comparisonKey": request.comparisonKey,
        "targetRef": request.targetRef,
        "sampleCount": n,
        "unit": request.unit,
        "metrics": {"mae": mae, "rmse": rmse, "maxAbsoluteError": max_abs, "bias": bias, "r2": r2},
        "checks": checks,
        "outcome": outcome,
        "observedHash": content_hash(obs),
        "predictedHash": content_hash(pred),
        "scientificValidityCertified": False,
        "fitnessForPurposeCertified": False,
    }
    record["evidenceHash"] = content_hash(record)
    return record


def convergence_evaluate(request: ConvergenceEvaluationRequest) -> Dict[str, Any]:
    study = request.study
    levels = study.get("levels") if isinstance(study, dict) else None
    if not isinstance(levels, list) or len(levels) < 2:
        raise HTTPException(status_code=422, detail="study must contain at least two convergence levels")
    changes = []
    for item in levels:
        if not isinstance(item, dict):
            raise HTTPException(status_code=422, detail="convergence level must be an object")
        change = item.get("absoluteChangeFromPrevious")
        if change is not None:
            changes.append(_finite_number(change, "absoluteChangeFromPrevious"))
    if not changes:
        outcome = "incomplete"
        monotone = False
        final_change = None
    else:
        monotone = all(changes[i] <= changes[i-1] * 1.05 for i in range(1, len(changes)))
        final_change = changes[-1]
        checks = []
        if request.requireMonotoneRefinement:
            checks.append(monotone)
        if request.finalChangeTolerance is not None:
            checks.append(final_change <= request.finalChangeTolerance)
        outcome = "incomplete" if not checks else ("pass" if all(checks) else "fail")
    record = {
        "ok": True,
        "schema": CONVERGENCE_SCHEMA,
        "version": VERSION,
        "evidenceKind": "numerical-convergence",
        "sourceStudySchema": study.get("schema") if isinstance(study, dict) else None,
        "sourceStudyHash": study.get("studyHash") if isinstance(study, dict) else None,
        "levelCount": len(levels),
        "changeSequence": changes,
        "lastAbsoluteChange": final_change,
        "monotoneRefinementObserved": monotone,
        "requireMonotoneRefinement": request.requireMonotoneRefinement,
        "finalChangeTolerance": request.finalChangeTolerance,
        "required": request.required,
        "outcome": outcome,
        "scientificConvergenceCertified": False,
        "scientificValidityCertified": False,
    }
    record["evidenceHash"] = content_hash(record)
    return record


def _evidence_outcome(item: Dict[str, Any]) -> str:
    value = str(item.get("outcome") or "incomplete")
    return value if value in {"pass", "fail", "incomplete"} else "incomplete"


def build_report(request: VVReportRequest) -> Dict[str, Any]:
    evidence = [deepcopy(x) for x in request.evidence]
    counts = {"pass": 0, "fail": 0, "incomplete": 0}
    evidence_refs = []
    for item in evidence:
        outcome = _evidence_outcome(item)
        counts[outcome] += 1
        if item.get("evidenceHash"):
            evidence_refs.append(f"sc://workbench/vv/evidence/{item['evidenceHash']}")
    overall = "fail" if counts["fail"] else ("incomplete" if counts["incomplete"] or not evidence else "pass")
    target_hash = content_hash(request.targetResult)
    target_execution_ref = ""
    eo = request.targetResult.get("executionObject") if isinstance(request.targetResult, dict) else None
    if isinstance(eo, dict):
        target_execution_ref = str(eo.get("objectRef") or "")
    basis = {
        "reportKey": request.reportKey,
        "targetKind": request.targetKind,
        "targetHash": target_hash,
        "evidenceHashes": [x.get("evidenceHash") for x in evidence],
        "assumptions": request.assumptions,
        "limitations": request.limitations,
        "methodRefs": request.methodRefs,
        "datasetRefs": request.datasetRefs,
        "projectRef": request.projectRef,
        "coreSessionId": request.coreSessionId,
        "performedBy": request.performedBy,
        "metadata": request.metadata,
    }
    report_id = "vv-" + content_hash(basis)[:24]
    record = {
        "ok": True,
        "schema": REPORT_SCHEMA,
        "version": VERSION,
        "reportId": report_id,
        "reportRef": f"sc://workbench/vv/report/{report_id}",
        "reportKey": request.reportKey,
        "targetKind": request.targetKind,
        "targetHash": target_hash,
        "targetExecutionObjectRef": target_execution_ref,
        "evidence": evidence,
        "evidenceRefs": sorted(set(evidence_refs)),
        "evidenceCounts": counts,
        "overallStatus": overall,
        "declaredChecksPassed": overall == "pass",
        "assumptions": request.assumptions,
        "limitations": request.limitations,
        "methodRefs": sorted(set(request.methodRefs)),
        "datasetRefs": sorted(set(request.datasetRefs)),
        "projectRef": request.projectRef,
        "coreSessionId": request.coreSessionId,
        "performedBy": request.performedBy,
        "metadata": request.metadata,
        "scientificValidityCertified": False,
        "truthDeterminationPerformed": False,
        "fitnessForPurposeCertified": False,
        "engineeringSafetyCertified": False,
        "codeComplianceCertified": False,
        "regulatoryAcceptanceCertified": False,
        "automaticModelAcceptanceAuthorized": False,
    }
    record["reportHash"] = content_hash(record)
    return record


def validate_report(report: Dict[str, Any]) -> Dict[str, Any]:
    reasons = []
    if report.get("schema") != REPORT_SCHEMA:
        reasons.append("report-schema-mismatch")
    if report.get("version") != VERSION:
        reasons.append("report-version-mismatch")
    observed = report.get("reportHash")
    basis = deepcopy(report)
    basis.pop("reportHash", None)
    expected = content_hash(basis)
    if observed != expected:
        reasons.append("report-hash-mismatch")
    report_id = str(report.get("reportId") or "")
    if report.get("reportRef") != f"sc://workbench/vv/report/{report_id}":
        reasons.append("report-reference-mismatch")
    return {
        "ok": not reasons,
        "schema": VALIDATION_SCHEMA,
        "version": VERSION,
        "valid": not reasons,
        "reasons": reasons,
        "expectedReportHash": expected,
        "observedReportHash": observed,
        "scientificValidityCertified": False,
    }


def core_lineage_plan(request: CoreVVLineagePlanRequest) -> Dict[str, Any]:
    check = validate_report(request.report)
    if not check["valid"]:
        raise HTTPException(status_code=422, detail={"message": "V&V report failed integrity validation", "reasons": check["reasons"]})
    verification_requests = []
    if request.coreExecutionId:
        item = VerificationItem(
            verificationKey=request.report.get("reportKey") or request.report.get("reportId") or "workbench-vv",
            verificationType="model_validation_verification",
            status=request.report.get("overallStatus") or "recorded",
            evidence={
                "report_ref": request.report.get("reportRef"),
                "report_hash": request.report.get("reportHash"),
                "target_kind": request.report.get("targetKind"),
                "target_hash": request.report.get("targetHash"),
                "declared_checks_passed": bool(request.report.get("declaredChecksPassed")),
                "evidence_counts": request.report.get("evidenceCounts", {}),
                "scientific_validity_certified": False,
                "fitness_for_purpose_certified": False,
                "truth_determination_performed": False,
            },
            performedBy=request.performedBy,
            provenance={"source":"workbench-v780","reportRef":request.report.get("reportRef")},
            createdBy=request.performedBy,
        )
        verification_requests.append(_request(
            CORE_PATHS["verifications"].format(execution_id=request.coreExecutionId),
            _verification_data(item),
            "verification-registration",
        ))
    record = {
        "ok": True,
        "schema": CORE_PLAN_SCHEMA,
        "version": VERSION,
        "frameworkRef": FRAMEWORK_REF,
        "coreComputationLineageContract": CORE_COMPUTATION_LINEAGE_CONTRACT,
        "reportRef": request.report.get("reportRef"),
        "reportHash": request.report.get("reportHash"),
        "coreExecutionId": request.coreExecutionId,
        "coreExecutionIdMustComeFromCore": True,
        "verificationRegistrations": verification_requests,
        "automaticCoreDispatchAuthorized": False,
        "automaticCorePersistenceAuthorized": False,
        "coreValidatesScientificTruth": False,
        "coreCertifiesFitnessForPurpose": False,
    }
    record["planHash"] = content_hash(record)
    return record


def manifest() -> Dict[str, Any]:
    record = {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Model Validation & Verification Framework",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "frameworkRef": FRAMEWORK_REF,
        "coreComputationLineageContract": CORE_LINEAGE_CONTRACT_LITERAL,
        "evidenceFamilies": ["scalar-benchmark", "dataset-comparison", "numerical-convergence", "integrated-vv-report"],
        "capabilities": {
            "referenceBenchmarkEvaluation": True,
            "absoluteRelativeTolerancePolicies": True,
            "observedPredictedDatasetComparison": True,
            "rmseMaeBiasR2Diagnostics": True,
            "numericalConvergenceVerification": True,
            "contentAddressedVVReports": True,
            "reportIntegrityValidation": True,
            "solverSimulationEngineeringOptimizationPredictiveTargets": True,
            "platformCoreVerificationLineagePlanning": True,
        },
        "boundaries": {
            "automaticModelAcceptanceAuthorized": False,
            "scientificValidityCertificationAuthorized": False,
            "truthDeterminationAuthorized": False,
            "fitnessForPurposeCertificationAuthorized": False,
            "engineeringSafetyCertificationAuthorized": False,
            "codeComplianceCertificationAuthorized": False,
            "regulatoryAcceptanceCertificationAuthorized": False,
            "automaticCoreDispatchAuthorized": False,
            "automaticCorePersistenceAuthorized": False,
        },
    }
    record["manifestHash"] = content_hash(record)
    return record


@router.get("/validation/manifest")
def get_manifest(): return manifest()

@router.post("/validation/benchmark/evaluate")
def post_benchmark(request: BenchmarkEvaluationRequest):
    try: return benchmark_evaluate(request)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post("/validation/dataset-compare")
def post_dataset_compare(request: DatasetComparisonRequest): return dataset_compare(request)

@router.post("/validation/convergence/evaluate")
def post_convergence(request: ConvergenceEvaluationRequest): return convergence_evaluate(request)

@router.post("/validation/report/build")
def post_report(request: VVReportRequest): return build_report(request)

@router.post("/validation/report/validate")
def post_report_validate(request: ReportValidationRequest): return validate_report(request.report)

@router.post("/integration/core/validation-lineage/plan")
def post_core_plan(request: CoreVVLineagePlanRequest, x_sc_service_token: Optional[str]=Header(default=None,alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token)
    return core_lineage_plan(request)

@router.get("/v780/status")
def status():
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Model Validation & Verification Framework",
        "benchmarkEvaluation": True,
        "datasetComparison": True,
        "convergenceVerification": True,
        "contentAddressedReports": True,
        "coreVerificationLineagePlanning": True,
        "automaticModelAcceptance": False,
        "scientificValidityCertification": False,
        "truthDetermination": False,
        "automaticCoreDispatch": False,
    }

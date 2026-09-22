"""Workbench v7.4.0 — Numerical Methods & Solver Runtime.

This release promotes the bounded numerical-scientific capabilities introduced in
v5.6 and unified by v7.0 into a canonical solver runtime. It normalizes problem
families, solver selection, convergence/error diagnostics, v7.3 workspace
bindings, v7.1 execution objects, and Platform Core computation-lineage plans.

The runtime is deliberately bounded: no arbitrary Python, dynamic imports,
shell execution, automatic Core dispatch, hidden data fetching, or claims of
scientific validity are authorized.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal, Optional, Type

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v560 import (
    RootInput, IntegrationInput, DifferentiationInput, InterpolationInput, ODEInput,
    LinearAlgebraInput, OptimizationInput,
)
from .v640 import _authorize_core_route
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT, CORE_PATHS, OutputItem, _output_data, _request
from .v720 import OrchestratedExecutionRequest, orchestrated_execute
from .v730 import _workspace_ok, _set_path

VERSION = APP_VERSION
SCHEMA = "sc-workbench-numerical-methods-solver-runtime/1.0"
SOLVER_RESULT_SCHEMA = "sc-workbench-numerical-solver-result/1.0"
CONVERGENCE_SCHEMA = "sc-workbench-numerical-convergence-study/1.0"
WORKSPACE_BINDING_SCHEMA = "sc-workbench-numerical-workspace-binding-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-numerical-solver-core-lineage-plan/1.0"
SOLVER_REF = "workbench:/runtime/numerical-methods-solvers"
CORE_LINEAGE_CONTRACT_LITERAL = "sc.research.computation-analysis-execution-lineage.v1"
MAX_STUDY_LEVELS = 8
MAX_BINDINGS = 200

ProblemKind = Literal[
    "root", "integration", "differentiation", "interpolation", "ode",
    "linear-algebra", "optimization",
]

router = APIRouter(tags=["workbench-v740-numerical-methods-solver-runtime"])

MODEL_BY_KIND: Dict[str, Type[BaseModel]] = {
    "root": RootInput,
    "integration": IntegrationInput,
    "differentiation": DifferentiationInput,
    "interpolation": InterpolationInput,
    "ode": ODEInput,
    "linear-algebra": LinearAlgebraInput,
    "optimization": OptimizationInput,
}

OPERATION_BY_KIND = {
    "root": "numerical.root",
    "integration": "numerical.integrate",
    "differentiation": "numerical.differentiate",
    "interpolation": "numerical.interpolate",
    "ode": "numerical.ode",
    "linear-algebra": "numerical.linear-algebra",
    "optimization": "numerical.optimize",
}

SOLVER_CATALOG: Dict[str, Dict[str, Any]] = {
    "root.brentq": {"problemKind": "root", "field": "method", "value": "brentq", "family": "bracketing", "requiresBracket": True},
    "root.bisection": {"problemKind": "root", "field": "method", "value": "bisection", "family": "bracketing", "requiresBracket": True},
    "root.secant": {"problemKind": "root", "field": "method", "value": "secant", "family": "open", "requiresInitialGuess": True},
    "root.newton": {"problemKind": "root", "field": "method", "value": "newton", "family": "derivative-open", "requiresInitialGuess": True},
    "integration.adaptive": {"problemKind": "integration", "field": "method", "value": "adaptive", "family": "adaptive-quadrature"},
    "integration.simpson": {"problemKind": "integration", "field": "method", "value": "simpson", "family": "composite-quadrature"},
    "integration.trapezoid": {"problemKind": "integration", "field": "method", "value": "trapezoid", "family": "composite-quadrature"},
    "differentiation.five-point": {"problemKind": "differentiation", "field": None, "value": None, "family": "centered-five-point"},
    "interpolation.linear": {"problemKind": "interpolation", "field": "method", "value": "linear", "family": "piecewise-linear"},
    "interpolation.cubic-spline": {"problemKind": "interpolation", "field": "method", "value": "cubic-spline", "family": "cubic-spline"},
    "interpolation.pchip": {"problemKind": "interpolation", "field": "method", "value": "pchip", "family": "shape-preserving"},
    "ode.rk45": {"problemKind": "ode", "field": "method", "value": "RK45", "family": "explicit-runge-kutta"},
    "ode.dop853": {"problemKind": "ode", "field": "method", "value": "DOP853", "family": "explicit-runge-kutta"},
    "ode.radau": {"problemKind": "ode", "field": "method", "value": "Radau", "family": "implicit-stiff"},
    "ode.bdf": {"problemKind": "ode", "field": "method", "value": "BDF", "family": "implicit-stiff"},
    "linear.solve": {"problemKind": "linear-algebra", "field": "operation", "value": "solve", "family": "direct-linear-solve"},
    "linear.eigen": {"problemKind": "linear-algebra", "field": "operation", "value": "eigen", "family": "eigen-analysis"},
    "linear.svd": {"problemKind": "linear-algebra", "field": "operation", "value": "svd", "family": "singular-value-decomposition"},
    "linear.least-squares": {"problemKind": "linear-algebra", "field": "operation", "value": "least-squares", "family": "least-squares"},
    "linear.inverse": {"problemKind": "linear-algebra", "field": "operation", "value": "inverse", "family": "matrix-inverse"},
    "optimization.lbfgsb": {"problemKind": "optimization", "field": None, "value": None, "family": "bounded-quasi-newton"},
}

DEFAULT_SOLVER = {
    "root": "root.brentq",
    "integration": "integration.adaptive",
    "differentiation": "differentiation.five-point",
    "interpolation": "interpolation.pchip",
    "ode": "ode.rk45",
    "linear-algebra": "linear.solve",
    "optimization": "optimization.lbfgsb",
}


class SolverRequest(BaseModel):
    problemKind: ProblemKind
    problem: Dict[str, Any]
    solverKey: str = Field(default="", max_length=120)
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    requestKey: str = Field(default="", max_length=180)
    label: str = Field(default="", max_length=400)
    workspaceRef: str = Field(default="", max_length=1000)
    workspaceHash: str = Field(default="", max_length=128)
    inputRefs: List[str] = Field(default_factory=list, max_length=200)
    datasetRefs: List[str] = Field(default_factory=list, max_length=100)
    methodRefs: List[str] = Field(default_factory=list, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("solverKey")
    @classmethod
    def solver_known(cls, value: str) -> str:
        value = (value or "").strip()
        if value and value not in SOLVER_CATALOG:
            raise ValueError("solverKey is not registered")
        return value

    @model_validator(mode="after")
    def solver_matches_problem(self):
        if self.solverKey and SOLVER_CATALOG[self.solverKey]["problemKind"] != self.problemKind:
            raise ValueError("solverKey does not support problemKind")
        return self


class ConvergenceStudyRequest(BaseModel):
    problemKind: Literal["root", "integration", "differentiation", "ode"]
    problem: Dict[str, Any]
    solverKey: str = Field(default="", max_length=120)
    levels: int = Field(default=4, ge=2, le=MAX_STUDY_LEVELS)
    refinementFactor: float = Field(default=2.0, gt=1.0, le=10.0)
    projectRef: str = Field(default="", max_length=1000)
    requestKey: str = Field(default="convergence-study", max_length=180)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BindingSpec(BaseModel):
    sourceKind: Literal["variable", "parameter", "dataset"]
    sourceKey: str
    parameterSetKey: str = Field(default="", max_length=120)
    targetField: str = Field(default="", max_length=300)


class WorkspaceSolverBindingRequest(BaseModel):
    workspace: Dict[str, Any]
    problemKind: ProblemKind
    problem: Dict[str, Any] = Field(default_factory=dict)
    solverKey: str = Field(default="", max_length=120)
    bindings: List[BindingSpec] = Field(default_factory=list, max_length=MAX_BINDINGS)
    requestKey: str = Field(default="", max_length=180)
    label: str = Field(default="", max_length=400)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CoreSolverLineagePlanRequest(BaseModel):
    solverResult: Dict[str, Any]
    coreExecutionId: str = Field(default="", max_length=128)
    createdBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _resolved_solver_key(request: SolverRequest) -> str:
    return request.solverKey or DEFAULT_SOLVER[request.problemKind]


def _validated_problem(request: SolverRequest) -> BaseModel:
    data = deepcopy(request.problem)
    solver_key = _resolved_solver_key(request)
    spec = SOLVER_CATALOG[solver_key]
    field = spec.get("field")
    if field:
        data[field] = spec["value"]
    try:
        return MODEL_BY_KIND[request.problemKind].model_validate(data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc


def _specialist_result(orchestrated: Dict[str, Any]) -> Dict[str, Any]:
    execution = orchestrated.get("executionResult", {})
    raw = execution.get("result", {})
    # v7.0 wraps specialist {ok,result}; tolerate either shape.
    if isinstance(raw, dict) and "result" in raw and isinstance(raw["result"], dict):
        return raw["result"]
    return raw if isinstance(raw, dict) else {}


def _diagnostics(kind: str, problem: BaseModel, specialist: Dict[str, Any]) -> Dict[str, Any]:
    # v5.6 numerical objects put the method-specific payload under `result`.
    details = specialist.get("result", specialist) if isinstance(specialist, dict) else {}
    diagnostics: Dict[str, Any] = {"problemKind": kind, "finiteResult": True}
    if kind == "root":
        residual = details.get("residual")
        tol = float(getattr(problem, "tolerance", 1e-10))
        diagnostics.update({
            "converged": bool(details.get("converged")),
            "residual": residual,
            "absoluteResidual": None if residual is None else abs(float(residual)),
            "tolerance": tol,
            "iterations": details.get("iterations"),
            "functionEvaluations": details.get("functionCalls"),
            "toleranceSatisfied": bool(details.get("converged")) and residual is not None and abs(float(residual)) <= max(tol * 10.0, 1e-12),
        })
    elif kind == "integration":
        diagnostics.update({
            "converged": True,
            "estimatedAbsoluteError": details.get("estimatedAbsoluteError"),
            "tolerance": getattr(problem, "tolerance", None),
            "sampleCount": details.get("sampleCount"),
            "errorEstimateAvailable": details.get("estimatedAbsoluteError") is not None,
        })
    elif kind == "differentiation":
        diagnostics.update({
            "converged": True,
            "step": details.get("step"),
            "order": details.get("order"),
            "absoluteDifferenceFromSymbolic": details.get("absoluteDifferenceFromSymbolic"),
            "symbolicReferenceAvailable": details.get("symbolicValue") is not None,
        })
    elif kind == "interpolation":
        diagnostics.update({
            "converged": True,
            "inputPointCount": len(details.get("inputPoints", [])),
            "evaluatedPointCount": len(details.get("evaluatedPoints", [])),
            "domain": details.get("domain"),
            "extrapolationAuthorized": False,
        })
    elif kind == "ode":
        diagnostics.update({
            "converged": bool(details.get("successful")),
            "functionEvaluations": details.get("functionEvaluations"),
            "jacobianEvaluations": details.get("jacobianEvaluations"),
            "relativeTolerance": getattr(problem, "relativeTolerance", None),
            "absoluteTolerance": getattr(problem, "absoluteTolerance", None),
            "message": details.get("message"),
        })
    elif kind == "linear-algebra":
        condition = details.get("conditionNumber")
        diagnostics.update({
            "converged": True,
            "rank": details.get("rank"),
            "conditionNumber": condition,
            "illConditioned": condition is not None and float(condition) >= 1e12,
            "residualNorm": details.get("residualNorm"),
            "shape": details.get("shape"),
        })
    elif kind == "optimization":
        diagnostics.update({
            "converged": bool(details.get("success")),
            "iterations": details.get("iterations"),
            "functionEvaluations": details.get("functionEvaluations"),
            "projectedGradientNorm": details.get("projectedGradientNorm"),
            "tolerance": getattr(problem, "tolerance", None),
            "message": details.get("message"),
        })
    diagnostics["diagnosticsHash"] = content_hash(diagnostics)
    return diagnostics


def solve(request: SolverRequest) -> Dict[str, Any]:
    solver_key = _resolved_solver_key(request)
    problem = _validated_problem(request)
    operation = OPERATION_BY_KIND[request.problemKind]
    orchestration = orchestrated_execute(OrchestratedExecutionRequest(
        operation=operation,
        payload=problem.model_dump(),
        projectRef=request.projectRef,
        coreSessionId=request.coreSessionId,
        requestKey=request.requestKey or f"solver:{request.problemKind}:{solver_key}",
        label=request.label or solver_key,
        inputRefs=request.inputRefs,
        datasetRefs=request.datasetRefs,
        preferredRuntime="workbench.numerical",
        methodRefs=[SOLVER_REF, solver_key, *request.methodRefs],
        tags=request.tags,
        metadata={
            **request.metadata,
            "solverKey": solver_key,
            "problemKind": request.problemKind,
            "workspaceRef": request.workspaceRef,
            "workspaceHash": request.workspaceHash,
        },
    ))
    diagnostics = _diagnostics(request.problemKind, problem, _specialist_result(orchestration))
    record = {
        "ok": bool(orchestration.get("ok", True)),
        "schema": SOLVER_RESULT_SCHEMA,
        "version": VERSION,
        "solverRuntimeRef": SOLVER_REF,
        "problemKind": request.problemKind,
        "solverKey": solver_key,
        "solverFamily": SOLVER_CATALOG[solver_key]["family"],
        "operation": operation,
        "normalizedProblem": problem.model_dump(),
        "workspaceRef": request.workspaceRef,
        "workspaceHash": request.workspaceHash,
        "diagnostics": diagnostics,
        "orchestration": orchestration,
        "executionObject": orchestration.get("executionObject"),
        "automaticSolverFallbackPerformed": False,
        "automaticCoreDispatchPerformed": False,
        "automaticCorePersistencePerformed": False,
        "scientificValidityCertified": False,
    }
    record["solverRunHash"] = content_hash({
        "problemKind": record["problemKind"], "solverKey": solver_key,
        "normalizedProblem": record["normalizedProblem"],
        "diagnosticsHash": diagnostics["diagnosticsHash"],
        "executionObjectHash": (record.get("executionObject") or {}).get("objectHash"),
    })
    return record


def validate_solver_result(result: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    if result.get("schema") != SOLVER_RESULT_SCHEMA: reasons.append("schema-mismatch")
    if result.get("version") != VERSION: reasons.append("version-mismatch")
    if result.get("solverKey") not in SOLVER_CATALOG: reasons.append("unknown-solver")
    diagnostics = result.get("diagnostics") or {}
    expected_diag = content_hash({k:v for k,v in diagnostics.items() if k != "diagnosticsHash"}) if diagnostics else ""
    if diagnostics.get("diagnosticsHash") != expected_diag: reasons.append("diagnostics-hash-mismatch")
    expected_run = content_hash({
        "problemKind": result.get("problemKind"), "solverKey": result.get("solverKey"),
        "normalizedProblem": result.get("normalizedProblem"),
        "diagnosticsHash": diagnostics.get("diagnosticsHash"),
        "executionObjectHash": (result.get("executionObject") or {}).get("objectHash"),
    })
    if result.get("solverRunHash") != expected_run: reasons.append("solver-run-hash-mismatch")
    return {"ok": not reasons, "schema": "sc-workbench-numerical-solver-validation/1.0", "version": VERSION, "valid": not reasons, "reasons": reasons, "solverRunHash": result.get("solverRunHash", "")}


def _refined_problem(kind: str, base: Dict[str, Any], level: int, factor: float) -> Dict[str, Any]:
    p = deepcopy(base)
    scale = factor ** level
    if kind == "integration":
        p["samples"] = min(5001, max(5, int(round(float(p.get("samples", 101)) * scale))))
        if p.get("method", "adaptive") == "adaptive": p["tolerance"] = max(1e-14, float(p.get("tolerance", 1e-9)) / scale)
    elif kind == "differentiation":
        p["step"] = max(1e-12, float(p.get("step", 1e-4)) / scale)
    elif kind == "ode":
        p["samples"] = min(5001, max(2, int(round(float(p.get("samples", 101)) * scale))))
        p["relativeTolerance"] = max(1e-12, float(p.get("relativeTolerance", 1e-6)) / scale)
        p["absoluteTolerance"] = max(1e-14, float(p.get("absoluteTolerance", 1e-8)) / scale)
    elif kind == "root":
        p["tolerance"] = max(1e-14, float(p.get("tolerance", 1e-8)) / scale)
        p["maxIterations"] = min(500, max(20, int(round(float(p.get("maxIterations", 100)) * min(scale, 4.0)))))
    return p


def _primary_value(kind: str, solver_result: Dict[str, Any]) -> Optional[float]:
    raw = _specialist_result(solver_result.get("orchestration", {}))
    details = raw.get("result", raw) if isinstance(raw, dict) else {}
    try:
        if kind == "root": return float(details["root"])
        if kind == "integration": return float(details["value"])
        if kind == "differentiation": return float(details["finiteDifferenceValue"])
        if kind == "ode":
            values = list((details.get("finalState") or {}).values())
            return float(values[0]) if values else None
    except (KeyError, TypeError, ValueError): return None
    return None


def convergence_study(request: ConvergenceStudyRequest) -> Dict[str, Any]:
    levels = []
    previous: Optional[float] = None
    for level in range(request.levels):
        run = solve(SolverRequest(
            problemKind=request.problemKind,
            problem=_refined_problem(request.problemKind, request.problem, level, request.refinementFactor),
            solverKey=request.solverKey,
            projectRef=request.projectRef,
            requestKey=f"{request.requestKey}:L{level}",
            metadata={**request.metadata, "convergenceStudyLevel": level},
        ))
        value = _primary_value(request.problemKind, run)
        delta = None if previous is None or value is None else abs(value - previous)
        levels.append({"level": level, "solverRunHash": run["solverRunHash"], "primaryValue": value, "absoluteChangeFromPrevious": delta, "diagnostics": run["diagnostics"]})
        previous = value
    changes = [x["absoluteChangeFromPrevious"] for x in levels if x["absoluteChangeFromPrevious"] is not None]
    record = {
        "ok": True, "schema": CONVERGENCE_SCHEMA, "version": VERSION,
        "problemKind": request.problemKind, "solverKey": request.solverKey or DEFAULT_SOLVER[request.problemKind],
        "refinementFactor": request.refinementFactor, "levels": levels,
        "lastAbsoluteChange": changes[-1] if changes else None,
        "monotoneRefinementObserved": len(changes) < 2 or all(changes[i] <= changes[i-1] * 1.05 for i in range(1, len(changes))),
        "scientificConvergenceCertified": False,
    }
    record["studyHash"] = content_hash(record)
    return record


def workspace_binding_plan(request: WorkspaceSolverBindingRequest) -> Dict[str, Any]:
    ws = request.workspace; _workspace_ok(ws)
    variables = {x["variableKey"]: x for x in ws.get("variables", []) if isinstance(x, dict)}
    datasets = {x["datasetKey"]: x for x in ws.get("datasets", []) if isinstance(x, dict)}
    parameter_sets = {x["parameterSetKey"]: x for x in ws.get("parameterSets", []) if isinstance(x, dict)}
    problem = deepcopy(request.problem); input_refs=[]; dataset_refs=[]; materialized=[]
    for binding in request.bindings:
        if binding.sourceKind == "variable":
            src=variables.get(binding.sourceKey)
            if not src: raise HTTPException(status_code=422,detail=f"unknown variable: {binding.sourceKey}")
            value=src.get("derivedValue") if src.get("expression") else src.get("value")
            if value is None or not binding.targetField: raise HTTPException(status_code=422,detail="variable bindings require scalar value and targetField")
            _set_path(problem,binding.targetField,value); input_refs.append(src["variableRef"]); ref=src["variableRef"]
        elif binding.sourceKind == "parameter":
            ps=parameter_sets.get(binding.parameterSetKey)
            if not ps: raise HTTPException(status_code=422,detail=f"unknown parameter set: {binding.parameterSetKey}")
            src=next((x for x in ps.get("parameters",[]) if x.get("parameterKey")==binding.sourceKey),None)
            if not src or not binding.targetField: raise HTTPException(status_code=422,detail="parameter binding requires known parameter and targetField")
            _set_path(problem,binding.targetField,src.get("value")); input_refs.append(src["parameterRef"]); ref=src["parameterRef"]
        else:
            src=datasets.get(binding.sourceKey)
            if not src: raise HTTPException(status_code=422,detail=f"unknown dataset: {binding.sourceKey}")
            ref=src["datasetRef"]; input_refs.append(ref); dataset_refs.append(ref)
            if binding.targetField: _set_path(problem,binding.targetField,ref)
        materialized.append({"sourceKind":binding.sourceKind,"sourceKey":binding.sourceKey,"sourceRef":ref,"targetField":binding.targetField})
    solver_request = {
        "problemKind": request.problemKind, "problem": problem, "solverKey": request.solverKey,
        "projectRef": ws.get("projectRef", ""), "coreSessionId": ws.get("coreSessionId", ""),
        "requestKey": request.requestKey or f"{ws.get('workspaceKey','workspace')}:solver:{request.problemKind}",
        "label": request.label, "workspaceRef": ws["workspaceRef"], "workspaceHash": ws["workspaceHash"],
        "inputRefs": sorted(set(input_refs)), "datasetRefs": sorted(set(dataset_refs)),
        "metadata": {"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],**request.metadata},
    }
    # Validate the materialized problem without executing it.
    _validated_problem(SolverRequest.model_validate(solver_request))
    record={"ok":True,"schema":WORKSPACE_BINDING_SCHEMA,"version":VERSION,"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],"materializedBindings":materialized,"solverRequest":solver_request,"executionPath":"/solvers/solve","executionPerformed":False,"automaticDispatchAuthorized":False}
    record["bindingPlanHash"]=content_hash(record)
    return record


def core_lineage_plan(request: CoreSolverLineagePlanRequest) -> Dict[str, Any]:
    result=request.solverResult
    validation=validate_solver_result(result)
    if not validation["valid"]: raise HTTPException(status_code=422,detail={"solverResultInvalid":validation["reasons"]})
    eid=(request.coreExecutionId or "").strip()
    execution_object=result.get("executionObject") or {}
    registration=[]
    if eid:
        item = OutputItem(
            outputKey="numerical-solver-result", outputType="result_bundle",
            objectRef=execution_object.get("objectRef", ""), contentHash=result.get("solverRunHash", ""),
            schema={"schema": SOLVER_RESULT_SCHEMA, "version": VERSION},
            metadata={
                "solverKey":result.get("solverKey"), "problemKind":result.get("problemKind"),
                "diagnosticsHash":(result.get("diagnostics") or {}).get("diagnosticsHash"),
                "workbenchVersion":VERSION,
            },
            provenance={"solverRuntimeRef":SOLVER_REF,"executionObjectHash":execution_object.get("objectHash","")},
            createdBy=request.createdBy,
        )
        registration=[_request(CORE_PATHS["outputs"].format(execution_id=eid), _output_data(item), "register-numerical-solver-result")]
    record={
        "ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,
        "coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,
        "solverRunHash":result.get("solverRunHash"),"coreExecutionIdProvided":bool(eid),
        "coreExecutionIdMustComeFromCore":not bool(eid),"outputRegistrations":registration,
        "automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,
        "coreExecutesNumericalSolver":False,"scientificValidityCertified":False,
    }
    record["planHash"]=content_hash(record)
    return record


def manifest() -> Dict[str, Any]:
    record={
        "ok":True,"schema":SCHEMA,"version":VERSION,"product":PRODUCT_KEY,"runtime":RUNTIME_KIND,
        "solverRuntimeRef":SOLVER_REF,"coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,
        "problemKinds":sorted(MODEL_BY_KIND),"solverCount":len(SOLVER_CATALOG),
        "capabilities":{
            "canonicalProblemSpecifications":True,"deterministicSolverSelection":True,
            "normalizedConvergenceDiagnostics":True,"residualAndErrorReporting":True,
            "conditioningDiagnostics":True,"convergenceStudies":True,"workspaceBindingPlanning":True,
            "executionObjectProjection":True,"coreLineagePlanning":True,
        },
        "boundaries":{
            "allowlistedNumericalMethodsOnly":True,"arbitraryCodeExecutionAuthorized":False,
            "pythonEvalAuthorized":False,"shellExecutionAuthorized":False,"automaticSolverFallbackAuthorized":False,
            "automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,
            "scientificValidityCertified":False,"mathematicalProofCertified":False,
        },
    }
    record["manifestHash"]=content_hash(record)
    return record


def catalog() -> Dict[str, Any]:
    solvers=[]
    for key in sorted(SOLVER_CATALOG):
        solvers.append({"solverKey":key,**SOLVER_CATALOG[key],"operation":OPERATION_BY_KIND[SOLVER_CATALOG[key]["problemKind"]]})
    return {"ok":True,"schema":"sc-workbench-numerical-solver-catalog/1.0","version":VERSION,"solvers":solvers,"solverCount":len(solvers),"defaultSolvers":DEFAULT_SOLVER}


@router.get("/solvers/manifest")
def get_manifest(): return manifest()

@router.get("/solvers/catalog")
def get_catalog(): return catalog()

@router.post("/solvers/solve")
def post_solve(request: SolverRequest): return solve(request)

@router.post("/solvers/validate")
def post_validate(result: Dict[str, Any]): return validate_solver_result(result)

@router.post("/solvers/convergence-study")
def post_convergence_study(request: ConvergenceStudyRequest): return convergence_study(request)

@router.post("/solvers/workspace-binding/plan")
def post_workspace_binding(request: WorkspaceSolverBindingRequest): return workspace_binding_plan(request)

@router.post("/integration/core/solver-lineage/plan")
def post_core_lineage(request: CoreSolverLineagePlanRequest, x_sc_service_token: Optional[str]=Header(default=None,alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token); return core_lineage_plan(request)

@router.get("/v740/status")
def status():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":"Numerical Methods & Solver Runtime","solverCount":len(SOLVER_CATALOG),"problemKinds":sorted(MODEL_BY_KIND),"convergenceDiagnostics":True,"workspaceBindingPlanning":True,"coreLineagePlanning":True,"automaticSolverFallback":False,"automaticCoreDispatch":False}

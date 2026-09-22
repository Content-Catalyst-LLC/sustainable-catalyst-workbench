"""Workbench v7.7.0 — Optimization & Design Space Exploration.

Bounded design-variable spaces, explicit objectives and constraints, deterministic
full-factorial exploration, Pareto-frontier extraction, and constrained weighted-
sum optimization. The runtime reuses the established Workbench execution/object
and data-workspace contracts. It does not silently normalize objectives, select a
"best" design on behalf of the user, certify safety/compliance, or automatically
write to Platform Core.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import product
from math import isfinite
from typing import Any, Dict, List, Literal, Optional

import numpy as np
from scipy import optimize as scipy_optimize
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import RestrictedSympyParser, content_hash
from .v640 import _authorize_core_route
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT, CORE_PATHS, OutputItem, _output_data, _request
from .v700 import RESULT_SCHEMA
from .v710 import _execution_object_from_result
from .v730 import _workspace_ok, _set_path, _unit

VERSION = APP_VERSION
SCHEMA = "sc-workbench-optimization-design-space-runtime/1.0"
RESULT_SCHEMA_V770 = "sc-workbench-design-optimization-result/1.0"
EXPLORATION_SCHEMA = "sc-workbench-design-space-exploration/1.0"
PARETO_SCHEMA = "sc-workbench-pareto-frontier/1.0"
BINDING_SCHEMA = "sc-workbench-design-space-workspace-binding-plan/1.0"
HANDOFF_SCHEMA = "sc-workbench-design-candidate-handoff-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-design-space-core-lineage-plan/1.0"
DESIGN_REF = "workbench:/runtime/optimization-design-space"
CORE_LINEAGE_CONTRACT_LITERAL = "sc.research.computation-analysis-execution-lineage.v1"
MAX_VARIABLES = 10
MAX_OBJECTIVES = 8
MAX_CONSTRAINTS = 30
MAX_GRID_POINTS = 4096
MAX_BINDINGS = 200

router = APIRouter(tags=["workbench-v770-optimization-design-space"])


class DesignVariable(BaseModel):
    variableKey: str = Field(min_length=1, max_length=120)
    lowerBound: float
    upperBound: float
    initial: Optional[float] = None
    unit: str = Field(default="", max_length=128)
    gridPoints: int = Field(default=7, ge=2, le=31)
    label: str = Field(default="", max_length=300)

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str) -> str:
        return _unit(v)

    @model_validator(mode="after")
    def validate_bounds(self):
        lo, hi = float(self.lowerBound), float(self.upperBound)
        if not (isfinite(lo) and isfinite(hi)) or not lo < hi:
            raise ValueError("design-variable bounds must be finite and lowerBound < upperBound")
        if self.initial is not None:
            x = float(self.initial)
            if not isfinite(x) or not lo <= x <= hi:
                raise ValueError("initial must be finite and within bounds")
        return self


class ObjectiveSpec(BaseModel):
    objectiveKey: str = Field(min_length=1, max_length=120)
    expression: str = Field(min_length=1, max_length=2000)
    goal: Literal["minimize", "maximize"] = "minimize"
    weight: float = Field(default=1.0, gt=0, le=1e9)
    unit: str = Field(default="", max_length=128)
    label: str = Field(default="", max_length=300)

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str) -> str:
        return _unit(v)


class ConstraintSpec(BaseModel):
    constraintKey: str = Field(min_length=1, max_length=120)
    expression: str = Field(min_length=1, max_length=2000)
    relation: Literal["<=", ">=", "=="] = "<="
    rhs: float = 0.0
    tolerance: float = Field(default=1e-8, ge=0, le=1e-2)
    unit: str = Field(default="", max_length=128)

    @field_validator("unit")
    @classmethod
    def unit_valid(cls, v: str) -> str:
        return _unit(v)


class DesignSpaceSpec(BaseModel):
    designSpaceKey: str = Field(default="design-space", min_length=1, max_length=120)
    variables: List[DesignVariable] = Field(min_length=1, max_length=MAX_VARIABLES)
    objectives: List[ObjectiveSpec] = Field(min_length=1, max_length=MAX_OBJECTIVES)
    constraints: List[ConstraintSpec] = Field(default_factory=list, max_length=MAX_CONSTRAINTS)
    parameters: Dict[str, float] = Field(default_factory=dict, max_length=100)
    projectRef: str = Field(default="", max_length=1000)
    coreSessionId: str = Field(default="", max_length=128)
    workspaceRef: str = Field(default="", max_length=1000)
    workspaceHash: str = Field(default="", max_length=128)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def unique_keys(self):
        for label, values in (
            ("variable", [x.variableKey for x in self.variables]),
            ("objective", [x.objectiveKey for x in self.objectives]),
            ("constraint", [x.constraintKey for x in self.constraints]),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} keys must be unique")
        for k, v in self.parameters.items():
            if not isfinite(float(v)):
                raise ValueError(f"parameter {k} must be finite")
        return self


class PointEvaluationRequest(BaseModel):
    designSpace: DesignSpaceSpec
    point: Dict[str, float]


class ExplorationRequest(BaseModel):
    designSpace: DesignSpaceSpec
    maxPoints: int = Field(default=MAX_GRID_POINTS, ge=2, le=MAX_GRID_POINTS)


class OptimizationRequest(BaseModel):
    designSpace: DesignSpaceSpec
    initialPoint: Dict[str, float] = Field(default_factory=dict)
    tolerance: float = Field(default=1e-8, gt=0, le=1e-2)
    maxIterations: int = Field(default=500, ge=20, le=3000)
    requestKey: str = Field(default="", max_length=180)
    label: str = Field(default="", max_length=400)
    inputRefs: List[str] = Field(default_factory=list, max_length=200)
    datasetRefs: List[str] = Field(default_factory=list, max_length=100)
    tags: List[str] = Field(default_factory=list, max_length=100)


class WorkspaceVariableBinding(BaseModel):
    sourceKind: Literal["variable", "parameter"]
    sourceKey: str
    parameterSetKey: str = Field(default="", max_length=120)
    designVariableKey: str = Field(min_length=1, max_length=120)
    bindField: Literal["initial", "lowerBound", "upperBound"] = "initial"


class WorkspaceBindingRequest(BaseModel):
    workspace: Dict[str, Any]
    designSpace: DesignSpaceSpec
    bindings: List[WorkspaceVariableBinding] = Field(default_factory=list, max_length=MAX_BINDINGS)


class CandidateFieldBinding(BaseModel):
    variableKey: str = Field(min_length=1, max_length=120)
    targetField: str = Field(min_length=1, max_length=300)


class CandidateHandoffRequest(BaseModel):
    candidatePoint: Dict[str, float]
    targetKind: Literal["engineering", "simulation"]
    targetRequest: Dict[str, Any]
    bindings: List[CandidateFieldBinding] = Field(default_factory=list, max_length=MAX_BINDINGS)


class CoreLineagePlanRequest(BaseModel):
    designResult: Dict[str, Any]
    coreExecutionId: str = Field(default="", max_length=128)
    createdBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _compiled(space: DesignSpaceSpec):
    names = [v.variableKey for v in space.variables]
    parser = RestrictedSympyParser(names + list(space.parameters.keys()))
    symbols = {name: parser.symbol(name) for name in names}
    params = {parser.symbol(k): float(v) for k, v in space.parameters.items()}
    objectives = [(obj, parser.parse(obj.expression)) for obj in space.objectives]
    constraints = [(con, parser.parse(con.expression)) for con in space.constraints]
    return parser, symbols, params, objectives, constraints


def _point(space: DesignSpaceSpec, values: Dict[str, float]) -> Dict[str, float]:
    out = {}
    for var in space.variables:
        if var.variableKey not in values:
            raise ValueError(f"missing design variable: {var.variableKey}")
        x = float(values[var.variableKey])
        if not isfinite(x) or not float(var.lowerBound) <= x <= float(var.upperBound):
            raise ValueError(f"{var.variableKey} must be finite and within declared bounds")
        out[var.variableKey] = x
    unknown = set(values) - set(out)
    if unknown:
        raise ValueError(f"unknown design variables: {sorted(unknown)}")
    return out


def _eval_expr(expr, substitutions: Dict[Any, float], label: str) -> float:
    try:
        value = float(expr.evalf(subs=substitutions))
    except Exception as exc:
        raise ValueError(f"{label} could not be evaluated: {exc}") from exc
    if not isfinite(value):
        raise ValueError(f"{label} did not evaluate to a finite value")
    return value


def evaluate_point(request: PointEvaluationRequest) -> Dict[str, Any]:
    space = request.designSpace
    point = _point(space, request.point)
    _, symbols, params, objectives, constraints = _compiled(space)
    subs = {symbols[k]: v for k, v in point.items()}
    subs.update(params)
    obj_values = []
    for obj, expr in objectives:
        val = _eval_expr(expr, subs, f"objective {obj.objectiveKey}")
        obj_values.append({"objectiveKey": obj.objectiveKey, "goal": obj.goal, "weight": obj.weight, "value": val, "unit": obj.unit})
    con_values = []
    feasible = True
    for con, expr in constraints:
        value = _eval_expr(expr, subs, f"constraint {con.constraintKey}")
        residual = value - float(con.rhs)
        if con.relation == "<=": satisfied = residual <= con.tolerance
        elif con.relation == ">=": satisfied = residual >= -con.tolerance
        else: satisfied = abs(residual) <= con.tolerance
        feasible = feasible and satisfied
        con_values.append({"constraintKey": con.constraintKey, "relation": con.relation, "value": value, "rhs": con.rhs, "residual": residual, "tolerance": con.tolerance, "satisfied": satisfied, "unit": con.unit})
    record = {"ok": True, "schema": "sc-workbench-design-point-evaluation/1.0", "version": VERSION, "designSpaceKey": space.designSpaceKey, "point": point, "objectives": obj_values, "constraints": con_values, "feasible": feasible}
    record["evaluationHash"] = content_hash(record)
    return record


def explore(request: ExplorationRequest) -> Dict[str, Any]:
    space = request.designSpace
    axes = [np.linspace(v.lowerBound, v.upperBound, v.gridPoints).tolist() for v in space.variables]
    count = 1
    for axis in axes: count *= len(axis)
    if count > request.maxPoints:
        raise HTTPException(status_code=422, detail=f"declared full-factorial grid has {count} points; maxPoints={request.maxPoints}")
    points = []
    for values in product(*axes):
        candidate = {v.variableKey: float(x) for v, x in zip(space.variables, values)}
        points.append(evaluate_point(PointEvaluationRequest(designSpace=space, point=candidate)))
    feasible_count = sum(1 for p in points if p["feasible"])
    record = {"ok": True, "schema": EXPLORATION_SCHEMA, "version": VERSION, "designSpaceKey": space.designSpaceKey, "strategy": "full-factorial", "pointCount": len(points), "feasibleCount": feasible_count, "infeasibleCount": len(points)-feasible_count, "points": points, "automaticBestDesignSelected": False, "automaticObjectiveNormalizationPerformed": False}
    record["explorationHash"] = content_hash({k:v for k,v in record.items() if k != "explorationHash"})
    return record


def pareto_frontier(exploration: Dict[str, Any]) -> Dict[str, Any]:
    if exploration.get("schema") != EXPLORATION_SCHEMA or exploration.get("version") != VERSION:
        raise HTTPException(status_code=422, detail="exploration must be a current v7.7 design-space exploration object")
    expected = content_hash({k:v for k,v in exploration.items() if k != "explorationHash"})
    if exploration.get("explorationHash") != expected:
        raise HTTPException(status_code=422, detail="exploration integrity hash mismatch")
    feasible = [p for p in exploration.get("points", []) if p.get("feasible")]
    frontier = []
    for i, candidate in enumerate(feasible):
        dominated = False
        cvals = candidate.get("objectives", [])
        for j, other in enumerate(feasible):
            if i == j: continue
            ovals = other.get("objectives", [])
            no_worse, strictly_better = True, False
            for cv, ov in zip(cvals, ovals):
                if cv.get("goal") == "minimize":
                    if float(ov["value"]) > float(cv["value"]): no_worse = False; break
                    if float(ov["value"]) < float(cv["value"]): strictly_better = True
                else:
                    if float(ov["value"]) < float(cv["value"]): no_worse = False; break
                    if float(ov["value"]) > float(cv["value"]): strictly_better = True
            if no_worse and strictly_better:
                dominated = True; break
        if not dominated: frontier.append(candidate)
    record = {"ok": True, "schema": PARETO_SCHEMA, "version": VERSION, "designSpaceKey": exploration.get("designSpaceKey"), "explorationHash": exploration.get("explorationHash"), "feasiblePointCount": len(feasible), "frontierPointCount": len(frontier), "frontier": frontier, "automaticTradeoffPreferenceApplied": False, "automaticWinnerSelected": False}
    record["paretoHash"] = content_hash({k:v for k,v in record.items() if k != "paretoHash"})
    return record


def _source_envelope(request: OptimizationRequest, raw: Dict[str, Any]) -> Dict[str, Any]:
    stable = {"designSpace": request.designSpace.model_dump(), "initialPoint": request.initialPoint, "tolerance": request.tolerance, "maxIterations": request.maxIterations, "requestKey": request.requestKey}
    request_hash = content_hash(stable); execution_id = "wbe-opt-" + request_hash[:20]; execution_ref = f"sc://workbench/execution/{execution_id}"; result_hash = content_hash(raw); output_ref = f"{execution_ref}/result/{result_hash[:16]}"
    return {"ok": bool(raw.get("success", False)), "schema": RESULT_SCHEMA, "version": VERSION, "runtimeRef": DESIGN_REF, "executionId": execution_id, "executionRef": execution_ref, "requestKey": request.requestKey or execution_id, "label": request.label or request.designSpace.designSpaceKey, "operation": "design-space.optimize", "category": "optimization-design-space", "executionType": "design_optimization", "runtimeKind": "workbench", "sourceRelease": "7.7.0", "deterministicOperation": True, "projectRef": request.designSpace.projectRef, "coreSessionId": request.designSpace.coreSessionId, "inputRefs": sorted(set(request.inputRefs)), "outputRef": output_ref, "outputType": "result_bundle", "requestHash": request_hash, "resultHash": result_hash, "result": raw, "provenance": {"product": PRODUCT_KEY, "workbenchVersion": VERSION, "runtimeRef": DESIGN_REF, "operation": "design-space.optimize", "resultContentHash": result_hash}, "lineageHints": {"executionType": "design_optimization", "runtimeKind": "workbench", "workbenchExecutionRef": execution_ref, "inputRefs": sorted(set(request.inputRefs)), "outputRefs": [output_ref]}, "boundaries": {"specialistComputationPerformedByWorkbench": True, "automaticCoreDispatchPerformed": False, "automaticCorePersistencePerformed": False, "engineeringCertificationPerformed": False}}


def optimize(request: OptimizationRequest) -> Dict[str, Any]:
    space = request.designSpace
    _, symbols, params, objectives, constraints = _compiled(space)
    names = [v.variableKey for v in space.variables]
    bounds = [(float(v.lowerBound), float(v.upperBound)) for v in space.variables]
    initial = []
    for v in space.variables:
        if v.variableKey in request.initialPoint: x = float(request.initialPoint[v.variableKey])
        elif v.initial is not None: x = float(v.initial)
        else: x = (float(v.lowerBound)+float(v.upperBound))/2
        if not bounds[len(initial)][0] <= x <= bounds[len(initial)][1]: raise HTTPException(status_code=422, detail=f"initial point for {v.variableKey} outside bounds")
        initial.append(x)

    def subs(values):
        d = {symbols[k]: float(v) for k, v in zip(names, values)}; d.update(params); return d

    def weighted(values):
        s = subs(values); total = 0.0
        for obj, expr in objectives:
            val = _eval_expr(expr, s, f"objective {obj.objectiveKey}")
            total += float(obj.weight) * (val if obj.goal == "minimize" else -val)
        return total

    scipy_constraints = []
    for con, expr in constraints:
        rhs, tol = float(con.rhs), float(con.tolerance)
        if con.relation == "<=":
            scipy_constraints.append({"type":"ineq", "fun": lambda x, e=expr, r=rhs, t=tol: r + t - _eval_expr(e, subs(x), "constraint")})
        elif con.relation == ">=":
            scipy_constraints.append({"type":"ineq", "fun": lambda x, e=expr, r=rhs, t=tol: _eval_expr(e, subs(x), "constraint") - r + t})
        else:
            scipy_constraints.append({"type":"eq", "fun": lambda x, e=expr, r=rhs: _eval_expr(e, subs(x), "constraint") - r})
    try:
        raw_result = scipy_optimize.minimize(weighted, np.asarray(initial, dtype=float), method="SLSQP", bounds=bounds, constraints=scipy_constraints, options={"maxiter": request.maxIterations, "ftol": request.tolerance})
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"optimization could not complete: {exc}") from exc
    point = {k: float(v) for k, v in zip(names, raw_result.x)}
    evaluation = evaluate_point(PointEvaluationRequest(designSpace=space, point=point))
    raw = {"success": bool(raw_result.success) and bool(evaluation["feasible"]), "solverSuccess": bool(raw_result.success), "message": str(raw_result.message), "method": "SLSQP", "iterations": int(raw_result.nit), "functionEvaluations": int(raw_result.nfev), "weightedObjectiveValue": float(raw_result.fun), "point": point, "evaluation": evaluation, "objectiveWeights": {o.objectiveKey:o.weight for o in space.objectives}, "automaticObjectiveNormalizationPerformed": False, "automaticWinnerSelectionPerformed": False}
    source = _source_envelope(request, raw)
    obj = _execution_object_from_result(source, declared_request={"payload": space.model_dump(), "inputRefs": request.inputRefs, "requestKey": request.requestKey}, object_key=request.requestKey, label=request.label, project_ref=space.projectRef, core_session_id=space.coreSessionId, dataset_refs=request.datasetRefs, method_refs=[DESIGN_REF, "SLSQP", "explicit-weighted-sum"], tags=request.tags, metadata={"designSpaceKey":space.designSpaceKey,"workspaceRef":space.workspaceRef,"workspaceHash":space.workspaceHash})
    diagnostics = {"converged": bool(raw_result.success), "feasible": bool(evaluation["feasible"]), "iterations": int(raw_result.nit), "functionEvaluations": int(raw_result.nfev), "constraintCount": len(space.constraints), "objectiveCount": len(space.objectives), "designVariableCount": len(space.variables), "solver":"SLSQP", "explicitWeightsRequired": True, "automaticObjectiveNormalizationPerformed": False}
    diagnostics["diagnosticsHash"] = content_hash(diagnostics)
    record = {"ok": bool(raw["success"]), "schema": RESULT_SCHEMA_V770, "version": VERSION, "designRuntimeRef": DESIGN_REF, "designSpace": space.model_dump(), "result": raw, "diagnostics": diagnostics, "executionObject": obj, "automaticBestDesignSelected": False, "automaticObjectivePreferenceInferred": False, "automaticCoreDispatchPerformed": False, "automaticCorePersistencePerformed": False, "engineeringSafetyCertified": False, "codeComplianceCertified": False}
    record["designRunHash"] = content_hash({"designSpace":record["designSpace"],"result":record["result"],"diagnosticsHash":diagnostics["diagnosticsHash"],"executionObjectHash":obj["objectHash"]})
    return record


def validate_result(result: Dict[str, Any]) -> Dict[str, Any]:
    reasons=[]
    if result.get("schema") != RESULT_SCHEMA_V770: reasons.append("schema-mismatch")
    if result.get("version") != VERSION: reasons.append("version-mismatch")
    diag=result.get("diagnostics") or {}; expected_diag=content_hash({k:v for k,v in diag.items() if k!="diagnosticsHash"}) if diag else ""
    if diag.get("diagnosticsHash") != expected_diag: reasons.append("diagnostics-hash-mismatch")
    expected=content_hash({"designSpace":result.get("designSpace"),"result":result.get("result"),"diagnosticsHash":diag.get("diagnosticsHash"),"executionObjectHash":(result.get("executionObject") or {}).get("objectHash")})
    if result.get("designRunHash") != expected: reasons.append("design-run-hash-mismatch")
    return {"ok":not reasons,"schema":"sc-workbench-design-optimization-validation/1.0","version":VERSION,"valid":not reasons,"reasons":reasons,"designRunHash":result.get("designRunHash","")}


def workspace_binding_plan(request: WorkspaceBindingRequest) -> Dict[str, Any]:
    ws=request.workspace; _workspace_ok(ws)
    variables={x["variableKey"]:x for x in ws.get("variables",[]) if isinstance(x,dict)}; psets={x["parameterSetKey"]:x for x in ws.get("parameterSets",[]) if isinstance(x,dict)}
    space=deepcopy(request.designSpace.model_dump()); dvars={x["variableKey"]:x for x in space["variables"]}; materialized=[]
    for b in request.bindings:
        if b.designVariableKey not in dvars: raise HTTPException(status_code=422, detail=f"unknown design variable: {b.designVariableKey}")
        if b.sourceKind=="variable":
            src=variables.get(b.sourceKey)
            if not src: raise HTTPException(status_code=422,detail=f"unknown variable: {b.sourceKey}")
            value=src.get("derivedValue") if src.get("expression") else src.get("value"); ref=src.get("variableRef","")
        else:
            ps=psets.get(b.parameterSetKey)
            if not ps: raise HTTPException(status_code=422,detail=f"unknown parameter set: {b.parameterSetKey}")
            src=next((p for p in ps.get("parameters",[]) if p.get("parameterKey")==b.sourceKey),None)
            if not src: raise HTTPException(status_code=422,detail=f"unknown parameter: {b.sourceKey}")
            value=src.get("value"); ref=src.get("parameterRef","")
        if not isinstance(value,(int,float)) or isinstance(value,bool) or not isfinite(float(value)): raise HTTPException(status_code=422,detail="design-space bindings require finite scalar values")
        dvars[b.designVariableKey][b.bindField]=float(value); materialized.append({"sourceRef":ref,"designVariableKey":b.designVariableKey,"bindField":b.bindField,"value":float(value)})
    bound=DesignSpaceSpec.model_validate(space)
    record={"ok":True,"schema":BINDING_SCHEMA,"version":VERSION,"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],"designSpace":bound.model_dump(),"materializedBindings":materialized,"executionPerformed":False,"automaticDispatchAuthorized":False}
    record["bindingPlanHash"]=content_hash(record); return record


def candidate_handoff_plan(request: CandidateHandoffRequest) -> Dict[str, Any]:
    target=deepcopy(request.targetRequest)
    for b in request.bindings:
        if b.variableKey not in request.candidatePoint: raise HTTPException(status_code=422,detail=f"candidate missing variable {b.variableKey}")
        _set_path(target,b.targetField,float(request.candidatePoint[b.variableKey]))
    path="/engineering/analyze" if request.targetKind=="engineering" else "/simulations/run"
    record={"ok":True,"schema":HANDOFF_SCHEMA,"version":VERSION,"targetKind":request.targetKind,"targetPath":path,"preparedRequest":target,"candidatePoint":request.candidatePoint,"bindingCount":len(request.bindings),"executionPerformed":False,"automaticDispatchAuthorized":False,"automaticCrossDomainCouplingPerformed":False}
    record["handoffPlanHash"]=content_hash(record); return record


def core_lineage_plan(request: CoreLineagePlanRequest) -> Dict[str, Any]:
    result=request.designResult; validation=validate_result(result)
    if not validation["valid"]: raise HTTPException(status_code=422,detail={"designResultInvalid":validation["reasons"]})
    eid=(request.coreExecutionId or "").strip(); obj=result.get("executionObject") or {}; regs=[]
    if eid:
        item=OutputItem(outputKey="design-optimization-result",outputType="result_bundle",objectRef=obj.get("objectRef",""),contentHash=result.get("designRunHash",""),schema={"schema":RESULT_SCHEMA_V770,"version":VERSION},metadata={"designSpaceKey":(result.get("designSpace") or {}).get("designSpaceKey"),"diagnosticsHash":(result.get("diagnostics") or {}).get("diagnosticsHash"),"workbenchVersion":VERSION},provenance={"designRuntimeRef":DESIGN_REF,"executionObjectHash":obj.get("objectHash","")},createdBy=request.createdBy)
        regs=[_request(CORE_PATHS["outputs"].format(execution_id=eid),_output_data(item),"register-design-optimization-result")]
    record={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,"designRunHash":result.get("designRunHash"),"coreExecutionIdProvided":bool(eid),"coreExecutionIdMustComeFromCore":not bool(eid),"outputRegistrations":regs,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"coreExecutesOptimization":False,"automaticBestDesignSelectionAuthorized":False}
    record["planHash"]=content_hash(record); return record


def manifest() -> Dict[str, Any]:
    record={"ok":True,"schema":SCHEMA,"version":VERSION,"product":PRODUCT_KEY,"runtime":RUNTIME_KIND,"designRuntimeRef":DESIGN_REF,"coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,"limits":{"maxVariables":MAX_VARIABLES,"maxObjectives":MAX_OBJECTIVES,"maxConstraints":MAX_CONSTRAINTS,"maxGridPoints":MAX_GRID_POINTS},"capabilities":{"boundedDesignVariables":True,"explicitObjectives":True,"explicitConstraints":True,"fullFactorialExploration":True,"paretoFrontierExtraction":True,"weightedSumConstrainedOptimization":True,"workspaceBindingPlanning":True,"engineeringSimulationCandidateHandoffs":True,"executionObjectProjection":True,"coreLineagePlanning":True},"boundaries":{"boundedDesignSpacesOnly":True,"arbitraryCodeExecutionAuthorized":False,"automaticObjectiveNormalizationAuthorized":False,"automaticPreferenceInferenceAuthorized":False,"automaticWinnerSelectionAuthorized":False,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"engineeringSafetyCertificationAuthorized":False,"codeComplianceCertificationAuthorized":False}}
    record["manifestHash"]=content_hash(record); return record


@router.get("/design-space/manifest")
def get_manifest(): return manifest()

@router.post("/design-space/evaluate")
def post_evaluate(request: PointEvaluationRequest):
    try: return evaluate_point(request)
    except HTTPException: raise
    except Exception as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc

@router.post("/design-space/explore")
def post_explore(request: ExplorationRequest):
    try: return explore(request)
    except HTTPException: raise
    except Exception as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc

@router.post("/design-space/pareto")
def post_pareto(exploration: Dict[str, Any]): return pareto_frontier(exploration)

@router.post("/design-space/optimize")
def post_optimize(request: OptimizationRequest): return optimize(request)

@router.post("/design-space/validate")
def post_validate(result: Dict[str, Any]): return validate_result(result)

@router.post("/design-space/workspace-binding/plan")
def post_workspace_binding(request: WorkspaceBindingRequest): return workspace_binding_plan(request)

@router.post("/design-space/candidate-handoff/plan")
def post_candidate_handoff(request: CandidateHandoffRequest): return candidate_handoff_plan(request)

@router.post("/integration/core/design-space-lineage/plan")
def post_core(request: CoreLineagePlanRequest, x_sc_service_token: Optional[str]=Header(default=None,alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token); return core_lineage_plan(request)

@router.get("/v770/status")
def status():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":"Optimization & Design Space Exploration","boundedDesignVariables":True,"multiObjective":True,"constraints":True,"paretoFrontier":True,"fullFactorialExploration":True,"weightedSumOptimization":True,"workspaceBindingPlanning":True,"candidateHandoffPlanning":True,"coreLineagePlanning":True,"automaticWinnerSelection":False,"automaticObjectiveNormalization":False,"automaticCoreDispatch":False}

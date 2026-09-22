"""Workbench v7.5.0 — Simulation & Dynamical Systems Runtime.

Promotes the bounded simulation capabilities accumulated across Workbench into a
canonical dynamical-systems layer. It normalizes simulation specifications,
trajectories, stability/event diagnostics, bounded parameter sweeps, v7.3
workspace bindings, v7.1 execution objects, and Platform Core computation
lineage plans without authorizing arbitrary code or automatic Core dispatch.
"""
from __future__ import annotations

from copy import deepcopy
from math import isfinite
from typing import Any, Dict, List, Literal, Optional

import numpy as np
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash
from .v640 import _authorize_core_route
from .v670 import CORE_COMPUTATION_LINEAGE_CONTRACT, CORE_PATHS, OutputItem, _output_data, _request
from .v720 import OrchestratedExecutionRequest, orchestrated_execute
from .v730 import _workspace_ok, _set_path
from .v740 import SolverRequest, solve as solve_numerical

VERSION = APP_VERSION
SCHEMA = "sc-workbench-simulation-dynamical-systems-runtime/1.0"
SIMULATION_RESULT_SCHEMA = "sc-workbench-dynamical-simulation-result/1.0"
SWEEP_SCHEMA = "sc-workbench-dynamical-parameter-sweep/1.0"
WORKSPACE_BINDING_SCHEMA = "sc-workbench-simulation-workspace-binding-plan/1.0"
CORE_PLAN_SCHEMA = "sc-workbench-simulation-core-lineage-plan/1.0"
SIMULATION_REF = "workbench:/runtime/simulation-dynamical-systems"
CORE_LINEAGE_CONTRACT_LITERAL = "sc.research.computation-analysis-execution-lineage.v1"
MAX_EVENTS = 50
MAX_SWEEP_POINTS = 101
MAX_BINDINGS = 200

SimulationKind = Literal["scalar-dynamic", "linear-state-space", "ode-ivp", "digital-twin"]
EventDirection = Literal["any", "rising", "falling"]
router = APIRouter(tags=["workbench-v750-simulation-dynamical-systems"])

SIMULATION_CATALOG: Dict[str, Dict[str, Any]] = {
    "scalar-dynamic": {
        "operation": "simulation.dynamic", "runtime": "workbench.simulation",
        "modelTypes": ["first_order", "logistic", "damped"], "bounded": True,
    },
    "linear-state-space": {
        "operation": "simulation.state-space-system", "runtime": "workbench.simulation",
        "solvers": ["euler", "rk4"], "bounded": True,
    },
    "ode-ivp": {
        "operation": "numerical.ode", "runtime": "workbench.numerical",
        "solvers": ["RK45", "DOP853", "Radau", "BDF"], "bounded": True,
    },
    "digital-twin": {
        "operation": "simulation.digital-twin", "runtime": "workbench.simulation",
        "calibration": "bounded-grid-search", "bounded": True,
    },
}


class EventSpec(BaseModel):
    eventKey: str = Field(min_length=1, max_length=120)
    stateKey: str = Field(default="state", max_length=120)
    threshold: float
    direction: EventDirection = "any"
    terminal: bool = False


class SimulationRequest(BaseModel):
    simulationKind: SimulationKind
    model: Dict[str, Any]
    events: List[EventSpec] = Field(default_factory=list, max_length=MAX_EVENTS)
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

    @field_validator("events")
    @classmethod
    def unique_event_keys(cls, events):
        keys=[e.eventKey for e in events]
        if len(keys)!=len(set(keys)): raise ValueError("eventKey values must be unique")
        return events


class SweepRequest(BaseModel):
    baseSimulation: SimulationRequest
    parameterPath: str = Field(min_length=1, max_length=200)
    values: List[float] = Field(min_length=2, max_length=MAX_SWEEP_POINTS)
    metric: Literal["final-state", "maximum-state", "minimum-state", "duration"] = "final-state"
    requestKey: str = Field(default="parameter-sweep", max_length=180)

    @field_validator("values")
    @classmethod
    def finite_values(cls, values):
        if any(not isfinite(float(v)) for v in values): raise ValueError("sweep values must be finite")
        return values


class BindingSpec(BaseModel):
    sourceKind: Literal["variable", "parameter", "dataset"]
    sourceKey: str
    parameterSetKey: str = Field(default="", max_length=120)
    targetField: str = Field(default="", max_length=300)


class WorkspaceSimulationBindingRequest(BaseModel):
    workspace: Dict[str, Any]
    simulationKind: SimulationKind
    model: Dict[str, Any] = Field(default_factory=dict)
    events: List[EventSpec] = Field(default_factory=list, max_length=MAX_EVENTS)
    bindings: List[BindingSpec] = Field(default_factory=list, max_length=MAX_BINDINGS)
    requestKey: str = Field(default="", max_length=180)
    label: str = Field(default="", max_length=400)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CoreSimulationLineagePlanRequest(BaseModel):
    simulationResult: Dict[str, Any]
    coreExecutionId: str = Field(default="", max_length=128)
    createdBy: str = Field(default=f"workbench-v{VERSION}", max_length=180)


def _unwrap_execution(orchestration: Dict[str, Any]) -> Dict[str, Any]:
    execution=orchestration.get("executionResult", {})
    raw=execution.get("result", {})
    if isinstance(raw, dict) and "result" in raw and isinstance(raw["result"], dict):
        return raw["result"]
    return raw if isinstance(raw, dict) else {}


def _run_underlying(request: SimulationRequest) -> Dict[str, Any]:
    kind=request.simulationKind
    if kind=="ode-ivp":
        solver_key={"RK45":"ode.rk45","DOP853":"ode.dop853","Radau":"ode.radau","BDF":"ode.bdf"}.get(str(request.model.get("method","RK45")),"ode.rk45")
        result=solve_numerical(SolverRequest(
            problemKind="ode", problem=request.model, solverKey=solver_key,
            projectRef=request.projectRef, coreSessionId=request.coreSessionId,
            requestKey=request.requestKey or "simulation:ode-ivp", label=request.label or "ODE simulation",
            workspaceRef=request.workspaceRef, workspaceHash=request.workspaceHash,
            inputRefs=request.inputRefs, datasetRefs=request.datasetRefs,
            methodRefs=[SIMULATION_REF, *request.methodRefs], tags=request.tags,
            metadata={**request.metadata,"simulationKind":kind},
        ))
        return {"mode":"solver-runtime","orchestration":result.get("orchestration",{}),"solverResult":result,"executionObject":result.get("executionObject")}
    operation=SIMULATION_CATALOG[kind]["operation"]
    orchestration=orchestrated_execute(OrchestratedExecutionRequest(
        operation=operation, payload=request.model,
        projectRef=request.projectRef, coreSessionId=request.coreSessionId,
        requestKey=request.requestKey or f"simulation:{kind}", label=request.label or kind,
        inputRefs=request.inputRefs, datasetRefs=request.datasetRefs,
        preferredRuntime="workbench.simulation", methodRefs=[SIMULATION_REF, kind, *request.methodRefs],
        tags=request.tags,
        metadata={**request.metadata,"simulationKind":kind,"workspaceRef":request.workspaceRef,"workspaceHash":request.workspaceHash},
    ))
    return {"mode":"orchestrator","orchestration":orchestration,"executionObject":orchestration.get("executionObject")}


def _trajectory(kind: str, run: Dict[str, Any], model: Dict[str, Any]) -> Dict[str, Any]:
    if kind=="ode-ivp":
        solver=run.get("solverResult",{})
        raw=_unwrap_execution(solver.get("orchestration",{}))
        details=raw.get("result",raw) if isinstance(raw,dict) else {}
        states=[]
        for series in details.get("series",[]):
            states.append({"stateKey":series.get("state"),"points":[{"time":p.get("t"),"value":p.get("value")} for p in series.get("points",[])]})
        times=[p["time"] for p in states[0]["points"]] if states else []
        return {"time":times,"states":states,"finalState":details.get("finalState",{}),"sampleCount":len(times)}
    raw=_unwrap_execution(run.get("orchestration",{}))
    if kind=="scalar-dynamic":
        series=raw.get("series",{})
        times=list(series.get("time",[])); values=list(series.get("values",[])); velocities=list(series.get("velocity",[]))
        states=[{"stateKey":"state","points":[{"time":t,"value":v} for t,v in zip(times,values)]}]
        if velocities and any(abs(float(v))>0 for v in velocities):
            states.append({"stateKey":"velocity","points":[{"time":t,"value":v} for t,v in zip(times,velocities)]})
        return {"time":times,"states":states,"finalState":{"state":values[-1] if values else None},"sampleCount":len(times)}
    if kind=="linear-state-space":
        series=raw.get("series",[]); dt=float(model.get("time_step",0.1)); n=max((len(s) for s in series),default=0); times=[round(i*dt,12) for i in range(n)]
        names=model.get("state_names") or [f"x{i}" for i in range(len(series))]
        states=[]
        for i,values in enumerate(series):
            states.append({"stateKey": names[i] if i<len(names) and names[i] else f"x{i}", "points":[{"time":t,"value":v} for t,v in zip(times,values)]})
        final=raw.get("finalState",[])
        return {"time":times,"states":states,"finalState":{(names[i] if i<len(names) and names[i] else f"x{i}"):v for i,v in enumerate(final)},"sampleCount":len(times)}
    if kind=="digital-twin":
        series=raw.get("series",{}); times=list(series.get("time",[])); predicted=list(series.get("predicted",[])); observed=list(series.get("observed",[]))
        states=[{"stateKey":"predicted","points":[{"time":t,"value":v} for t,v in zip(times,predicted)]}]
        if observed: states.append({"stateKey":"observed","points":[{"time":t,"value":v} for t,v in zip(times,observed)]})
        return {"time":times,"states":states,"finalState":{"predicted":predicted[-1] if predicted else None},"sampleCount":len(times)}
    return {"time":[],"states":[],"finalState":{},"sampleCount":0}


def _stability(kind: str, model: Dict[str, Any], trajectory: Dict[str, Any], run: Dict[str, Any]) -> Dict[str, Any]:
    out={"classification":"not-evaluated","method":"none","established":False}
    if kind=="linear-state-space":
        matrix=np.asarray(model.get("matrix_a",[]),dtype=float)
        if matrix.ndim==2 and matrix.shape[0]==matrix.shape[1] and matrix.size:
            eig=np.linalg.eigvals(matrix)
            max_real=float(np.max(np.real(eig)))
            tol=1e-10
            classification="asymptotically-stable" if max_real < -tol else ("unstable" if max_real > tol else "marginal-or-undetermined")
            out={"classification":classification,"method":"continuous-linear-eigenvalue","established":classification in {"asymptotically-stable","unstable"},"maxRealEigenvalue":round(max_real,12),"eigenvalues":[{"real":round(float(v.real),12),"imag":round(float(v.imag),12)} for v in eig]}
    elif kind=="scalar-dynamic" and model.get("model_type","first_order")=="first_order":
        tau=float(model.get("time_constant",0))
        out={"classification":"asymptotically-stable" if tau>0 else "invalid","method":"first-order-time-constant","established":tau>0,"timeConstant":tau}
    elif kind=="scalar-dynamic" and model.get("model_type")=="logistic":
        gain=float(model.get("gain",0)); capacity=float(model.get("capacity",0))
        out={"classification":"locally-stable-positive-equilibrium" if gain>0 and capacity>0 else "not-established","method":"logistic-local-linearization","established":gain>0 and capacity>0,"equilibrium":capacity if capacity>0 else None}
    elif kind=="ode-ivp":
        out={"classification":"not-automatically-classified","method":"generic-nonlinear-ode","established":False}
    elif kind=="digital-twin":
        raw=_unwrap_execution(run.get("orchestration",{})); metrics=raw.get("metrics",{})
        out={"classification":"calibration-fit-only","method":"observed-vs-predicted-fit","established":False,"r2":metrics.get("r2"),"rmse":metrics.get("rmse")}
    out["stabilityHash"]=content_hash(out)
    return out


def _detect_events(trajectory: Dict[str, Any], specs: List[EventSpec]) -> List[Dict[str, Any]]:
    by_key={s.get("stateKey"):s.get("points",[]) for s in trajectory.get("states",[]) if isinstance(s,dict)}
    events=[]
    for spec in specs:
        points=by_key.get(spec.stateKey,[])
        for prev,curr in zip(points,points[1:]):
            a=float(prev.get("value",0))-spec.threshold; b=float(curr.get("value",0))-spec.threshold
            rising=a<0<=b; falling=a>0>=b; crossed=rising or falling or a==0 or b==0
            if not crossed: continue
            if spec.direction=="rising" and not rising: continue
            if spec.direction=="falling" and not falling: continue
            t0=float(prev.get("time",0)); t1=float(curr.get("time",t0)); denom=abs(a)+abs(b)
            frac=0.0 if denom==0 else abs(a)/denom
            t=t0+(t1-t0)*frac
            events.append({"eventKey":spec.eventKey,"stateKey":spec.stateKey,"threshold":spec.threshold,"direction":"rising" if rising else ("falling" if falling else "touch"),"time":round(t,12),"terminal":spec.terminal})
            break
    return events


def run_simulation(request: SimulationRequest) -> Dict[str, Any]:
    run=_run_underlying(request)
    trajectory=_trajectory(request.simulationKind,run,request.model)
    stability=_stability(request.simulationKind,request.model,trajectory,run)
    events=_detect_events(trajectory,request.events)
    values=[float(p["value"]) for s in trajectory.get("states",[]) for p in s.get("points",[]) if p.get("value") is not None]
    diagnostics={
        "sampleCount":trajectory.get("sampleCount",0),"stateCount":len(trajectory.get("states",[])),
        "eventCount":len(events),"finiteTrajectory":all(isfinite(v) for v in values),
        "minimumObserved":min(values) if values else None,"maximumObserved":max(values) if values else None,
        "stability":stability,
    }
    diagnostics["diagnosticsHash"]=content_hash(diagnostics)
    execution_object=run.get("executionObject")
    record={
        "ok":bool((run.get("solverResult") or run.get("orchestration") or {}).get("ok",True)),
        "schema":SIMULATION_RESULT_SCHEMA,"version":VERSION,"simulationRuntimeRef":SIMULATION_REF,
        "simulationKind":request.simulationKind,"model":request.model,"workspaceRef":request.workspaceRef,"workspaceHash":request.workspaceHash,
        "trajectory":trajectory,"events":events,"diagnostics":diagnostics,"executionObject":execution_object,
        "underlyingRun":run,"automaticModelSelectionPerformed":False,"automaticCoreDispatchPerformed":False,
        "automaticCorePersistencePerformed":False,"scientificValidityCertified":False,
    }
    record["simulationRunHash"]=content_hash({"simulationKind":record["simulationKind"],"model":record["model"],"trajectory":record["trajectory"],"events":events,"diagnosticsHash":diagnostics["diagnosticsHash"],"executionObjectHash":(execution_object or {}).get("objectHash")})
    return record


def validate_simulation_result(result: Dict[str, Any]) -> Dict[str, Any]:
    reasons=[]
    if result.get("schema")!=SIMULATION_RESULT_SCHEMA: reasons.append("schema-mismatch")
    if result.get("version")!=VERSION: reasons.append("version-mismatch")
    if result.get("simulationKind") not in SIMULATION_CATALOG: reasons.append("unknown-simulation-kind")
    diagnostics=result.get("diagnostics") or {}
    expected_diag=content_hash({k:v for k,v in diagnostics.items() if k!="diagnosticsHash"}) if diagnostics else ""
    if diagnostics.get("diagnosticsHash")!=expected_diag: reasons.append("diagnostics-hash-mismatch")
    expected_run=content_hash({"simulationKind":result.get("simulationKind"),"model":result.get("model"),"trajectory":result.get("trajectory"),"events":result.get("events",[]),"diagnosticsHash":diagnostics.get("diagnosticsHash"),"executionObjectHash":(result.get("executionObject") or {}).get("objectHash")})
    if result.get("simulationRunHash")!=expected_run: reasons.append("simulation-run-hash-mismatch")
    return {"ok":not reasons,"schema":"sc-workbench-dynamical-simulation-validation/1.0","version":VERSION,"valid":not reasons,"reasons":reasons,"simulationRunHash":result.get("simulationRunHash","")}


def _metric(result: Dict[str, Any], metric: str) -> Optional[float]:
    traj=result.get("trajectory",{}); states=traj.get("states",[])
    values=[float(p["value"]) for s in states for p in s.get("points",[]) if p.get("value") is not None]
    if metric=="duration":
        times=traj.get("time",[]); return float(times[-1]-times[0]) if len(times)>=2 else None
    if not values: return None
    if metric=="maximum-state": return max(values)
    if metric=="minimum-state": return min(values)
    first=states[0].get("points",[]) if states else []
    return float(first[-1]["value"]) if first else None


def parameter_sweep(request: SweepRequest) -> Dict[str, Any]:
    runs=[]
    for idx,value in enumerate(request.values):
        model=deepcopy(request.baseSimulation.model)
        try: _set_path(model,request.parameterPath,float(value))
        except Exception as exc: raise HTTPException(status_code=422,detail=f"invalid parameterPath: {exc}") from exc
        base=request.baseSimulation
        sim=run_simulation(SimulationRequest(**{**base.model_dump(),"model":model,"requestKey":f"{request.requestKey}:{idx}"}))
        runs.append({"index":idx,"parameterValue":value,"metricValue":_metric(sim,request.metric),"simulationRunHash":sim["simulationRunHash"],"diagnostics":sim["diagnostics"]})
    metrics=[r["metricValue"] for r in runs if r["metricValue"] is not None]
    record={"ok":True,"schema":SWEEP_SCHEMA,"version":VERSION,"parameterPath":request.parameterPath,"metric":request.metric,"runs":runs,"runCount":len(runs),"minimumMetric":min(metrics) if metrics else None,"maximumMetric":max(metrics) if metrics else None,"automaticOptimizationPerformed":False}
    record["sweepHash"]=content_hash(record)
    return record


def workspace_binding_plan(request: WorkspaceSimulationBindingRequest) -> Dict[str, Any]:
    ws=request.workspace; _workspace_ok(ws)
    variables={x["variableKey"]:x for x in ws.get("variables",[]) if isinstance(x,dict)}
    datasets={x["datasetKey"]:x for x in ws.get("datasets",[]) if isinstance(x,dict)}
    parameter_sets={x["parameterSetKey"]:x for x in ws.get("parameterSets",[]) if isinstance(x,dict)}
    model=deepcopy(request.model); input_refs=[]; dataset_refs=[]; materialized=[]
    for binding in request.bindings:
        if binding.sourceKind=="variable":
            src=variables.get(binding.sourceKey)
            if not src: raise HTTPException(status_code=422,detail=f"unknown variable: {binding.sourceKey}")
            value=src.get("derivedValue") if src.get("expression") else src.get("value")
            if value is None or not binding.targetField: raise HTTPException(status_code=422,detail="variable bindings require scalar value and targetField")
            _set_path(model,binding.targetField,value); ref=src["variableRef"]; input_refs.append(ref)
        elif binding.sourceKind=="parameter":
            ps=parameter_sets.get(binding.parameterSetKey)
            if not ps: raise HTTPException(status_code=422,detail=f"unknown parameter set: {binding.parameterSetKey}")
            src=next((x for x in ps.get("parameters",[]) if x.get("parameterKey")==binding.sourceKey),None)
            if not src or not binding.targetField: raise HTTPException(status_code=422,detail="parameter binding requires known parameter and targetField")
            _set_path(model,binding.targetField,src.get("value")); ref=src["parameterRef"]; input_refs.append(ref)
        else:
            src=datasets.get(binding.sourceKey)
            if not src: raise HTTPException(status_code=422,detail=f"unknown dataset: {binding.sourceKey}")
            ref=src["datasetRef"]; input_refs.append(ref); dataset_refs.append(ref)
            if binding.targetField: _set_path(model,binding.targetField,ref)
        materialized.append({"sourceKind":binding.sourceKind,"sourceKey":binding.sourceKey,"sourceRef":ref,"targetField":binding.targetField})
    sim_request={"simulationKind":request.simulationKind,"model":model,"events":[e.model_dump() for e in request.events],"projectRef":ws.get("projectRef",""),"coreSessionId":ws.get("coreSessionId",""),"requestKey":request.requestKey or f"{ws.get('workspaceKey','workspace')}:simulation:{request.simulationKind}","label":request.label,"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],"inputRefs":sorted(set(input_refs)),"datasetRefs":sorted(set(dataset_refs)),"metadata":{"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],**request.metadata}}
    SimulationRequest.model_validate(sim_request)
    record={"ok":True,"schema":WORKSPACE_BINDING_SCHEMA,"version":VERSION,"workspaceRef":ws["workspaceRef"],"workspaceHash":ws["workspaceHash"],"materializedBindings":materialized,"simulationRequest":sim_request,"executionPath":"/simulations/run","executionPerformed":False,"automaticDispatchAuthorized":False}
    record["bindingPlanHash"]=content_hash(record)
    return record


def core_lineage_plan(request: CoreSimulationLineagePlanRequest) -> Dict[str, Any]:
    result=request.simulationResult; validation=validate_simulation_result(result)
    if not validation["valid"]: raise HTTPException(status_code=422,detail={"simulationResultInvalid":validation["reasons"]})
    eid=(request.coreExecutionId or "").strip(); execution_object=result.get("executionObject") or {}; registrations=[]
    if eid:
        item=OutputItem(outputKey="dynamical-simulation-result",outputType="result_bundle",objectRef=execution_object.get("objectRef",""),contentHash=result.get("simulationRunHash",""),schema={"schema":SIMULATION_RESULT_SCHEMA,"version":VERSION},metadata={"simulationKind":result.get("simulationKind"),"diagnosticsHash":(result.get("diagnostics") or {}).get("diagnosticsHash"),"eventCount":len(result.get("events",[])),"workbenchVersion":VERSION},provenance={"simulationRuntimeRef":SIMULATION_REF,"executionObjectHash":execution_object.get("objectHash","")},createdBy=request.createdBy)
        registrations=[_request(CORE_PATHS["outputs"].format(execution_id=eid),_output_data(item),"register-dynamical-simulation-result")]
    record={"ok":True,"schema":CORE_PLAN_SCHEMA,"version":VERSION,"coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,"simulationRunHash":result.get("simulationRunHash"),"coreExecutionIdProvided":bool(eid),"coreExecutionIdMustComeFromCore":not bool(eid),"outputRegistrations":registrations,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"coreExecutesSimulation":False,"scientificValidityCertified":False}
    record["planHash"]=content_hash(record); return record


def manifest() -> Dict[str, Any]:
    record={"ok":True,"schema":SCHEMA,"version":VERSION,"product":PRODUCT_KEY,"runtime":RUNTIME_KIND,"simulationRuntimeRef":SIMULATION_REF,"coreComputationLineageContract":CORE_COMPUTATION_LINEAGE_CONTRACT,"simulationKinds":sorted(SIMULATION_CATALOG),"capabilities":{"canonicalSimulationSpecifications":True,"trajectoryNormalization":True,"eventDetection":True,"linearStabilityDiagnostics":True,"boundedParameterSweeps":True,"workspaceBindingPlanning":True,"executionObjectProjection":True,"coreLineagePlanning":True},"boundaries":{"boundedModelsOnly":True,"arbitraryCodeExecutionAuthorized":False,"pythonEvalAuthorized":False,"shellExecutionAuthorized":False,"automaticModelSelectionAuthorized":False,"automaticCoreDispatchAuthorized":False,"automaticCorePersistenceAuthorized":False,"scientificValidityCertified":False,"stabilityProofCertified":False}}
    record["manifestHash"]=content_hash(record); return record


def catalog() -> Dict[str, Any]:
    return {"ok":True,"schema":"sc-workbench-simulation-runtime-catalog/1.0","version":VERSION,"simulations":[{"simulationKind":k,**SIMULATION_CATALOG[k]} for k in sorted(SIMULATION_CATALOG)],"simulationCount":len(SIMULATION_CATALOG)}


@router.get("/simulations/manifest")
def get_manifest(): return manifest()
@router.get("/simulations/catalog")
def get_catalog(): return catalog()
@router.post("/simulations/run")
def post_run(request: SimulationRequest): return run_simulation(request)
@router.post("/simulations/validate")
def post_validate(result: Dict[str, Any]): return validate_simulation_result(result)
@router.post("/simulations/parameter-sweep")
def post_sweep(request: SweepRequest): return parameter_sweep(request)
@router.post("/simulations/workspace-binding/plan")
def post_workspace_binding(request: WorkspaceSimulationBindingRequest): return workspace_binding_plan(request)
@router.post("/integration/core/simulation-lineage/plan")
def post_core_lineage(request: CoreSimulationLineagePlanRequest, x_sc_service_token: Optional[str]=Header(default=None,alias="X-SC-Service-Token")):
    _authorize_core_route(x_sc_service_token); return core_lineage_plan(request)
@router.get("/v750/status")
def status():
    return {"ok":True,"schema":SCHEMA,"version":VERSION,"release":"Simulation & Dynamical Systems Runtime","simulationKinds":sorted(SIMULATION_CATALOG),"trajectoryNormalization":True,"eventDetection":True,"stabilityDiagnostics":True,"parameterSweeps":True,"workspaceBindingPlanning":True,"coreLineagePlanning":True,"automaticModelSelection":False,"automaticCoreDispatch":False}

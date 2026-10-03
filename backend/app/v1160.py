"""Workbench v11.6.0 — Differential Equations & Dynamical Systems.

Adds symbolic ODE solving, general numerical IVP integration, structured Julia
dynamical-system execution, equilibria, Jacobians, and local stability analysis
to the unified CalculationObject architecture.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import numpy as np
import sympy as sp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from scipy.integrate import solve_ivp

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v1150 import _julia_binary, runtime_identity
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-differential-equations-dynamical-systems-status/1.0"
DYNAMICS_SCHEMA = "sc-workbench-dynamical-system-result/1.0"

router = APIRouter(tags=["workbench-v1160-differential-equations-dynamical-systems"])
JULIA_RUNNER = Path(__file__).resolve().parents[1] / "julia-runtime" / "dynamics_runner.jl"


class DynamicsRequest(BaseModel):
    operation: Literal[
        "symbolic-ode",
        "numerical-ivp",
        "julia-ivp",
        "equilibria",
        "jacobian",
        "stability",
    ]
    equation: Optional[str] = Field(default=None, max_length=20000)
    equations: List[str] = Field(default_factory=list, max_length=50)
    stateVariables: List[str] = Field(default_factory=lambda: ["y"], max_length=20)
    independentVariable: str = Field(default="t", max_length=100)
    initialState: List[float] = Field(default_factory=list, max_length=100)
    timeSpan: List[float] = Field(default_factory=lambda: [0.0, 1.0], min_length=2, max_length=2)
    samples: int = Field(default=101, ge=2, le=10000)
    parameters: Dict[str, float] = Field(default_factory=dict)
    model: Optional[Literal[
        "exponential-decay",
        "logistic",
        "harmonic-oscillator",
        "damped-oscillator",
        "linear-system",
    ]] = None
    systemMatrix: Optional[List[List[float]]] = None
    equilibriumPoint: Optional[List[float]] = None
    preferredRuntime: Literal["python", "julia"] = "python"
    allowPythonFallback: bool = True
    rtol: float = Field(default=1e-8, gt=0)
    atol: float = Field(default=1e-10, gt=0)


class DynamicsCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    dynamics: DynamicsRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _symbols(req: DynamicsRequest):
    t = sp.Symbol(req.independentVariable, real=True)
    states = [sp.Symbol(name, real=True) for name in req.stateVariables]
    params = {name: sp.Symbol(name, real=True) for name in req.parameters}
    locals_map = {req.independentVariable: t, **{str(s): s for s in states}, **params}
    return t, states, params, locals_map


def _parse_exprs(req: DynamicsRequest):
    _, states, _, locals_map = _symbols(req)
    expressions = req.equations or ([req.equation] if req.equation else [])
    if not expressions:
        raise ValueError("equations or equation is required")
    return [sp.sympify(e, locals=locals_map) for e in expressions], states, locals_map


def _symbolic_ode(req: DynamicsRequest) -> Dict[str, Any]:
    if not req.equation:
        raise ValueError("symbolic-ode requires equation")
    t = sp.Symbol(req.independentVariable, real=True)
    yname = req.stateVariables[0] if req.stateVariables else "y"
    y = sp.Function(yname)
    local_map = {req.independentVariable: t, yname: y(t)}
    text = req.equation
    if "=" in text:
        left, right = text.split("=", 1)
        lhs = sp.sympify(left, locals={**local_map, f"{yname}'": sp.diff(y(t), t)})
        rhs = sp.sympify(right, locals=local_map)
        eq = sp.Eq(lhs, rhs)
    else:
        rhs = sp.sympify(text, locals=local_map)
        eq = sp.Eq(sp.diff(y(t), t), rhs)
    solution = sp.dsolve(eq)
    return {
        "result": str(solution),
        "equation": str(eq),
        "engine": "sympy",
        "runtime": "python",
        "method": "dsolve",
    }


def _numerical_ivp(req: DynamicsRequest) -> Dict[str, Any]:
    exprs, states, locals_map = _parse_exprs(req)
    if len(exprs) != len(states):
        raise ValueError("number of equations must equal number of stateVariables")
    if len(req.initialState) != len(states):
        raise ValueError("initialState length must match stateVariables")

    t_sym = locals_map[req.independentVariable]
    parameter_symbols = [locals_map[k] for k in req.parameters]
    fn = sp.lambdify(
        [t_sym, states, parameter_symbols],
        sp.Matrix(exprs),
        modules="numpy",
    )
    pvals = [req.parameters[k] for k in req.parameters]

    def rhs(t, y):
        out = np.asarray(fn(t, list(y), pvals), dtype=float).reshape(-1)
        return out

    t0, t1 = float(req.timeSpan[0]), float(req.timeSpan[1])
    grid = np.linspace(t0, t1, req.samples)
    sol = solve_ivp(
        rhs,
        (t0, t1),
        np.asarray(req.initialState, dtype=float),
        t_eval=grid,
        rtol=req.rtol,
        atol=req.atol,
    )
    if not sol.success:
        raise RuntimeError(sol.message)

    trajectories = {
        name: sol.y[i].tolist()
        for i, name in enumerate(req.stateVariables)
    }
    residual = rhs(float(sol.t[-1]), sol.y[:, -1]).tolist()

    return {
        "result": {
            "time": sol.t.tolist(),
            "trajectories": trajectories,
            "finalState": sol.y[:, -1].tolist(),
        },
        "engine": "scipy",
        "runtime": "python",
        "method": sol.message,
        "verification": {
            "success": bool(sol.success),
            "functionEvaluations": int(sol.nfev),
            "finalDerivative": residual,
        },
    }


def _structured_rhs(req: DynamicsRequest):
    model = req.model
    p = req.parameters
    if model == "exponential-decay":
        k = float(p.get("rate", 1.0))
        return lambda t, y: np.array([-k * y[0]])
    if model == "logistic":
        r = float(p.get("r", 1.0))
        K = float(p.get("K", 1.0))
        return lambda t, y: np.array([r * y[0] * (1.0 - y[0] / K)])
    if model == "harmonic-oscillator":
        omega = float(p.get("omega", 1.0))
        return lambda t, y: np.array([y[1], -(omega**2) * y[0]])
    if model == "damped-oscillator":
        omega = float(p.get("omega", 1.0))
        damping = float(p.get("damping", 0.1))
        return lambda t, y: np.array([y[1], -2*damping*y[1] - (omega**2)*y[0]])
    if model == "linear-system":
        if req.systemMatrix is None:
            raise ValueError("linear-system requires systemMatrix")
        A = np.asarray(req.systemMatrix, dtype=float)
        return lambda t, y: A @ y
    raise ValueError("structured model is required for julia-ivp")


def _python_structured_fallback(req: DynamicsRequest) -> Dict[str, Any]:
    rhs = _structured_rhs(req)
    t0, t1 = map(float, req.timeSpan)
    if not req.initialState:
        raise ValueError("initialState is required")
    grid = np.linspace(t0, t1, req.samples)
    sol = solve_ivp(
        rhs, (t0, t1), np.asarray(req.initialState, dtype=float),
        t_eval=grid, rtol=req.rtol, atol=req.atol
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    return {
        "result": {
            "time": sol.t.tolist(),
            "trajectories": {
                f"x{i+1}": sol.y[i].tolist()
                for i in range(sol.y.shape[0])
            },
            "finalState": sol.y[:, -1].tolist(),
        },
        "engine": "scipy",
        "runtime": "python",
        "fallback": True,
        "method": "solve_ivp",
    }


def _encode_vector(v: List[float]) -> str:
    return ",".join(format(float(x), ".17g") for x in v)


def _encode_matrix(m: Optional[List[List[float]]]) -> str:
    if not m:
        return ""
    return ";".join(_encode_vector(row) for row in m)


def _julia_structured_ivp(req: DynamicsRequest) -> Dict[str, Any]:
    binary = _julia_binary()
    if not binary or not JULIA_RUNNER.exists():
        raise RuntimeError("Julia dynamical-system runtime unavailable")
    if not req.model:
        raise ValueError("julia-ivp requires model")
    t0, t1 = map(float, req.timeSpan)
    args = [
        binary, "--startup-file=no", "--history-file=no", str(JULIA_RUNNER),
        req.model,
        _encode_vector(req.initialState),
        f"{t0:.17g}",
        f"{t1:.17g}",
        str(req.samples),
        _encode_vector([
            req.parameters.get("rate", 1.0),
            req.parameters.get("r", 1.0),
            req.parameters.get("K", 1.0),
            req.parameters.get("omega", 1.0),
            req.parameters.get("damping", 0.1),
        ]),
        _encode_matrix(req.systemMatrix),
    ]
    proc = subprocess.run(args, check=True, capture_output=True, text=True, timeout=60)
    fields = {}
    for line in proc.stdout.splitlines():
        if "\t" in line:
            k, v = line.split("\t", 1)
            fields[k] = v
    if fields.get("status") != "ok":
        raise RuntimeError(fields.get("error") or proc.stderr or "Julia dynamics execution failed")

    times = [float(x) for x in fields["time"].split(",") if x]
    rows = [
        [float(x) for x in row.split(",") if x]
        for row in fields["states"].split(";")
        if row
    ]
    arr = np.asarray(rows, dtype=float)
    return {
        "result": {
            "time": times,
            "trajectories": {
                f"x{i+1}": arr[:, i].tolist()
                for i in range(arr.shape[1])
            },
            "finalState": arr[-1].tolist(),
        },
        "engine": "julia-rk4",
        "runtime": "julia",
        "fallback": False,
        "method": "fixed-step-rk4",
        "juliaVersion": fields.get("juliaVersion"),
    }


def _equilibria(req: DynamicsRequest) -> Dict[str, Any]:
    exprs, states, _ = _parse_exprs(req)
    solutions = sp.solve([sp.Eq(e, 0) for e in exprs], states, dict=True)
    return {
        "result": [{str(k): str(v) for k, v in s.items()} for s in solutions],
        "engine": "sympy", "runtime": "python", "method": "solve-equilibria",
    }


def _jacobian(req: DynamicsRequest) -> Dict[str, Any]:
    exprs, states, _ = _parse_exprs(req)
    J = sp.Matrix(exprs).jacobian(states)
    return {
        "result": [[str(v) for v in row] for row in J.tolist()],
        "engine": "sympy", "runtime": "python", "method": "symbolic-jacobian",
    }


def _stability(req: DynamicsRequest) -> Dict[str, Any]:
    exprs, states, _ = _parse_exprs(req)
    if req.equilibriumPoint is None or len(req.equilibriumPoint) != len(states):
        raise ValueError("stability requires equilibriumPoint matching stateVariables")
    J = sp.Matrix(exprs).jacobian(states)
    subs = {states[i]: req.equilibriumPoint[i] for i in range(len(states))}
    Jeq = J.subs(subs)
    eigs = [complex(sp.N(v)) for v in Jeq.eigenvals().keys()]
    real_parts = [v.real for v in eigs]
    if all(r < -1e-12 for r in real_parts):
        classification = "asymptotically-stable"
    elif any(r > 1e-12 for r in real_parts):
        classification = "unstable"
    else:
        classification = "nonhyperbolic-or-marginal"
    return {
        "result": {
            "jacobianAtEquilibrium": [[str(v) for v in row] for row in Jeq.tolist()],
            "eigenvalues": [str(v) for v in eigs],
            "classification": classification,
        },
        "engine": "sympy", "runtime": "python", "method": "linearization-eigenvalues",
    }


def execute_dynamics(req: DynamicsRequest) -> Dict[str, Any]:
    fallback_reason = None
    if req.operation == "symbolic-ode":
        executed = _symbolic_ode(req)
    elif req.operation == "numerical-ivp":
        executed = _numerical_ivp(req)
    elif req.operation == "julia-ivp":
        try:
            executed = _julia_structured_ivp(req)
        except Exception as exc:
            if not req.allowPythonFallback:
                raise HTTPException(status_code=503, detail=f"Julia dynamics failed: {exc}")
            fallback_reason = str(exc)
            executed = _python_structured_fallback(req)
    elif req.operation == "equilibria":
        executed = _equilibria(req)
    elif req.operation == "jacobian":
        executed = _jacobian(req)
    elif req.operation == "stability":
        executed = _stability(req)
    else:
        raise ValueError(f"Unsupported dynamics operation: {req.operation}")

    body = {
        "ok": True,
        "schema": DYNAMICS_SCHEMA,
        "version": VERSION,
        "operation": req.operation,
        "engine": executed["engine"],
        "runtime": executed["runtime"],
        "method": executed["method"],
        "fallback": bool(executed.get("fallback", False)),
        "fallbackReason": fallback_reason,
        "result": executed["result"],
        "verification": executed.get("verification", {}),
        "runtimeIdentity": runtime_identity() if req.operation == "julia-ivp" else None,
        "wordpressRequired": False,
    }
    body["resultHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "resultHash"}}
    )
    return body


def calculation_object_extension(req: UnifiedCalculationRequest, dyn: DynamicsRequest):
    obj = build_calculation_object(req)
    result = execute_dynamics(dyn)
    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["dynamicalSystems"] = result
    obj["result"]["dynamicalSystems"] = result["result"]
    obj["executionPlan"]["dynamicalSystems"] = {
        "operation": dyn.operation,
        "runtime": result["runtime"],
        "engine": result["engine"],
        "method": result["method"],
        "fallback": result["fallback"],
    }
    obj["verification"]["dynamicalSystems"] = result["verification"]
    obj["provenance"]["dynamicalSystemsResultHash"] = result["resultHash"]
    if result.get("runtimeIdentity"):
        obj["provenance"]["juliaRuntimeIdentityHash"] = result["runtimeIdentity"]["runtimeIdentityHash"]
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status():
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Differential Equations & Dynamical Systems",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "engines": {
            "symbolic": "sympy",
            "generalNumericalIVP": "scipy",
            "structuredScientificRuntime": "julia",
        },
        "capabilities": {
            "symbolicODE": True,
            "generalNumericalIVP": True,
            "juliaStructuredIVP": True,
            "phaseTrajectories": True,
            "equilibria": True,
            "symbolicJacobian": True,
            "localStabilityAnalysis": True,
            "runtimeFallbackProvenance": True,
            "calculationObjectExtension": True,
        },
    }


@router.get("/v1160/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/dynamics")
def dynamics_route(req: DynamicsRequest):
    return execute_dynamics(req)


@router.post("/calculation-engine/v1/dynamics/calculation-object")
def dynamics_calculation_object_route(req: DynamicsCalculationObjectRequest):
    return calculation_object_extension(req.calculationObjectRequest, req.dynamics)

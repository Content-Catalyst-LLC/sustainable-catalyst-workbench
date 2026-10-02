"""Workbench v10.10.0 — Hybrid Numerical Runtime & Standalone Application Foundation.

Backend-first calculation runtime for Sustainable Catalyst Workbench.
WordPress is an optional adapter; all authoritative calculation contracts and execution live here.
"""
from __future__ import annotations

import hashlib
import math
from decimal import Decimal, getcontext
from typing import Any, Dict, List, Literal, Optional

import numpy as np
import sympy as sp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from scipy import integrate, optimize

try:
    import pint
except Exception:  # pragma: no cover
    pint = None

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v510 import content_hash

VERSION = APP_VERSION
SCHEMA = "sc-workbench-hybrid-numerical-runtime/1.0"
CALC_SCHEMA = "sc-workbench-calculation-result/1.0"
PLAN_SCHEMA = "sc-workbench-calculation-plan/1.0"
CLIENT_SCHEMA = "sc-workbench-standalone-client-contract/1.0"

router = APIRouter(tags=["workbench-v10100-hybrid-numerical-runtime"])

Operation = Literal[
    "exact", "evaluate", "simplify", "solve", "differentiate", "integrate-symbolic",
    "root", "integrate-numeric", "optimize-scalar", "matrix", "ode", "units",
]
MatrixOperation = Literal["det", "inverse", "rank", "eigen", "svd", "solve"]


def _stable_hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _float(value: Any) -> float:
    try:
        return float(value)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Expected numeric value: {value}") from exc


def _sympify_expression(expr: str, variables: List[str]) -> tuple[Any, Dict[str, Any]]:
    if len(expr) > 20000:
        raise HTTPException(status_code=422, detail="Expression exceeds 20,000 characters")
    symbols = {name: sp.Symbol(name) for name in variables}
    try:
        return sp.sympify(expr, locals=symbols), symbols
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid expression: {exc}") from exc


class PrecisionSpec(BaseModel):
    digits: int = Field(default=30, ge=10, le=500)
    absoluteTolerance: float = Field(default=1e-10, gt=0)
    relativeTolerance: float = Field(default=1e-10, gt=0)
    maxIterations: int = Field(default=1000, ge=1, le=1_000_000)


class CalculationRequest(BaseModel):
    operation: Operation
    expression: Optional[str] = Field(default=None, max_length=20000)
    variable: Optional[str] = Field(default=None, max_length=200)
    variables: List[str] = Field(default_factory=list, max_length=100)
    values: Dict[str, float] = Field(default_factory=dict)
    domain: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)
    initialGuess: Optional[float] = None
    bracket: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)
    matrix: Optional[List[List[float]]] = None
    vector: Optional[List[float]] = None
    matrixOperation: Optional[MatrixOperation] = None
    initialState: Optional[List[float]] = None
    timeSpan: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)
    unitExpression: Optional[str] = Field(default=None, max_length=2000)
    targetUnit: Optional[str] = Field(default=None, max_length=300)
    precision: PrecisionSpec = Field(default_factory=PrecisionSpec)
    randomSeed: Optional[int] = None
    notes: str = Field(default="", max_length=5000)

    @model_validator(mode="after")
    def validate_operation_fields(self):
        expr_ops = {"exact", "evaluate", "simplify", "solve", "differentiate", "integrate-symbolic", "root", "integrate-numeric", "optimize-scalar", "ode"}
        if self.operation in expr_ops and not self.expression:
            raise ValueError(f"{self.operation} requires expression")
        if self.operation in {"differentiate", "integrate-symbolic", "root", "integrate-numeric", "optimize-scalar", "ode"} and not self.variable:
            raise ValueError(f"{self.operation} requires variable")
        if self.operation == "matrix" and (self.matrix is None or self.matrixOperation is None):
            raise ValueError("matrix operation requires matrix and matrixOperation")
        if self.operation == "units" and not self.unitExpression:
            raise ValueError("units operation requires unitExpression")
        return self


class PlanRequest(BaseModel):
    operation: Operation
    expression: Optional[str] = Field(default=None, max_length=20000)
    objective: str = Field(default="", max_length=5000)
    requireExactWhenPossible: bool = True
    requireUnits: bool = False
    requireUncertainty: bool = False
    preferredRuntime: Literal["auto", "symbolic", "numeric"] = "auto"


def _base_result(req: CalculationRequest, engine: str, method: str, result: Any, diagnostics: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = {
        "schema": CALC_SCHEMA,
        "version": VERSION,
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "operation": req.operation,
        "engine": engine,
        "method": method,
        "result": result,
        "precision": req.precision.model_dump(mode="json"),
        "diagnostics": diagnostics or {},
        "randomSeed": req.randomSeed,
        "notes": req.notes,
        "wordpressRequired": False,
    }
    payload["calculationHash"] = _stable_hash(payload)
    return {"ok": True, **payload}


def execute(req: CalculationRequest) -> Dict[str, Any]:
    variables = list(dict.fromkeys(([req.variable] if req.variable else []) + req.variables + list(req.values.keys())))
    expr = symbols = None
    if req.expression:
        expr, symbols = _sympify_expression(req.expression, variables)

    if req.operation == "exact":
        exact = sp.simplify(expr)
        numeric = sp.N(exact, req.precision.digits)
        return _base_result(req, "sympy", "exact", {"exact": str(exact), "decimal": str(numeric)})

    if req.operation == "evaluate":
        subs = {symbols[k]: v for k, v in req.values.items() if k in symbols}
        out = sp.N(expr.subs(subs), req.precision.digits)
        return _base_result(req, "sympy", "evaluate", {"value": str(out), "float": float(out) if out.is_real else None})

    if req.operation == "simplify":
        out = sp.simplify(expr)
        return _base_result(req, "sympy", "simplify", {"expression": str(out)})

    if req.operation == "solve":
        var = symbols.get(req.variable) if req.variable else (next(iter(expr.free_symbols), None))
        if var is None:
            raise HTTPException(status_code=422, detail="solve requires a variable")
        sols = sp.solve(expr, var)
        return _base_result(req, "sympy", "solve", {"solutions": [str(x) for x in sols], "count": len(sols)})

    if req.operation == "differentiate":
        var = symbols[req.variable]
        out = sp.diff(expr, var)
        return _base_result(req, "sympy", "differentiate", {"expression": str(out)})

    if req.operation == "integrate-symbolic":
        var = symbols[req.variable]
        if req.domain:
            out = sp.integrate(expr, (var, req.domain[0], req.domain[1]))
        else:
            out = sp.integrate(expr, var)
        return _base_result(req, "sympy", "integrate", {"expression": str(out), "decimal": str(sp.N(out, req.precision.digits))})

    if req.operation in {"root", "integrate-numeric", "optimize-scalar"}:
        var = symbols[req.variable]
        f = sp.lambdify(var, expr, modules=["numpy", "math"])
        if req.operation == "root":
            if req.bracket:
                sol = optimize.root_scalar(f, bracket=req.bracket, xtol=req.precision.absoluteTolerance, rtol=req.precision.relativeTolerance, maxiter=req.precision.maxIterations)
            elif req.initialGuess is not None:
                sol = optimize.root_scalar(f, x0=req.initialGuess, x1=req.initialGuess + 1e-4, xtol=req.precision.absoluteTolerance, rtol=req.precision.relativeTolerance, maxiter=req.precision.maxIterations)
            else:
                raise HTTPException(status_code=422, detail="root requires bracket or initialGuess")
            return _base_result(req, "scipy", "root_scalar", {"root": sol.root, "converged": sol.converged, "iterations": sol.iterations, "functionCalls": sol.function_calls})
        if req.operation == "integrate-numeric":
            if not req.domain:
                raise HTTPException(status_code=422, detail="integrate-numeric requires domain")
            value, error = integrate.quad(f, req.domain[0], req.domain[1], epsabs=req.precision.absoluteTolerance, epsrel=req.precision.relativeTolerance, limit=min(req.precision.maxIterations, 10000))
            return _base_result(req, "scipy", "quad", {"value": value, "estimatedAbsoluteError": error})
        if req.domain:
            sol = optimize.minimize_scalar(f, bounds=tuple(req.domain), method="bounded", options={"xatol": req.precision.absoluteTolerance, "maxiter": req.precision.maxIterations})
        else:
            sol = optimize.minimize_scalar(f, options={"maxiter": req.precision.maxIterations})
        return _base_result(req, "scipy", "minimize_scalar", {"x": float(sol.x), "fun": float(sol.fun), "success": bool(sol.success), "iterations": int(getattr(sol, "nit", 0))})

    if req.operation == "matrix":
        a = np.array(req.matrix, dtype=float)
        op = req.matrixOperation
        if a.ndim != 2:
            raise HTTPException(status_code=422, detail="matrix must be two-dimensional")
        if op == "det":
            out = float(np.linalg.det(a))
        elif op == "inverse":
            out = np.linalg.inv(a).tolist()
        elif op == "rank":
            out = int(np.linalg.matrix_rank(a))
        elif op == "eigen":
            vals, vecs = np.linalg.eig(a)
            out = {"eigenvalues": [complex(x).__repr__() for x in vals], "eigenvectors": [[complex(x).__repr__() for x in row] for row in vecs]}
        elif op == "svd":
            u, s, vh = np.linalg.svd(a)
            out = {"u": u.tolist(), "singularValues": s.tolist(), "vh": vh.tolist(), "conditionNumber": float(np.linalg.cond(a))}
        elif op == "solve":
            if req.vector is None:
                raise HTTPException(status_code=422, detail="matrix solve requires vector")
            out = np.linalg.solve(a, np.array(req.vector, dtype=float)).tolist()
        else:  # pragma: no cover
            raise HTTPException(status_code=422, detail="Unsupported matrix operation")
        return _base_result(req, "numpy", f"matrix-{op}", out, {"shape": list(a.shape)})

    if req.operation == "ode":
        if not req.timeSpan or req.initialState is None:
            raise HTTPException(status_code=422, detail="ode requires timeSpan and initialState")
        t = symbols[req.variable]
        state_symbols = [sp.Symbol(name) for name in req.variables]
        if len(state_symbols) != len(req.initialState):
            raise HTTPException(status_code=422, detail="variables must name each ODE state and match initialState length")
        local_map = {req.variable: t, **{n: s for n, s in zip(req.variables, state_symbols)}}
        try:
            ode_expr = sp.sympify(req.expression, locals=local_map)
            exprs = list(ode_expr) if isinstance(ode_expr, (tuple, list, sp.Tuple)) else [ode_expr]
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Invalid ODE expression: {exc}") from exc
        if len(exprs) != len(req.initialState):
            raise HTTPException(status_code=422, detail="ODE expression must provide one derivative per state")
        f = sp.lambdify([t, *state_symbols], exprs, modules=["numpy", "math"])
        def rhs(tt, yy):
            return np.asarray(f(tt, *yy), dtype=float).reshape(-1)
        sol = integrate.solve_ivp(rhs, tuple(req.timeSpan), req.initialState, rtol=req.precision.relativeTolerance, atol=req.precision.absoluteTolerance)
        return _base_result(req, "scipy", "solve_ivp", {"t": sol.t.tolist(), "y": sol.y.tolist(), "success": bool(sol.success), "message": sol.message, "evaluations": int(sol.nfev)})

    if req.operation == "units":
        if pint is None:
            raise HTTPException(status_code=503, detail="Pint unit runtime unavailable")
        ureg = pint.UnitRegistry()
        try:
            quantity = ureg(req.unitExpression)
            if req.targetUnit:
                quantity = quantity.to(req.targetUnit)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Invalid unit expression: {exc}") from exc
        return _base_result(req, "pint", "units", {"magnitude": quantity.magnitude, "units": str(quantity.units), "text": str(quantity)})

    raise HTTPException(status_code=422, detail=f"Unsupported operation: {req.operation}")


def plan(req: PlanRequest) -> Dict[str, Any]:
    engines: List[str] = []
    if req.operation in {"exact", "simplify", "solve", "differentiate", "integrate-symbolic"}:
        engines = ["sympy"]
    elif req.operation == "matrix":
        engines = ["numpy"]
    elif req.operation == "units":
        engines = ["pint"]
    else:
        engines = ["sympy", "scipy", "numpy"]
    payload = {
        "schema": PLAN_SCHEMA,
        "version": VERSION,
        "operation": req.operation,
        "objective": req.objective,
        "engines": engines,
        "requireExactWhenPossible": req.requireExactWhenPossible,
        "requireUnits": req.requireUnits,
        "requireUncertainty": req.requireUncertainty,
        "preferredRuntime": req.preferredRuntime,
        "automaticExecution": False,
        "wordpressRequired": False,
    }
    payload["planHash"] = _stable_hash(payload)
    return {"ok": True, **payload}


def capabilities() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "release": "Hybrid Numerical Runtime & Standalone Application Foundation",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "backendFirst": True,
        "wordpressRequired": False,
        "engines": {"symbolic": "sympy", "numeric": ["numpy", "scipy"], "units": "pint"},
        "capabilities": {
            "exactArithmetic": True,
            "arbitraryPrecisionEvaluation": True,
            "symbolicSimplification": True,
            "symbolicEquationSolving": True,
            "symbolicDifferentiation": True,
            "symbolicIntegration": True,
            "numericalRootFinding": True,
            "numericalQuadrature": True,
            "scalarOptimization": True,
            "matrixLinearAlgebra": True,
            "svdAndConditioning": True,
            "odeIntegration": True,
            "unitAwareCalculation": pint is not None,
            "calculationProvenance": True,
            "deterministicCalculationHashes": True,
            "standaloneClientContract": True,
            "wordpressAdapterOptional": True,
        },
        "boundaries": {
            "browserExecutesAuthoritativeMath": False,
            "wordpressExecutesAuthoritativeMath": False,
            "automaticPlatformCoreDispatch": False,
            "automaticWorkspaceHeavyJobDispatch": False,
        },
    }


def standalone_contract() -> Dict[str, Any]:
    body = {
        "ok": True,
        "schema": CLIENT_SCHEMA,
        "version": VERSION,
        "application": "Sustainable Catalyst Workbench",
        "architecture": "backend-first-decoupled",
        "wordpressRequired": False,
        "wordpressRole": "optional-adapter-and-embed-host",
        "canonicalBackend": "FastAPI",
        "api": {
            "status": "/v10100/status",
            "capabilities": "/numerical/capabilities",
            "plan": "/numerical/plan",
            "calculate": "/numerical/compute",
            "standaloneBootstrap": "/standalone/bootstrap",
        },
        "migration": {
            "frontendMayMoveOffWordPressWithoutChangingCalculationContracts": True,
            "runtimeStateOwnedByBackend": True,
            "wordpressSpecificStateMayNotBeCanonical": True,
        },
    }
    body["contractHash"] = _stable_hash({k: v for k, v in body.items() if k not in {"ok", "contractHash"}})
    return body


@router.get("/v10100/status")
def status_route():
    return capabilities()


@router.get("/numerical/capabilities")
def capabilities_route():
    return capabilities()


@router.post("/numerical/plan")
def plan_route(req: PlanRequest):
    return plan(req)


@router.post("/numerical/compute")
def compute_route(req: CalculationRequest):
    return execute(req)


@router.get("/standalone/bootstrap")
def standalone_bootstrap_route():
    return standalone_contract()

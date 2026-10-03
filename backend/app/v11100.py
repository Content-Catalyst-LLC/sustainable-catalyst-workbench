"""Workbench v11.10.0 — Optimization & Mathematical Programming.

Adds scalar, multivariate, constrained, linear, mixed-integer, and nonlinear
least-squares optimization plus analytical gradient/Hessian inspection to the
unified v11 CalculationObject architecture.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import numpy as np
import sympy as sp
from fastapi import APIRouter
from pydantic import BaseModel, Field
from scipy.optimize import Bounds, LinearConstraint, least_squares, linprog, milp, minimize, minimize_scalar

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-optimization-mathematical-programming-status/1.0"
OPTIMIZATION_SCHEMA = "sc-workbench-optimization-result/1.0"

router = APIRouter(tags=["workbench-v11100-optimization-mathematical-programming"])


class OptimizationConstraint(BaseModel):
    kind: Literal["eq", "ineq"]
    expression: str = Field(max_length=10000)


class OptimizationRequest(BaseModel):
    operation: Literal[
        "scalar-minimize",
        "multivariate-minimize",
        "constrained-minimize",
        "linear-program",
        "mixed-integer-linear-program",
        "nonlinear-least-squares",
        "symbolic-gradient-hessian",
        "verify-point",
    ]
    objective: Optional[str] = Field(default=None, max_length=20000)
    variable: str = Field(default="x", max_length=200)
    variables: List[str] = Field(default_factory=list, max_length=100)
    initialGuess: List[float] = Field(default_factory=list, max_length=100)
    bounds: List[List[Optional[float]]] = Field(default_factory=list, max_length=100)
    constraints: List[OptimizationConstraint] = Field(default_factory=list, max_length=100)
    residualExpressions: List[str] = Field(default_factory=list, max_length=1000)
    coefficients: List[float] = Field(default_factory=list, max_length=10000)
    A_ub: List[List[float]] = Field(default_factory=list, max_length=10000)
    b_ub: List[float] = Field(default_factory=list, max_length=10000)
    A_eq: List[List[float]] = Field(default_factory=list, max_length=10000)
    b_eq: List[float] = Field(default_factory=list, max_length=10000)
    integrality: List[int] = Field(default_factory=list, max_length=10000)
    sense: Literal["minimize", "maximize"] = "minimize"
    point: List[float] = Field(default_factory=list, max_length=100)
    tolerance: float = Field(default=1e-9, gt=0)
    maxIterations: int = Field(default=1000, ge=1, le=100000)


class OptimizationCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    optimization: OptimizationRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _symbol_map(names: List[str]) -> Dict[str, sp.Symbol]:
    if not names:
        raise ValueError("variables are required")
    return {name: sp.Symbol(name, real=True) for name in names}


def _parse(expr: str, symbols: Dict[str, sp.Symbol]):
    return sp.sympify(expr, locals=symbols)


def _numeric_function(expr, ordered_symbols):
    fn = sp.lambdify(ordered_symbols, expr, modules="numpy")
    return lambda x: float(np.asarray(fn(*np.asarray(x, dtype=float))).reshape(()))


def _bounds(req: OptimizationRequest, n: int):
    if not req.bounds:
        return None
    if len(req.bounds) != n:
        raise ValueError("bounds length must match variable count")
    normalized = []
    for pair in req.bounds:
        if len(pair) != 2:
            raise ValueError("each bounds entry must be [lower, upper]")
        normalized.append((pair[0], pair[1]))
    return normalized


def _solution_payload(result, variables: List[str]) -> Dict[str, Any]:
    x = np.atleast_1d(np.asarray(result.x, dtype=float))
    return {
        "solution": {variables[i]: float(x[i]) for i in range(len(variables))},
        "objectiveValue": float(result.fun),
        "success": bool(result.success),
        "status": int(result.status),
        "message": str(result.message),
        "iterations": None if getattr(result, "nit", None) is None else int(result.nit),
        "functionEvaluations": None if getattr(result, "nfev", None) is None else int(result.nfev),
    }


def _constraint_diagnostics(req: OptimizationRequest, symbols, point) -> Dict[str, Any]:
    ordered = [symbols[name] for name in req.variables]
    values = {}
    feasible = True
    for idx, c in enumerate(req.constraints):
        expr = _parse(c.expression, symbols)
        fn = sp.lambdify(ordered, expr, modules="numpy")
        value = float(fn(*point))
        values[f"c{idx+1}"] = {"kind": c.kind, "value": value}
        if c.kind == "eq":
            ok = abs(value) <= req.tolerance
        else:
            ok = value >= -req.tolerance
        values[f"c{idx+1}"]["satisfied"] = bool(ok)
        feasible = feasible and bool(ok)
    return {"feasible": feasible, "constraints": values}


def execute_optimization(req: OptimizationRequest) -> Dict[str, Any]:
    op = req.operation
    details: Dict[str, Any] = {}
    verification: Dict[str, Any] = {}
    method = op

    if op == "scalar-minimize":
        if not req.objective:
            raise ValueError("scalar-minimize requires objective")
        x = sp.Symbol(req.variable, real=True)
        expr = sp.sympify(req.objective, locals={req.variable: x})
        fn0 = sp.lambdify(x, expr, modules="numpy")
        fn = lambda value: float(fn0(value))
        options = {"maxiter": req.maxIterations, "xatol": req.tolerance}
        if req.bounds:
            if len(req.bounds) != 1 or len(req.bounds[0]) != 2:
                raise ValueError("scalar-minimize bounds must contain one [lower, upper] pair")
            lo, hi = req.bounds[0]
            if lo is None or hi is None:
                raise ValueError("bounded scalar optimization requires finite lower and upper bounds")
            solved = minimize_scalar(fn, bounds=(lo, hi), method="bounded", options=options)
            method = "scipy-minimize-scalar-bounded"
        else:
            solved = minimize_scalar(fn, method="brent", options={"maxiter": req.maxIterations, "xtol": req.tolerance})
            method = "scipy-minimize-scalar-brent"
        result = {
            "solution": {req.variable: float(solved.x)},
            "objectiveValue": float(solved.fun),
            "success": bool(solved.success),
            "message": str(solved.message),
            "iterations": int(solved.nit),
            "functionEvaluations": int(solved.nfev),
        }
        verification["finiteSolution"] = bool(np.isfinite(solved.x) and np.isfinite(solved.fun))

    elif op in {"multivariate-minimize", "constrained-minimize"}:
        if not req.objective:
            raise ValueError(f"{op} requires objective")
        symbols = _symbol_map(req.variables)
        ordered = [symbols[n] for n in req.variables]
        expr = _parse(req.objective, symbols)
        fn = _numeric_function(expr, ordered)
        if len(req.initialGuess) != len(ordered):
            raise ValueError("initialGuess length must match variables")
        bounds = _bounds(req, len(ordered))

        scipy_constraints = []
        for c in req.constraints:
            cexpr = _parse(c.expression, symbols)
            cfn = _numeric_function(cexpr, ordered)
            scipy_constraints.append({"type": c.kind, "fun": cfn})

        if op == "constrained-minimize" or scipy_constraints:
            solved = minimize(
                fn,
                np.asarray(req.initialGuess, dtype=float),
                method="SLSQP",
                bounds=bounds,
                constraints=scipy_constraints,
                options={"maxiter": req.maxIterations, "ftol": req.tolerance},
            )
            method = "scipy-slsqp"
        else:
            solved = minimize(
                fn,
                np.asarray(req.initialGuess, dtype=float),
                method="L-BFGS-B" if bounds else "BFGS",
                bounds=bounds,
                options={"maxiter": req.maxIterations, "gtol": req.tolerance},
            )
            method = "scipy-l-bfgs-b" if bounds else "scipy-bfgs"

        result = _solution_payload(solved, req.variables)
        verification["solverSuccess"] = bool(solved.success)
        if req.constraints:
            verification.update(_constraint_diagnostics(req, symbols, np.asarray(solved.x, dtype=float)))

    elif op == "linear-program":
        if not req.coefficients:
            raise ValueError("linear-program requires coefficients")
        c = np.asarray(req.coefficients, dtype=float)
        objective_c = -c if req.sense == "maximize" else c
        bounds = _bounds(req, len(c)) or [(0, None)] * len(c)
        solved = linprog(
            objective_c,
            A_ub=np.asarray(req.A_ub, dtype=float) if req.A_ub else None,
            b_ub=np.asarray(req.b_ub, dtype=float) if req.b_ub else None,
            A_eq=np.asarray(req.A_eq, dtype=float) if req.A_eq else None,
            b_eq=np.asarray(req.b_eq, dtype=float) if req.b_eq else None,
            bounds=bounds,
            method="highs",
            options={"time_limit": float(req.maxIterations)},
        )
        variables = req.variables or [f"x{i+1}" for i in range(len(c))]
        if len(variables) != len(c):
            raise ValueError("variables length must match coefficients")
        objective = float(c @ solved.x) if solved.x is not None else None
        result = {
            "solution": None if solved.x is None else {variables[i]: float(solved.x[i]) for i in range(len(c))},
            "objectiveValue": objective,
            "success": bool(solved.success),
            "status": int(solved.status),
            "message": str(solved.message),
            "iterations": int(getattr(solved, "nit", 0)),
        }
        method = "scipy-highs-linear-programming"
        verification["solverSuccess"] = bool(solved.success)

    elif op == "mixed-integer-linear-program":
        if not req.coefficients:
            raise ValueError("mixed-integer-linear-program requires coefficients")
        c = np.asarray(req.coefficients, dtype=float)
        objective_c = -c if req.sense == "maximize" else c
        n = len(c)
        bounds_list = _bounds(req, n) or [(0, np.inf)] * n
        lb = np.array([-np.inf if b[0] is None else b[0] for b in bounds_list], dtype=float)
        ub = np.array([np.inf if b[1] is None else b[1] for b in bounds_list], dtype=float)
        constraints = []
        if req.A_ub:
            A = np.asarray(req.A_ub, dtype=float)
            constraints.append(LinearConstraint(A, -np.inf, np.asarray(req.b_ub, dtype=float)))
        if req.A_eq:
            A = np.asarray(req.A_eq, dtype=float)
            b = np.asarray(req.b_eq, dtype=float)
            constraints.append(LinearConstraint(A, b, b))
        integrality = np.asarray(req.integrality or [1] * n, dtype=int)
        if integrality.size != n:
            raise ValueError("integrality length must match coefficients")
        solved = milp(
            c=objective_c,
            integrality=integrality,
            bounds=Bounds(lb, ub),
            constraints=constraints or None,
            options={"time_limit": float(req.maxIterations)},
        )
        variables = req.variables or [f"x{i+1}" for i in range(n)]
        if len(variables) != n:
            raise ValueError("variables length must match coefficients")
        objective = float(c @ solved.x) if solved.x is not None else None
        result = {
            "solution": None if solved.x is None else {variables[i]: float(solved.x[i]) for i in range(n)},
            "objectiveValue": objective,
            "success": bool(solved.success),
            "status": int(solved.status),
            "message": str(solved.message),
        }
        method = "scipy-highs-milp"
        verification["solverSuccess"] = bool(solved.success)
        if solved.x is not None:
            integer_mask = integrality != 0
            verification["integerVariablesIntegral"] = bool(
                np.all(np.abs(solved.x[integer_mask] - np.round(solved.x[integer_mask])) <= req.tolerance)
            )

    elif op == "nonlinear-least-squares":
        if not req.residualExpressions:
            raise ValueError("nonlinear-least-squares requires residualExpressions")
        symbols = _symbol_map(req.variables)
        ordered = [symbols[n] for n in req.variables]
        residual_exprs = [_parse(e, symbols) for e in req.residualExpressions]
        fn0 = sp.lambdify(ordered, residual_exprs, modules="numpy")
        fn = lambda x: np.asarray(fn0(*np.asarray(x, dtype=float)), dtype=float).reshape(-1)
        if len(req.initialGuess) != len(ordered):
            raise ValueError("initialGuess length must match variables")
        bounds_list = _bounds(req, len(ordered))
        if bounds_list:
            lo = [-np.inf if b[0] is None else b[0] for b in bounds_list]
            hi = [np.inf if b[1] is None else b[1] for b in bounds_list]
            bounds_arg = (lo, hi)
        else:
            bounds_arg = (-np.inf, np.inf)
        solved = least_squares(
            fn,
            np.asarray(req.initialGuess, dtype=float),
            bounds=bounds_arg,
            ftol=req.tolerance,
            xtol=req.tolerance,
            gtol=req.tolerance,
            max_nfev=req.maxIterations,
        )
        residual = fn(solved.x)
        result = {
            "solution": {req.variables[i]: float(solved.x[i]) for i in range(len(req.variables))},
            "cost": float(solved.cost),
            "residuals": residual.tolist(),
            "residualNorm": float(np.linalg.norm(residual)),
            "success": bool(solved.success),
            "status": int(solved.status),
            "message": str(solved.message),
            "functionEvaluations": int(solved.nfev),
        }
        method = "scipy-least-squares"
        verification["solverSuccess"] = bool(solved.success)

    elif op == "symbolic-gradient-hessian":
        if not req.objective:
            raise ValueError("symbolic-gradient-hessian requires objective")
        symbols = _symbol_map(req.variables)
        ordered = [symbols[n] for n in req.variables]
        expr = _parse(req.objective, symbols)
        gradient = [sp.diff(expr, s) for s in ordered]
        hessian = sp.hessian(expr, ordered)
        result = {
            "gradient": [str(x) for x in gradient],
            "hessian": [[str(v) for v in row] for row in hessian.tolist()],
        }
        method = "sympy-gradient-hessian"

    elif op == "verify-point":
        if not req.objective:
            raise ValueError("verify-point requires objective")
        symbols = _symbol_map(req.variables)
        ordered = [symbols[n] for n in req.variables]
        if len(req.point) != len(ordered):
            raise ValueError("point length must match variables")
        expr = _parse(req.objective, symbols)
        fn = _numeric_function(expr, ordered)
        objective_value = fn(np.asarray(req.point, dtype=float))
        gradient_exprs = [sp.diff(expr, s) for s in ordered]
        gfn = sp.lambdify(ordered, gradient_exprs, modules="numpy")
        gradient = np.asarray(gfn(*req.point), dtype=float).reshape(-1)
        result = {
            "point": {req.variables[i]: float(req.point[i]) for i in range(len(req.variables))},
            "objectiveValue": float(objective_value),
            "gradient": gradient.tolist(),
            "gradientNorm": float(np.linalg.norm(gradient)),
        }
        verification["firstOrderStationary"] = bool(np.linalg.norm(gradient) <= req.tolerance)
        if req.constraints:
            verification.update(_constraint_diagnostics(req, symbols, np.asarray(req.point, dtype=float)))
        method = "symbolic-numeric-point-verification"

    else:
        raise ValueError(f"Unsupported optimization operation: {op}")

    body = {
        "ok": True,
        "schema": OPTIMIZATION_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "sympy-scipy-optimize",
        "runtime": "python",
        "method": method,
        "result": result,
        "details": details,
        "verification": verification,
        "wordpressRequired": False,
    }
    body["resultHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "resultHash"}}
    )
    return body


def calculation_object_extension(
    req: UnifiedCalculationRequest,
    optimization_req: OptimizationRequest,
):
    obj = build_calculation_object(req)
    result = execute_optimization(optimization_req)

    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["optimization"] = result
    obj["result"]["optimization"] = result["result"]
    obj["executionPlan"]["optimization"] = {
        "runtime": "python",
        "engine": "sympy-scipy-optimize",
        "operation": optimization_req.operation,
        "method": result["method"],
        "tolerance": optimization_req.tolerance,
        "maxIterations": optimization_req.maxIterations,
    }
    obj["verification"]["optimization"] = result["verification"]
    obj["provenance"]["optimizationResultHash"] = result["resultHash"]
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Optimization & Mathematical Programming",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "sympy-scipy-optimize",
        "wordpressRequired": False,
        "capabilities": {
            "scalarOptimization": True,
            "multivariateOptimization": True,
            "boundedOptimization": True,
            "nonlinearConstrainedOptimization": True,
            "linearProgramming": True,
            "mixedIntegerLinearProgramming": True,
            "nonlinearLeastSquares": True,
            "symbolicGradientHessian": True,
            "solutionVerification": True,
            "constraintFeasibilityDiagnostics": True,
            "calculationObjectExtension": True,
        },
        "solvers": ["Brent", "bounded", "BFGS", "L-BFGS-B", "SLSQP", "HiGHS", "HiGHS-MILP", "least_squares"],
    }


@router.get("/v11100/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/optimization")
def optimization_route(req: OptimizationRequest):
    return execute_optimization(req)


@router.post("/calculation-engine/v1/optimization/calculation-object")
def optimization_calculation_object_route(req: OptimizationCalculationObjectRequest):
    return calculation_object_extension(
        req.calculationObjectRequest,
        req.optimization,
    )

"""Workbench v11.11.0 — Numerical Analysis Laboratory.

Adds root-method studies, numerical differentiation/integration, interpolation,
convergence-order estimation, error diagnostics, and conditioning analysis to
the unified v11 CalculationObject.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import numpy as np
import sympy as sp
from fastapi import APIRouter
from pydantic import BaseModel, Field
from scipy import integrate, interpolate, optimize

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-numerical-analysis-laboratory-status/1.0"
RESULT_SCHEMA = "sc-workbench-numerical-analysis-result/1.0"

router = APIRouter(tags=["workbench-v11110-numerical-analysis-laboratory"])


class NumericalAnalysisRequest(BaseModel):
    operation: Literal[
        "root-study",
        "differentiate",
        "integrate",
        "interpolate",
        "convergence-study",
        "conditioning",
    ]
    expression: Optional[str] = Field(default=None, max_length=20000)
    variable: str = Field(default="x", max_length=200)
    point: Optional[float] = None
    bracket: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)
    initialGuess: Optional[float] = None
    secondGuess: Optional[float] = None
    method: Optional[str] = Field(default=None, max_length=100)
    step: float = Field(default=1e-5, gt=0)
    steps: List[float] = Field(default_factory=list, max_length=1000)
    interval: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)
    samples: int = Field(default=101, ge=3, le=100000)
    xValues: List[float] = Field(default_factory=list, max_length=100000)
    yValues: List[float] = Field(default_factory=list, max_length=100000)
    evaluationPoints: List[float] = Field(default_factory=list, max_length=100000)
    exactValue: Optional[float] = None
    matrix: Optional[List[List[float]]] = None
    tolerance: float = Field(default=1e-10, gt=0)
    maxIterations: int = Field(default=100, ge=1, le=100000)


class NumericalCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    numericalAnalysis: NumericalAnalysisRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _expr_function(req: NumericalAnalysisRequest):
    if not req.expression:
        raise ValueError(f"{req.operation} requires expression")
    x = sp.Symbol(req.variable, real=True)
    expr = sp.sympify(req.expression, locals={req.variable: x})
    fn = sp.lambdify(x, expr, modules="numpy")
    return x, expr, lambda value: float(np.asarray(fn(value)).reshape(()))


def _root_study(req: NumericalAnalysisRequest):
    x, expr, fn = _expr_function(req)
    results = {}
    if req.bracket:
        a, b = map(float, req.bracket)
        bis = optimize.root_scalar(
            fn, bracket=(a, b), method="bisect",
            xtol=req.tolerance, maxiter=req.maxIterations
        )
        brent = optimize.root_scalar(
            fn, bracket=(a, b), method="brentq",
            xtol=req.tolerance, maxiter=req.maxIterations
        )
        results["bisection"] = {
            "root": float(bis.root), "converged": bool(bis.converged),
            "iterations": int(bis.iterations), "functionCalls": int(bis.function_calls),
            "residual": abs(fn(bis.root)),
        }
        results["brentq"] = {
            "root": float(brent.root), "converged": bool(brent.converged),
            "iterations": int(brent.iterations), "functionCalls": int(brent.function_calls),
            "residual": abs(fn(brent.root)),
        }
    if req.initialGuess is not None:
        deriv = sp.diff(expr, x)
        dfn0 = sp.lambdify(x, deriv, modules="numpy")
        dfn = lambda value: float(np.asarray(dfn0(value)).reshape(()))
        newton = optimize.root_scalar(
            fn, x0=req.initialGuess, fprime=dfn, method="newton",
            xtol=req.tolerance, maxiter=req.maxIterations
        )
        results["newton"] = {
            "root": float(newton.root), "converged": bool(newton.converged),
            "iterations": int(newton.iterations), "functionCalls": int(newton.function_calls),
            "residual": abs(fn(newton.root)),
        }
    if req.initialGuess is not None and req.secondGuess is not None:
        secant = optimize.root_scalar(
            fn, x0=req.initialGuess, x1=req.secondGuess, method="secant",
            xtol=req.tolerance, maxiter=req.maxIterations
        )
        results["secant"] = {
            "root": float(secant.root), "converged": bool(secant.converged),
            "iterations": int(secant.iterations), "functionCalls": int(secant.function_calls),
            "residual": abs(fn(secant.root)),
        }
    if not results:
        raise ValueError("root-study requires a bracket and/or initial guesses")
    best = min(
        (v for v in results.values() if v["converged"]),
        key=lambda d: d["residual"],
        default=None
    )
    return {
        "result": {"methods": results, "bestByResidual": best},
        "method": "root-method-comparison",
        "verification": {
            "allReportedResidualsFinite": all(np.isfinite(v["residual"]) for v in results.values())
        },
    }


def _differentiate(req: NumericalAnalysisRequest):
    x, expr, fn = _expr_function(req)
    if req.point is None:
        raise ValueError("differentiate requires point")
    h = float(req.step)
    p = float(req.point)
    forward = (fn(p + h) - fn(p)) / h
    backward = (fn(p) - fn(p - h)) / h
    central = (fn(p + h) - fn(p - h)) / (2*h)
    exact_expr = sp.diff(expr, x)
    exact = float(sp.N(exact_expr.subs(x, p)))
    return {
        "result": {
            "forward": forward,
            "backward": backward,
            "central": central,
            "symbolicReference": exact,
            "absoluteErrors": {
                "forward": abs(forward-exact),
                "backward": abs(backward-exact),
                "central": abs(central-exact),
            },
            "step": h,
        },
        "method": "finite-difference-comparison",
        "verification": {"centralImprovesFirstOrderAtSmallStep": abs(central-exact) <= max(abs(forward-exact), abs(backward-exact))},
    }


def _integrate(req: NumericalAnalysisRequest):
    _, _, fn = _expr_function(req)
    if req.interval is None:
        raise ValueError("integrate requires interval")
    a, b = map(float, req.interval)
    n = req.samples if req.samples % 2 == 1 else req.samples + 1
    xs = np.linspace(a, b, n)
    ys = np.asarray([fn(v) for v in xs], dtype=float)
    trap = float(np.trapezoid(ys, xs))
    simp = float(integrate.simpson(ys, x=xs))
    quad, quad_err = integrate.quad(fn, a, b, epsabs=req.tolerance, epsrel=req.tolerance)
    exact = None
    if req.exactValue is not None:
        exact = float(req.exactValue)
    result = {
        "trapezoid": trap,
        "simpson": simp,
        "adaptiveQuad": float(quad),
        "adaptiveQuadEstimatedError": float(quad_err),
        "samples": n,
    }
    if exact is not None:
        result["reference"] = exact
        result["absoluteErrors"] = {
            "trapezoid": abs(trap-exact),
            "simpson": abs(simp-exact),
            "adaptiveQuad": abs(float(quad)-exact),
        }
    return {
        "result": result,
        "method": "quadrature-comparison",
        "verification": {"adaptiveQuadFinite": bool(np.isfinite(quad))},
    }


def _interpolate(req: NumericalAnalysisRequest):
    if len(req.xValues) != len(req.yValues) or len(req.xValues) < 2:
        raise ValueError("interpolate requires equal-length xValues/yValues with at least 2 points")
    if not req.evaluationPoints:
        raise ValueError("interpolate requires evaluationPoints")
    x = np.asarray(req.xValues, dtype=float)
    y = np.asarray(req.yValues, dtype=float)
    points = np.asarray(req.evaluationPoints, dtype=float)
    poly = interpolate.BarycentricInterpolator(x, y)
    poly_values = np.asarray(poly(points), dtype=float)
    result = {
        "evaluationPoints": points.tolist(),
        "polynomial": poly_values.tolist(),
    }
    if len(x) >= 3:
        cubic = interpolate.CubicSpline(x, y)
        result["cubicSpline"] = np.asarray(cubic(points), dtype=float).tolist()
    return {
        "result": result,
        "method": "barycentric-polynomial-and-cubic-spline",
        "verification": {
            "interpolatesNodes": bool(np.allclose(np.asarray(poly(x), dtype=float), y, atol=req.tolerance, rtol=0))
        },
    }


def _convergence_study(req: NumericalAnalysisRequest):
    _, _, fn = _expr_function(req)
    if req.point is None:
        raise ValueError("convergence-study requires point")
    if len(req.steps) < 3:
        raise ValueError("convergence-study requires at least 3 step sizes")
    p = float(req.point)
    x = sp.Symbol(req.variable, real=True)
    expr = sp.sympify(req.expression, locals={req.variable: x})
    exact = float(sp.N(sp.diff(expr, x).subs(x, p)))
    rows = []
    for h in req.steps:
        h = float(h)
        approx = (fn(p+h)-fn(p-h))/(2*h)
        err = abs(approx-exact)
        rows.append({"step": h, "approximation": approx, "absoluteError": err})
    orders = []
    for i in range(1, len(rows)-0):
        if i >= len(rows):
            break
        e0 = rows[i-1]["absoluteError"]
        e1 = rows[i]["absoluteError"]
        h0 = rows[i-1]["step"]
        h1 = rows[i]["step"]
        if e0 > 0 and e1 > 0 and h0 != h1:
            orders.append(float(np.log(e0/e1)/np.log(h0/h1)))
    return {
        "result": {
            "referenceDerivative": exact,
            "study": rows,
            "observedOrders": orders,
            "meanObservedOrder": float(np.mean(orders)) if orders else None,
        },
        "method": "central-difference-convergence-study",
        "verification": {"finiteErrors": all(np.isfinite(r["absoluteError"]) for r in rows)},
    }


def _conditioning(req: NumericalAnalysisRequest):
    if req.matrix is None:
        raise ValueError("conditioning requires matrix")
    A = np.asarray(req.matrix, dtype=float)
    if A.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    s = np.linalg.svd(A, compute_uv=False)
    cond2 = float(np.linalg.cond(A, 2))
    cond1 = float(np.linalg.cond(A, 1)) if A.shape[0] == A.shape[1] else None
    condinf = float(np.linalg.cond(A, np.inf)) if A.shape[0] == A.shape[1] else None
    return {
        "result": {
            "conditionNumber2": cond2,
            "conditionNumber1": cond1,
            "conditionNumberInf": condinf,
            "singularValues": s.tolist(),
            "rank": int(np.linalg.matrix_rank(A)),
        },
        "method": "svd-conditioning-analysis",
        "verification": {
            "illConditionedAt1e12": bool(cond2 >= 1e12),
            "finiteConditionNumber": bool(np.isfinite(cond2)),
        },
    }


def execute_numerical_analysis(req: NumericalAnalysisRequest) -> Dict[str, Any]:
    handlers = {
        "root-study": _root_study,
        "differentiate": _differentiate,
        "integrate": _integrate,
        "interpolate": _interpolate,
        "convergence-study": _convergence_study,
        "conditioning": _conditioning,
    }
    payload = handlers[req.operation](req)
    body = {
        "ok": True,
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "operation": req.operation,
        "engine": "sympy-numpy-scipy",
        "runtime": "python",
        "method": payload["method"],
        "result": payload["result"],
        "verification": payload["verification"],
        "wordpressRequired": False,
    }
    body["resultHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "resultHash"}}
    )
    return body


def calculation_object_extension(req: UnifiedCalculationRequest, analysis_req: NumericalAnalysisRequest):
    obj = build_calculation_object(req)
    result = execute_numerical_analysis(analysis_req)
    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["numericalAnalysis"] = result
    obj["result"]["numericalAnalysis"] = result["result"]
    obj["executionPlan"]["numericalAnalysis"] = {
        "runtime": "python",
        "engine": "sympy-numpy-scipy",
        "operation": analysis_req.operation,
        "method": result["method"],
        "tolerance": analysis_req.tolerance,
    }
    obj["verification"]["numericalAnalysis"] = result["verification"]
    obj["provenance"]["numericalAnalysisResultHash"] = result["resultHash"]
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Numerical Analysis Laboratory",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "sympy-numpy-scipy",
        "wordpressRequired": False,
        "capabilities": {
            "rootMethodComparison": True,
            "finiteDifferenceDifferentiation": True,
            "quadratureComparison": True,
            "polynomialInterpolation": True,
            "cubicSplineInterpolation": True,
            "convergenceOrderEstimation": True,
            "conditioningAnalysis": True,
            "errorDiagnostics": True,
            "calculationObjectExtension": True,
        },
        "methods": [
            "bisection", "brentq", "newton", "secant",
            "forward-difference", "backward-difference", "central-difference",
            "trapezoid", "simpson", "adaptive-quad",
            "barycentric-interpolation", "cubic-spline", "svd-conditioning",
        ],
    }


@router.get("/v11110/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/numerical-analysis")
def numerical_analysis_route(req: NumericalAnalysisRequest):
    return execute_numerical_analysis(req)


@router.post("/calculation-engine/v1/numerical-analysis/calculation-object")
def numerical_analysis_calculation_object_route(req: NumericalCalculationObjectRequest):
    return calculation_object_extension(
        req.calculationObjectRequest,
        req.numericalAnalysis,
    )

"""Workbench v5.6.0 — Numerical Methods & Scientific Computing.

Bounded numerical root finding, integration, interpolation, differentiation,
initial-value ODE solving, linear algebra, and bounded optimization. User
expressions are parsed only by the v5.1 restricted AST -> SymPy allow-list.
No Python eval/exec, shell execution, or arbitrary callable upload is exposed.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

import numpy as np
import scipy
import sympy as sp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from scipy import integrate as scipy_integrate
from scipy import interpolate as scipy_interpolate
from scipy import optimize as scipy_optimize
from scipy.integrate import solve_ivp

from app.v510 import RestrictedSympyParser, content_hash
from app.v520 import _linspace, _safe_real

VERSION = "5.6.0"
SCHEMA = "sc-workbench-numerical-methods-object/1.0"
MAX_PARAMETERS = 8
MAX_SAMPLES = 1001
MAX_POINTS = 1001
MAX_STATES = 8
MAX_MATRIX_DIM = 16
MAX_OPT_VARIABLES = 6

router = APIRouter(prefix="/v560", tags=["workbench-v560-numerical-scientific-computing"])


def _finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite.")
    return number


def _finite_list(values: Sequence[float], label: str) -> List[float]:
    return [_finite(value, f"{label}[{idx}]") for idx, value in enumerate(values)]


def _range(lo: float, hi: float, label: str) -> Tuple[float, float]:
    lo = _finite(lo, f"{label} minimum")
    hi = _finite(hi, f"{label} maximum")
    if lo >= hi:
        raise ValueError(f"{label} minimum must be less than maximum.")
    return lo, hi


def _record(kind: str, source: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "schema": SCHEMA,
        "version": VERSION,
        "kind": kind,
        "source": source,
        **payload,
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
        "automaticDeviceProgrammingAuthorized": False,
    }
    value["numericalObjectHash"] = content_hash(value)
    return value


def _parser_for(variable_names: Sequence[str], parameter_names: Sequence[str] = ()) -> RestrictedSympyParser:
    names = list(variable_names) + list(parameter_names)
    if len(set(names)) != len(names):
        raise ValueError("Variable and parameter names must be unique.")
    return RestrictedSympyParser(names)


def _param_subs(parser: RestrictedSympyParser, parameters: Dict[str, float]) -> Dict[sp.Symbol, float]:
    if len(parameters) > MAX_PARAMETERS:
        raise ValueError(f"At most {MAX_PARAMETERS} parameters are supported.")
    return {parser.symbol(name): _finite(value, f"parameter {name}") for name, value in parameters.items()}


def _scalar(expr: sp.Expr, substitutions: Dict[sp.Symbol, float], label: str = "expression") -> float:
    value = _safe_real(expr, substitutions)
    if value is None or not math.isfinite(value):
        raise ValueError(f"{label} did not evaluate to a finite real number.")
    return float(value)


class RootInput(BaseModel):
    expression: str
    variable: str = "x"
    method: Literal["brentq", "bisection", "secant", "newton"] = "brentq"
    bracket: Optional[List[float]] = Field(default_factory=lambda: [-10.0, 10.0], min_length=2, max_length=2)
    initialGuess: Optional[float] = None
    secondGuess: Optional[float] = None
    tolerance: float = Field(default=1e-10, gt=0, le=1e-2)
    maxIterations: int = Field(default=100, ge=4, le=500)
    parameters: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_root(self):
        if self.bracket is not None:
            _range(self.bracket[0], self.bracket[1], "root bracket")
        if self.initialGuess is not None:
            _finite(self.initialGuess, "initialGuess")
        if self.secondGuess is not None:
            _finite(self.secondGuess, "secondGuess")
        if self.method in {"brentq", "bisection"} and self.bracket is None:
            raise ValueError(f"{self.method} requires a bracket.")
        if self.method in {"newton", "secant"} and self.initialGuess is None:
            raise ValueError(f"{self.method} requires initialGuess.")
        return self


class IntegrationInput(BaseModel):
    expression: str
    variable: str = "x"
    lower: float = 0.0
    upper: float = 1.0
    method: Literal["adaptive", "simpson", "trapezoid"] = "adaptive"
    samples: int = Field(default=401, ge=5, le=MAX_SAMPLES)
    tolerance: float = Field(default=1e-9, gt=0, le=1e-2)
    parameters: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_integration(self):
        _range(self.lower, self.upper, "integration interval")
        if self.method == "simpson" and self.samples < 5:
            raise ValueError("Simpson integration requires at least 5 samples.")
        return self


class DifferentiationInput(BaseModel):
    expression: str
    variable: str = "x"
    x: float = 0.0
    order: Literal[1, 2] = 1
    step: float = Field(default=1e-5, gt=0, le=1.0)
    parameters: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_differentiation(self):
        _finite(self.x, "x")
        return self


class InterpolationInput(BaseModel):
    xValues: List[float] = Field(min_length=2, max_length=MAX_POINTS)
    yValues: List[float] = Field(min_length=2, max_length=MAX_POINTS)
    method: Literal["linear", "cubic-spline", "pchip"] = "pchip"
    evaluateAt: List[float] = Field(default_factory=list, max_length=MAX_POINTS)
    outputSamples: int = Field(default=201, ge=2, le=MAX_SAMPLES)

    @model_validator(mode="after")
    def validate_interpolation(self):
        if len(self.xValues) != len(self.yValues):
            raise ValueError("xValues and yValues must have equal length.")
        xs = _finite_list(self.xValues, "xValues")
        _finite_list(self.yValues, "yValues")
        if len(set(xs)) != len(xs):
            raise ValueError("xValues must be unique.")
        if self.method == "cubic-spline" and len(xs) < 3:
            raise ValueError("Cubic spline interpolation requires at least 3 points.")
        _finite_list(self.evaluateAt, "evaluateAt")
        return self


class ODEInput(BaseModel):
    equations: List[str] = Field(min_length=1, max_length=MAX_STATES)
    stateNames: List[str] = Field(min_length=1, max_length=MAX_STATES)
    initialValues: List[float] = Field(min_length=1, max_length=MAX_STATES)
    tMin: float = 0.0
    tMax: float = 10.0
    samples: int = Field(default=201, ge=2, le=MAX_SAMPLES)
    method: Literal["RK45", "DOP853", "Radau", "BDF"] = "RK45"
    relativeTolerance: float = Field(default=1e-7, gt=0, le=1e-2)
    absoluteTolerance: float = Field(default=1e-9, gt=0, le=1e-2)
    parameters: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ode(self):
        if not (len(self.equations) == len(self.stateNames) == len(self.initialValues)):
            raise ValueError("equations, stateNames, and initialValues must have equal length.")
        _range(self.tMin, self.tMax, "ODE time interval")
        _finite_list(self.initialValues, "initialValues")
        return self


class LinearAlgebraInput(BaseModel):
    operation: Literal["solve", "eigen", "svd", "least-squares", "inverse"] = "solve"
    matrix: List[List[float]] = Field(min_length=1, max_length=MAX_MATRIX_DIM)
    vector: Optional[List[float]] = Field(default=None, max_length=MAX_MATRIX_DIM)

    @model_validator(mode="after")
    def validate_matrix(self):
        if not self.matrix or not self.matrix[0]:
            raise ValueError("matrix must not be empty.")
        columns = len(self.matrix[0])
        if columns > MAX_MATRIX_DIM:
            raise ValueError(f"Matrix dimension is limited to {MAX_MATRIX_DIM}.")
        for row in self.matrix:
            if len(row) != columns:
                raise ValueError("matrix rows must have equal length.")
            _finite_list(row, "matrix row")
        rows = len(self.matrix)
        if self.operation in {"solve", "eigen", "inverse"} and rows != columns:
            raise ValueError(f"{self.operation} requires a square matrix.")
        if self.operation in {"solve", "least-squares"}:
            if self.vector is None or len(self.vector) != rows:
                raise ValueError(f"{self.operation} requires a vector with one value per matrix row.")
            _finite_list(self.vector, "vector")
        return self


class OptimizationInput(BaseModel):
    expression: str
    variables: List[str] = Field(min_length=1, max_length=MAX_OPT_VARIABLES)
    initial: List[float] = Field(min_length=1, max_length=MAX_OPT_VARIABLES)
    bounds: List[List[float]] = Field(min_length=1, max_length=MAX_OPT_VARIABLES)
    goal: Literal["minimize", "maximize"] = "minimize"
    tolerance: float = Field(default=1e-9, gt=0, le=1e-2)
    maxIterations: int = Field(default=300, ge=10, le=2000)
    parameters: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_optimization(self):
        if not (len(self.variables) == len(self.initial) == len(self.bounds)):
            raise ValueError("variables, initial, and bounds must have equal length.")
        _finite_list(self.initial, "initial")
        for idx, bound in enumerate(self.bounds):
            if len(bound) != 2:
                raise ValueError("Each optimization bound must contain [minimum, maximum].")
            lo, hi = _range(bound[0], bound[1], f"bounds[{idx}]")
            if not lo <= self.initial[idx] <= hi:
                raise ValueError(f"initial[{idx}] must lie within bounds[{idx}].")
        return self


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-numerical-methods-status/1.0",
        "version": VERSION,
        "engine": "NumPy + SciPy + restricted SymPy",
        "numpyVersion": np.__version__,
        "scipyVersion": scipy.__version__,
        "capabilities": [
            "numerical-root-finding",
            "adaptive-quadrature",
            "composite-simpson",
            "composite-trapezoid",
            "finite-difference-derivatives",
            "linear-interpolation",
            "cubic-spline-interpolation",
            "shape-preserving-pchip",
            "initial-value-ode-solving",
            "stiff-ode-methods",
            "linear-system-solving",
            "eigen-analysis",
            "singular-value-decomposition",
            "least-squares",
            "bounded-multivariable-optimization",
            "canonical-numerical-objects",
        ],
        "limits": {
            "maxSamples": MAX_SAMPLES,
            "maxInterpolationPoints": MAX_POINTS,
            "maxODEStates": MAX_STATES,
            "maxMatrixDimension": MAX_MATRIX_DIM,
            "maxOptimizationVariables": MAX_OPT_VARIABLES,
            "maxParameters": MAX_PARAMETERS,
        },
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
    }


def root_object(payload: RootInput) -> Dict[str, Any]:
    parser = _parser_for([payload.variable], payload.parameters.keys())
    x = parser.symbol(payload.variable)
    expr = parser.parse(payload.expression)
    params = _param_subs(parser, payload.parameters)

    def fn(value: float) -> float:
        return _scalar(expr, {x: float(value), **params}, "root expression")

    iterations = None
    function_calls = None
    if payload.method in {"brentq", "bisection"}:
        assert payload.bracket is not None
        lo, hi = _range(payload.bracket[0], payload.bracket[1], "root bracket")
        flo, fhi = fn(lo), fn(hi)
        if flo == 0:
            root, converged = lo, True
        elif fhi == 0:
            root, converged = hi, True
        else:
            if flo * fhi > 0:
                raise ValueError("Root bracket must contain a sign change.")
            solver = scipy_optimize.brentq if payload.method == "brentq" else scipy_optimize.bisect
            root, info = solver(fn, lo, hi, xtol=payload.tolerance, maxiter=payload.maxIterations, full_output=True, disp=False)
            converged = bool(info.converged)
            iterations = int(info.iterations)
            function_calls = int(info.function_calls)
    elif payload.method == "secant":
        x0 = float(payload.initialGuess)
        x1 = float(payload.secondGuess) if payload.secondGuess is not None else x0 + max(1e-4, abs(x0) * 1e-3)
        result = scipy_optimize.root_scalar(fn, method="secant", x0=x0, x1=x1, xtol=payload.tolerance, maxiter=payload.maxIterations)
        root, converged = float(result.root), bool(result.converged)
        iterations = int(result.iterations)
        function_calls = int(result.function_calls)
    else:
        x0 = float(payload.initialGuess)
        derivative = sp.diff(expr, x)

        def dfn(value: float) -> float:
            return _scalar(derivative, {x: float(value), **params}, "root derivative")

        result = scipy_optimize.root_scalar(fn, method="newton", x0=x0, fprime=dfn, xtol=payload.tolerance, maxiter=payload.maxIterations)
        root, converged = float(result.root), bool(result.converged)
        iterations = int(result.iterations)
        function_calls = int(result.function_calls)

    residual = fn(root)
    result = _record(
        "root",
        payload.model_dump(),
        {
            "expression": str(expr),
            "latex": sp.latex(expr),
            "root": round(float(root), 14),
            "residual": round(float(residual), 14),
            "converged": converged,
            "iterations": iterations,
            "functionCalls": function_calls,
            "method": payload.method,
        },
    )
    return {"ok": True, "result": result}


def integration_object(payload: IntegrationInput) -> Dict[str, Any]:
    parser = _parser_for([payload.variable], payload.parameters.keys())
    x = parser.symbol(payload.variable)
    expr = parser.parse(payload.expression)
    params = _param_subs(parser, payload.parameters)
    lo, hi = _range(payload.lower, payload.upper, "integration interval")

    def fn(value: float) -> float:
        return _scalar(expr, {x: float(value), **params}, "integration expression")

    xs = np.linspace(lo, hi, payload.samples)
    ys = np.asarray([fn(float(value)) for value in xs], dtype=float)
    error_estimate: Optional[float] = None
    if payload.method == "adaptive":
        value, error_estimate = scipy_integrate.quad(fn, lo, hi, epsabs=payload.tolerance, epsrel=payload.tolerance, limit=200)
    elif payload.method == "simpson":
        value = float(scipy_integrate.simpson(ys, x=xs))
    else:
        value = float(np.trapezoid(ys, xs))

    sample_stride = max(1, math.ceil(payload.samples / 201))
    sampled_curve = [
        {"x": round(float(xs[i]), 12), "y": round(float(ys[i]), 12)}
        for i in range(0, len(xs), sample_stride)
    ]
    result = _record(
        "integration",
        payload.model_dump(),
        {
            "expression": str(expr),
            "latex": sp.latex(expr),
            "value": round(float(value), 14),
            "estimatedAbsoluteError": None if error_estimate is None else round(float(error_estimate), 14),
            "method": payload.method,
            "interval": [lo, hi],
            "sampleCount": int(payload.samples),
            "curve": sampled_curve,
        },
    )
    return {"ok": True, "result": result}


def differentiation_object(payload: DifferentiationInput) -> Dict[str, Any]:
    parser = _parser_for([payload.variable], payload.parameters.keys())
    x = parser.symbol(payload.variable)
    expr = parser.parse(payload.expression)
    params = _param_subs(parser, payload.parameters)
    x0, h = float(payload.x), float(payload.step)

    def fn(value: float) -> float:
        return _scalar(expr, {x: float(value), **params}, "differentiation expression")

    if payload.order == 1:
        value = (fn(x0 - 2*h) - 8*fn(x0 - h) + 8*fn(x0 + h) - fn(x0 + 2*h)) / (12*h)
        symbolic = sp.diff(expr, x)
    else:
        value = (-fn(x0 + 2*h) + 16*fn(x0 + h) - 30*fn(x0) + 16*fn(x0 - h) - fn(x0 - 2*h)) / (12*h*h)
        symbolic = sp.diff(expr, x, 2)
    symbolic_value = _safe_real(symbolic, {x: x0, **params})
    result = _record(
        "differentiation",
        payload.model_dump(),
        {
            "expression": str(expr),
            "order": payload.order,
            "x": x0,
            "step": h,
            "finiteDifferenceValue": round(float(value), 14),
            "symbolicDerivative": str(symbolic),
            "symbolicValue": None if symbolic_value is None else round(float(symbolic_value), 14),
            "absoluteDifferenceFromSymbolic": None if symbolic_value is None else round(abs(float(value) - float(symbolic_value)), 14),
        },
    )
    return {"ok": True, "result": result}


def interpolation_object(payload: InterpolationInput) -> Dict[str, Any]:
    pairs = sorted(zip(payload.xValues, payload.yValues), key=lambda item: item[0])
    xs = np.asarray([float(item[0]) for item in pairs], dtype=float)
    ys = np.asarray([float(item[1]) for item in pairs], dtype=float)
    if payload.method == "linear":
        interpolator = scipy_interpolate.interp1d(xs, ys, kind="linear", bounds_error=False, fill_value=np.nan)
        coefficient_payload = None
    elif payload.method == "cubic-spline":
        interpolator = scipy_interpolate.CubicSpline(xs, ys, extrapolate=False)
        coefficient_payload = np.asarray(interpolator.c).round(12).tolist()
    else:
        interpolator = scipy_interpolate.PchipInterpolator(xs, ys, extrapolate=False)
        coefficient_payload = np.asarray(interpolator.c).round(12).tolist()

    output_x = np.linspace(float(xs[0]), float(xs[-1]), payload.outputSamples)
    output_y = np.asarray(interpolator(output_x), dtype=float)
    requested = []
    for value in payload.evaluateAt:
        y = float(interpolator(float(value)))
        requested.append({"x": round(float(value), 12), "y": None if not math.isfinite(y) else round(y, 12)})
    curve = [
        {"x": round(float(xv), 12), "y": round(float(yv), 12)}
        for xv, yv in zip(output_x, output_y)
        if math.isfinite(float(yv))
    ]
    result = _record(
        "interpolation",
        payload.model_dump(),
        {
            "method": payload.method,
            "inputPoints": [{"x": round(float(x), 12), "y": round(float(y), 12)} for x, y in zip(xs, ys)],
            "evaluatedPoints": requested,
            "curve": curve,
            "coefficients": coefficient_payload,
            "domain": [round(float(xs[0]), 12), round(float(xs[-1]), 12)],
        },
    )
    return {"ok": True, "result": result}


def ode_object(payload: ODEInput) -> Dict[str, Any]:
    parser = _parser_for(["t", *payload.stateNames], payload.parameters.keys())
    t_symbol = parser.symbol("t")
    state_symbols = [parser.symbol(name) for name in payload.stateNames]
    equations = [parser.parse(text) for text in payload.equations]
    params = _param_subs(parser, payload.parameters)
    t0, t1 = _range(payload.tMin, payload.tMax, "ODE time interval")

    def rhs(t: float, y: np.ndarray) -> List[float]:
        substitutions: Dict[sp.Symbol, float] = {t_symbol: float(t), **params}
        substitutions.update({symbol: float(value) for symbol, value in zip(state_symbols, y)})
        return [_scalar(expr, substitutions, f"ODE equation {idx}") for idx, expr in enumerate(equations)]

    t_eval = np.linspace(t0, t1, payload.samples)
    solution = solve_ivp(
        rhs,
        (t0, t1),
        np.asarray(payload.initialValues, dtype=float),
        t_eval=t_eval,
        method=payload.method,
        rtol=payload.relativeTolerance,
        atol=payload.absoluteTolerance,
        max_step=(t1 - t0) / max(20, min(payload.samples - 1, 200)),
    )
    if not solution.success:
        raise ValueError(f"ODE solver failed: {solution.message}")
    series = []
    for idx, name in enumerate(payload.stateNames):
        series.append({
            "state": name,
            "points": [
                {"t": round(float(t), 12), "value": round(float(v), 12)}
                for t, v in zip(solution.t, solution.y[idx])
            ],
        })
    result = _record(
        "ode",
        payload.model_dump(),
        {
            "method": payload.method,
            "equations": [str(expr) for expr in equations],
            "stateNames": payload.stateNames,
            "successful": True,
            "message": solution.message,
            "functionEvaluations": int(solution.nfev),
            "jacobianEvaluations": None if solution.njev is None else int(solution.njev),
            "timeRange": [t0, t1],
            "series": series,
            "finalState": {name: round(float(solution.y[idx, -1]), 12) for idx, name in enumerate(payload.stateNames)},
        },
    )
    return {"ok": True, "result": result}


def _complex_record(value: complex) -> Dict[str, float]:
    return {"real": round(float(np.real(value)), 12), "imag": round(float(np.imag(value)), 12)}


def linear_algebra_object(payload: LinearAlgebraInput) -> Dict[str, Any]:
    matrix = np.asarray(payload.matrix, dtype=float)
    rank = int(np.linalg.matrix_rank(matrix))
    condition = float(np.linalg.cond(matrix)) if matrix.size else math.inf
    common = {
        "operation": payload.operation,
        "shape": [int(matrix.shape[0]), int(matrix.shape[1])],
        "rank": rank,
        "conditionNumber": None if not math.isfinite(condition) else round(condition, 12),
    }
    if payload.operation == "solve":
        vector = np.asarray(payload.vector, dtype=float)
        try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError as exc:
            raise ValueError(f"Linear solve failed: {exc}") from exc
        residual = matrix @ solution - vector
        details = {"solution": solution.round(12).tolist(), "residualNorm": round(float(np.linalg.norm(residual)), 14)}
    elif payload.operation == "eigen":
        values, vectors = np.linalg.eig(matrix)
        details = {
            "eigenvalues": [_complex_record(value) for value in values],
            "eigenvectors": [[_complex_record(value) for value in row] for row in vectors],
        }
    elif payload.operation == "svd":
        u, singular, vt = np.linalg.svd(matrix, full_matrices=False)
        details = {"singularValues": singular.round(12).tolist(), "u": u.round(12).tolist(), "vt": vt.round(12).tolist()}
    elif payload.operation == "least-squares":
        vector = np.asarray(payload.vector, dtype=float)
        solution, residuals, ls_rank, singular = np.linalg.lstsq(matrix, vector, rcond=None)
        residual_vector = matrix @ solution - vector
        details = {
            "solution": solution.round(12).tolist(),
            "leastSquaresRank": int(ls_rank),
            "singularValues": singular.round(12).tolist(),
            "residualNorm": round(float(np.linalg.norm(residual_vector)), 14),
            "reportedResiduals": np.asarray(residuals).round(12).tolist(),
        }
    else:
        try:
            inverse = np.linalg.inv(matrix)
        except np.linalg.LinAlgError as exc:
            raise ValueError(f"Matrix inverse failed: {exc}") from exc
        details = {"inverse": inverse.round(12).tolist(), "determinant": round(float(np.linalg.det(matrix)), 12)}
    result = _record("linear-algebra", payload.model_dump(), {**common, **details})
    return {"ok": True, "result": result}


def optimization_object(payload: OptimizationInput) -> Dict[str, Any]:
    parser = _parser_for(payload.variables, payload.parameters.keys())
    variables = [parser.symbol(name) for name in payload.variables]
    expr = parser.parse(payload.expression)
    params = _param_subs(parser, payload.parameters)
    sign = 1.0 if payload.goal == "minimize" else -1.0

    def objective(values: np.ndarray) -> float:
        substitutions: Dict[sp.Symbol, float] = {symbol: float(value) for symbol, value in zip(variables, values)}
        substitutions.update(params)
        return sign * _scalar(expr, substitutions, "optimization expression")

    result_raw = scipy_optimize.minimize(
        objective,
        np.asarray(payload.initial, dtype=float),
        method="L-BFGS-B",
        bounds=[(float(bound[0]), float(bound[1])) for bound in payload.bounds],
        options={"maxiter": payload.maxIterations, "ftol": payload.tolerance},
    )
    optimum_value = sign * float(result_raw.fun)
    point = {name: round(float(value), 12) for name, value in zip(payload.variables, result_raw.x)}
    gradient_norm = None
    if getattr(result_raw, "jac", None) is not None:
        gradient_norm = round(float(np.linalg.norm(np.asarray(result_raw.jac, dtype=float))), 12)
    result = _record(
        "optimization",
        payload.model_dump(),
        {
            "expression": str(expr),
            "latex": sp.latex(expr),
            "goal": payload.goal,
            "method": "L-BFGS-B",
            "success": bool(result_raw.success),
            "message": str(result_raw.message),
            "iterations": int(result_raw.nit),
            "functionEvaluations": int(result_raw.nfev),
            "point": point,
            "value": round(optimum_value, 14),
            "projectedGradientNorm": gradient_norm,
        },
    )
    return {"ok": True, "result": result}


def _guard(callable_):
    try:
        return callable_()
    except (ValueError, TypeError, ZeroDivisionError, np.linalg.LinAlgError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Numerical engine could not complete the operation: {exc}") from exc


@router.get("/status")
def status() -> Dict[str, Any]:
    return status_record()


@router.post("/root")
def root_endpoint(payload: RootInput) -> Dict[str, Any]:
    return _guard(lambda: root_object(payload))


@router.post("/integrate")
def integrate_endpoint(payload: IntegrationInput) -> Dict[str, Any]:
    return _guard(lambda: integration_object(payload))


@router.post("/differentiate")
def differentiate_endpoint(payload: DifferentiationInput) -> Dict[str, Any]:
    return _guard(lambda: differentiation_object(payload))


@router.post("/interpolate")
def interpolate_endpoint(payload: InterpolationInput) -> Dict[str, Any]:
    return _guard(lambda: interpolation_object(payload))


@router.post("/ode")
def ode_endpoint(payload: ODEInput) -> Dict[str, Any]:
    return _guard(lambda: ode_object(payload))


@router.post("/linear-algebra")
def linear_algebra_endpoint(payload: LinearAlgebraInput) -> Dict[str, Any]:
    return _guard(lambda: linear_algebra_object(payload))


@router.post("/optimize")
def optimize_endpoint(payload: OptimizationInput) -> Dict[str, Any]:
    return _guard(lambda: optimization_object(payload))

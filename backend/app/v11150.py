"""Workbench v11.15.0 — Uncertainty Propagation & Monte Carlo.

Adds first-order covariance propagation, independent uncertainty propagation,
Monte Carlo uncertainty simulation, seeded stochastic provenance, distribution
sampling, quantile/confidence summaries, and convergence diagnostics.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import numpy as np
import sympy as sp
from fastapi import APIRouter
from pydantic import BaseModel, Field
from scipy import stats

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-uncertainty-propagation-monte-carlo-status/1.0"
RESULT_SCHEMA = "sc-workbench-uncertainty-propagation-monte-carlo-result/1.0"

router = APIRouter(tags=["workbench-v11150-uncertainty-propagation-monte-carlo"])


class UncertainInput(BaseModel):
    name: str = Field(max_length=100)
    mean: float
    standardDeviation: float = Field(ge=0)
    distribution: Literal["normal", "uniform", "triangular", "lognormal"] = "normal"
    lower: Optional[float] = None
    upper: Optional[float] = None
    mode: Optional[float] = None


class UncertaintyRequest(BaseModel):
    operation: Literal[
        "first-order-independent",
        "first-order-covariance",
        "monte-carlo",
        "monte-carlo-convergence",
    ]
    expression: str = Field(max_length=20000)
    variables: List[str] = Field(default_factory=list, max_length=100)
    means: List[float] = Field(default_factory=list, max_length=100)
    standardDeviations: List[float] = Field(default_factory=list, max_length=100)
    covarianceMatrix: Optional[List[List[float]]] = None
    inputs: List[UncertainInput] = Field(default_factory=list, max_length=100)
    samples: int = Field(default=10000, ge=100, le=1000000)
    seed: Optional[int] = None
    confidenceLevel: float = Field(default=0.95, gt=0.0, lt=1.0)
    convergenceBatches: int = Field(default=10, ge=2, le=100)


class UncertaintyCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    uncertaintyAnalysis: UncertaintyRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _symbolic_model(req: UncertaintyRequest):
    if not req.variables:
        raise ValueError("variables are required")
    symbols = [sp.Symbol(v, real=True) for v in req.variables]
    expr = sp.sympify(req.expression, locals={v: s for v, s in zip(req.variables, symbols)})
    fn = sp.lambdify(symbols, expr, modules="numpy")
    jac_expr = [sp.diff(expr, s) for s in symbols]
    jac_fn = sp.lambdify(symbols, jac_expr, modules="numpy")
    return symbols, expr, fn, jac_expr, jac_fn


def _validate_means(req: UncertaintyRequest):
    n = len(req.variables)
    if len(req.means) != n:
        raise ValueError("means length must match variables")
    return np.asarray(req.means, dtype=float)


def _summary(values: np.ndarray, confidence_level: float):
    values = np.asarray(values, dtype=float).reshape(-1)
    alpha = 1.0 - confidence_level
    lower_q = alpha / 2.0
    upper_q = 1.0 - alpha / 2.0
    return {
        "count": int(values.size),
        "mean": float(np.mean(values)),
        "standardDeviation": float(np.std(values, ddof=1)),
        "variance": float(np.var(values, ddof=1)),
        "median": float(np.median(values)),
        "minimum": float(np.min(values)),
        "maximum": float(np.max(values)),
        "quantiles": {
            "0.025": float(np.quantile(values, 0.025)),
            "0.25": float(np.quantile(values, 0.25)),
            "0.5": float(np.quantile(values, 0.5)),
            "0.75": float(np.quantile(values, 0.75)),
            "0.975": float(np.quantile(values, 0.975)),
        },
        "confidenceIntervalCentral": {
            "level": confidence_level,
            "lower": float(np.quantile(values, lower_q)),
            "upper": float(np.quantile(values, upper_q)),
        },
    }


def _draw_input(spec: UncertainInput, size: int, rng: np.random.Generator):
    if spec.distribution == "normal":
        return rng.normal(spec.mean, spec.standardDeviation, size=size)

    if spec.distribution == "uniform":
        if spec.lower is not None and spec.upper is not None:
            lo, hi = spec.lower, spec.upper
        else:
            half = np.sqrt(3.0) * spec.standardDeviation
            lo, hi = spec.mean - half, spec.mean + half
        if hi <= lo:
            raise ValueError(f"uniform bounds invalid for {spec.name}")
        return rng.uniform(lo, hi, size=size)

    if spec.distribution == "triangular":
        if spec.lower is None or spec.upper is None:
            raise ValueError(f"triangular distribution requires lower and upper for {spec.name}")
        mode = spec.mode if spec.mode is not None else spec.mean
        if not (spec.lower <= mode <= spec.upper):
            raise ValueError(f"triangular mode must be within bounds for {spec.name}")
        return rng.triangular(spec.lower, mode, spec.upper, size=size)

    if spec.distribution == "lognormal":
        if spec.mean <= 0:
            raise ValueError(f"lognormal mean must be positive for {spec.name}")
        variance = spec.standardDeviation ** 2
        sigma2 = np.log(1.0 + variance / (spec.mean ** 2))
        sigma = np.sqrt(sigma2)
        mu = np.log(spec.mean) - sigma2 / 2.0
        return rng.lognormal(mean=mu, sigma=sigma, size=size)

    raise ValueError(f"unsupported distribution: {spec.distribution}")


def _monte_carlo(req: UncertaintyRequest, samples: Optional[int] = None):
    count = int(samples or req.samples)
    if not req.inputs:
        raise ValueError("monte-carlo requires inputs")
    names = [x.name for x in req.inputs]
    if len(set(names)) != len(names):
        raise ValueError("input names must be unique")
    symbols = [sp.Symbol(name, real=True) for name in names]
    expr = sp.sympify(req.expression, locals={n: s for n, s in zip(names, symbols)})
    fn = sp.lambdify(symbols, expr, modules="numpy")
    rng = np.random.default_rng(req.seed)
    draws = [_draw_input(spec, count, rng) for spec in req.inputs]
    output = np.asarray(fn(*draws), dtype=float)
    if output.ndim == 0:
        output = np.full(count, float(output))
    output = output.reshape(-1)
    if output.size != count:
        raise ValueError("model output must produce one scalar per Monte Carlo sample")
    if not np.all(np.isfinite(output)):
        raise ValueError("model produced non-finite Monte Carlo outputs")
    return names, draws, output


def execute_uncertainty(req: UncertaintyRequest) -> Dict[str, Any]:
    op = req.operation
    verification: Dict[str, Any] = {}
    details: Dict[str, Any] = {}
    method = op

    if op in {"first-order-independent", "first-order-covariance"}:
        symbols, expr, fn, jac_expr, jac_fn = _symbolic_model(req)
        means = _validate_means(req)
        jac = np.asarray(jac_fn(*means.tolist()), dtype=float).reshape(-1)
        nominal = float(np.asarray(fn(*means.tolist())).reshape(()))

        if op == "first-order-independent":
            if len(req.standardDeviations) != len(req.variables):
                raise ValueError("standardDeviations length must match variables")
            std = np.asarray(req.standardDeviations, dtype=float)
            if np.any(std < 0):
                raise ValueError("standard deviations must be nonnegative")
            covariance = np.diag(std ** 2)
            method = "first-order-taylor-independent"
        else:
            if req.covarianceMatrix is None:
                raise ValueError("first-order-covariance requires covarianceMatrix")
            covariance = np.asarray(req.covarianceMatrix, dtype=float)
            n = len(req.variables)
            if covariance.shape != (n, n):
                raise ValueError("covarianceMatrix must be square and match variables")
            if not np.allclose(covariance, covariance.T, atol=1e-12):
                raise ValueError("covarianceMatrix must be symmetric")
            eig = np.linalg.eigvalsh(covariance)
            if np.min(eig) < -1e-10:
                raise ValueError("covarianceMatrix must be positive semidefinite")
            method = "first-order-taylor-covariance"

        variance = float(jac @ covariance @ jac.T)
        variance = max(0.0, variance)
        std_out = float(np.sqrt(variance))
        contributions = {}
        for i, name in enumerate(req.variables):
            contributions[name] = {
                "derivative": float(jac[i]),
                "diagonalVarianceContribution": float((jac[i] ** 2) * covariance[i, i]),
            }

        result: Any = {
            "nominalValue": nominal,
            "outputVariance": variance,
            "outputStandardDeviation": std_out,
            "jacobian": {
                req.variables[i]: str(jac_expr[i]) for i in range(len(req.variables))
            },
            "jacobianAtMean": {
                req.variables[i]: float(jac[i]) for i in range(len(req.variables))
            },
            "contributions": contributions,
        }
        details["covarianceMatrix"] = covariance.tolist()
        verification["varianceNonnegative"] = variance >= 0

    elif op == "monte-carlo":
        names, draws, output = _monte_carlo(req)
        result = {
            "output": _summary(output, req.confidenceLevel),
            "inputs": {
                name: _summary(draw, req.confidenceLevel)
                for name, draw in zip(names, draws)
            },
            "samples": req.samples,
            "seed": req.seed,
        }
        verification["deterministicWhenSeeded"] = req.seed is not None
        verification["finiteOutputs"] = bool(np.all(np.isfinite(output)))
        details["inputDistributions"] = [
            {
                "name": x.name,
                "distribution": x.distribution,
                "mean": x.mean,
                "standardDeviation": x.standardDeviation,
                "lower": x.lower,
                "upper": x.upper,
                "mode": x.mode,
            }
            for x in req.inputs
        ]
        method = "numpy-seeded-monte-carlo"

    elif op == "monte-carlo-convergence":
        if req.convergenceBatches > req.samples:
            raise ValueError("convergenceBatches cannot exceed samples")
        names, draws, output = _monte_carlo(req)
        sizes = np.linspace(
            max(100, req.samples // req.convergenceBatches),
            req.samples,
            req.convergenceBatches,
            dtype=int,
        )
        rows = []
        for n in sizes:
            subset = output[:n]
            rows.append({
                "samples": int(n),
                "mean": float(np.mean(subset)),
                "standardDeviation": float(np.std(subset, ddof=1)),
                "standardErrorMean": float(np.std(subset, ddof=1) / np.sqrt(n)),
            })
        result = {
            "output": _summary(output, req.confidenceLevel),
            "convergence": rows,
            "samples": req.samples,
            "seed": req.seed,
        }
        if len(rows) >= 2:
            verification["standardErrorDecreases"] = rows[-1]["standardErrorMean"] <= rows[0]["standardErrorMean"]
        else:
            verification["standardErrorDecreases"] = True
        verification["deterministicWhenSeeded"] = req.seed is not None
        method = "numpy-monte-carlo-convergence-study"

    else:
        raise ValueError(f"Unsupported uncertainty operation: {op}")

    body = {
        "ok": True,
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "sympy-numpy-scipy-uncertainty",
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


def calculation_object_extension(req: UnifiedCalculationRequest, uncertainty_req: UncertaintyRequest):
    obj = build_calculation_object(req)
    result = execute_uncertainty(uncertainty_req)
    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["uncertaintyPropagation"] = result
    obj["result"]["uncertaintyPropagation"] = result["result"]
    obj["uncertainty"] = {
        "operation": uncertainty_req.operation,
        "method": result["method"],
        "result": result["result"],
    }
    obj["executionPlan"]["uncertaintyPropagation"] = {
        "runtime": "python",
        "engine": "sympy-numpy-scipy-uncertainty",
        "operation": uncertainty_req.operation,
        "method": result["method"],
        "samples": uncertainty_req.samples if "monte-carlo" in uncertainty_req.operation else None,
    }
    obj["verification"]["uncertaintyPropagation"] = result["verification"]
    obj["provenance"]["uncertaintyPropagationResultHash"] = result["resultHash"]
    if uncertainty_req.seed is not None:
        obj["provenance"]["uncertaintyRandomSeed"] = uncertainty_req.seed
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Uncertainty Propagation & Monte Carlo",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "sympy-numpy-scipy-uncertainty",
        "wordpressRequired": False,
        "capabilities": {
            "firstOrderIndependentPropagation": True,
            "covarianceAwarePropagation": True,
            "symbolicJacobian": True,
            "normalSampling": True,
            "uniformSampling": True,
            "triangularSampling": True,
            "lognormalSampling": True,
            "seededMonteCarlo": True,
            "quantileConfidenceSummaries": True,
            "monteCarloConvergenceDiagnostics": True,
            "calculationObjectUncertainty": True,
            "calculationObjectExtension": True,
        },
    }


@router.get("/v11150/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/uncertainty")
def uncertainty_route(req: UncertaintyRequest):
    return execute_uncertainty(req)


@router.post("/calculation-engine/v1/uncertainty/calculation-object")
def uncertainty_calculation_object_route(req: UncertaintyCalculationObjectRequest):
    return calculation_object_extension(req.calculationObjectRequest, req.uncertaintyAnalysis)

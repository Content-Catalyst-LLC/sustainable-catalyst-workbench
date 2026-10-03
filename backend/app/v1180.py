"""Workbench v11.8.0 — Probability & Statistics Engine.

Adds distribution computation, descriptive statistics, moments, confidence
intervals, hypothesis tests, correlation/covariance, regression diagnostics,
and deterministic random sampling to the unified CalculationObject.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field
from scipy import stats

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-probability-statistics-status/1.0"
STATISTICS_SCHEMA = "sc-workbench-probability-statistics-result/1.0"

router = APIRouter(tags=["workbench-v1180-probability-statistics-engine"])

DistributionName = Literal[
    "normal", "student-t", "chi-square", "f", "exponential", "uniform",
    "beta", "gamma", "lognormal", "binomial", "poisson",
]


class ProbabilityStatisticsRequest(BaseModel):
    operation: Literal[
        "describe",
        "moments",
        "distribution-pdf",
        "distribution-pmf",
        "distribution-cdf",
        "distribution-sf",
        "distribution-quantile",
        "random-sample",
        "confidence-interval-mean",
        "one-sample-t-test",
        "two-sample-t-test",
        "paired-t-test",
        "pearson-correlation",
        "spearman-correlation",
        "covariance",
        "linear-regression",
    ]
    data: List[float] = Field(default_factory=list, max_length=100000)
    dataB: List[float] = Field(default_factory=list, max_length=100000)
    distribution: Optional[DistributionName] = None
    parameters: Dict[str, float] = Field(default_factory=dict)
    x: Optional[float] = None
    probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    sampleSize: int = Field(default=1, ge=1, le=100000)
    seed: Optional[int] = None
    confidenceLevel: float = Field(default=0.95, gt=0.0, lt=1.0)
    hypothesizedMean: float = 0.0
    equalVariance: bool = False


class StatisticsCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    statistics: ProbabilityStatisticsRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _array(values: List[float], name: str = "data") -> np.ndarray:
    if not values:
        raise ValueError(f"{name} is required")
    arr = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must contain only finite numbers")
    return arr


def _distribution(req: ProbabilityStatisticsRequest):
    if req.distribution is None:
        raise ValueError("distribution is required")
    p = req.parameters
    name = req.distribution
    if name == "normal":
        return stats.norm(loc=p.get("loc", 0.0), scale=p.get("scale", 1.0)), "continuous"
    if name == "student-t":
        return stats.t(df=p.get("df", 1.0), loc=p.get("loc", 0.0), scale=p.get("scale", 1.0)), "continuous"
    if name == "chi-square":
        return stats.chi2(df=p.get("df", 1.0), loc=p.get("loc", 0.0), scale=p.get("scale", 1.0)), "continuous"
    if name == "f":
        return stats.f(dfn=p.get("dfn", 1.0), dfd=p.get("dfd", 1.0), loc=p.get("loc", 0.0), scale=p.get("scale", 1.0)), "continuous"
    if name == "exponential":
        return stats.expon(loc=p.get("loc", 0.0), scale=p.get("scale", 1.0)), "continuous"
    if name == "uniform":
        return stats.uniform(loc=p.get("loc", 0.0), scale=p.get("scale", 1.0)), "continuous"
    if name == "beta":
        return stats.beta(a=p.get("a", 1.0), b=p.get("b", 1.0), loc=p.get("loc", 0.0), scale=p.get("scale", 1.0)), "continuous"
    if name == "gamma":
        return stats.gamma(a=p.get("a", 1.0), loc=p.get("loc", 0.0), scale=p.get("scale", 1.0)), "continuous"
    if name == "lognormal":
        return stats.lognorm(s=p.get("s", 1.0), loc=p.get("loc", 0.0), scale=p.get("scale", 1.0)), "continuous"
    if name == "binomial":
        return stats.binom(n=int(p.get("n", 1)), p=p.get("p", 0.5), loc=int(p.get("loc", 0))), "discrete"
    if name == "poisson":
        return stats.poisson(mu=p.get("mu", 1.0), loc=int(p.get("loc", 0))), "discrete"
    raise ValueError(f"Unsupported distribution: {name}")


def execute_statistics(req: ProbabilityStatisticsRequest) -> Dict[str, Any]:
    op = req.operation
    details: Dict[str, Any] = {}
    verification: Dict[str, Any] = {}
    method = op

    if op == "describe":
        a = _array(req.data)
        result: Any = {
            "count": int(a.size),
            "mean": float(np.mean(a)),
            "median": float(np.median(a)),
            "varianceSample": float(np.var(a, ddof=1)) if a.size > 1 else 0.0,
            "standardDeviationSample": float(np.std(a, ddof=1)) if a.size > 1 else 0.0,
            "minimum": float(np.min(a)),
            "maximum": float(np.max(a)),
            "q1": float(np.quantile(a, 0.25)),
            "q3": float(np.quantile(a, 0.75)),
            "iqr": float(np.quantile(a, 0.75) - np.quantile(a, 0.25)),
        }
        details["ddof"] = 1

    elif op == "moments":
        a = _array(req.data)
        result = {
            "mean": float(np.mean(a)),
            "variancePopulation": float(np.var(a, ddof=0)),
            "skewness": float(stats.skew(a, bias=False)) if a.size >= 3 else 0.0,
            "excessKurtosis": float(stats.kurtosis(a, fisher=True, bias=False)) if a.size >= 4 else 0.0,
        }
        details["skewnessBiasCorrected"] = True
        details["kurtosisDefinition"] = "Fisher excess kurtosis"

    elif op in {
        "distribution-pdf", "distribution-pmf", "distribution-cdf",
        "distribution-sf", "distribution-quantile",
    }:
        dist, kind = _distribution(req)
        details["distribution"] = req.distribution
        details["parameters"] = req.parameters
        details["kind"] = kind

        if op == "distribution-quantile":
            if req.probability is None:
                raise ValueError("distribution-quantile requires probability")
            result = float(dist.ppf(req.probability))
            details["probability"] = req.probability
        else:
            if req.x is None:
                raise ValueError(f"{op} requires x")
            if op == "distribution-pdf":
                if kind != "continuous":
                    raise ValueError("distribution-pdf requires a continuous distribution")
                result = float(dist.pdf(req.x))
            elif op == "distribution-pmf":
                if kind != "discrete":
                    raise ValueError("distribution-pmf requires a discrete distribution")
                result = float(dist.pmf(req.x))
            elif op == "distribution-cdf":
                result = float(dist.cdf(req.x))
            else:
                result = float(dist.sf(req.x))
            details["x"] = req.x

    elif op == "random-sample":
        dist, kind = _distribution(req)
        rng = np.random.default_rng(req.seed)
        sample = dist.rvs(size=req.sampleSize, random_state=rng)
        result = np.asarray(sample).tolist()
        details.update({
            "distribution": req.distribution,
            "parameters": req.parameters,
            "sampleSize": req.sampleSize,
            "seed": req.seed,
            "kind": kind,
        })
        verification["deterministicWhenSeeded"] = req.seed is not None

    elif op == "confidence-interval-mean":
        a = _array(req.data)
        if a.size < 2:
            raise ValueError("confidence-interval-mean requires at least 2 values")
        mean = float(np.mean(a))
        sem = float(stats.sem(a))
        alpha = 1.0 - req.confidenceLevel
        critical = float(stats.t.ppf(1.0 - alpha / 2.0, df=a.size - 1))
        margin = critical * sem
        result = {
            "mean": mean,
            "lower": mean - margin,
            "upper": mean + margin,
            "confidenceLevel": req.confidenceLevel,
            "standardError": sem,
            "degreesOfFreedom": int(a.size - 1),
        }
        method = "student-t-confidence-interval"

    elif op == "one-sample-t-test":
        a = _array(req.data)
        test = stats.ttest_1samp(a, popmean=req.hypothesizedMean)
        result = {
            "statistic": float(test.statistic),
            "pValueTwoSided": float(test.pvalue),
            "degreesOfFreedom": float(test.df),
            "hypothesizedMean": req.hypothesizedMean,
        }
        method = "scipy-ttest-1samp"

    elif op == "two-sample-t-test":
        a = _array(req.data)
        b = _array(req.dataB, "dataB")
        test = stats.ttest_ind(a, b, equal_var=req.equalVariance)
        result = {
            "statistic": float(test.statistic),
            "pValueTwoSided": float(test.pvalue),
            "degreesOfFreedom": float(test.df),
            "equalVariance": req.equalVariance,
        }
        method = "scipy-ttest-ind"

    elif op == "paired-t-test":
        a = _array(req.data)
        b = _array(req.dataB, "dataB")
        if a.size != b.size:
            raise ValueError("paired-t-test requires equal-length samples")
        test = stats.ttest_rel(a, b)
        result = {
            "statistic": float(test.statistic),
            "pValueTwoSided": float(test.pvalue),
            "degreesOfFreedom": float(test.df),
        }
        method = "scipy-ttest-rel"

    elif op == "pearson-correlation":
        a = _array(req.data)
        b = _array(req.dataB, "dataB")
        if a.size != b.size:
            raise ValueError("pearson-correlation requires equal-length samples")
        test = stats.pearsonr(a, b)
        result = {
            "correlation": float(test.statistic),
            "pValueTwoSided": float(test.pvalue),
            "count": int(a.size),
        }
        method = "scipy-pearsonr"

    elif op == "spearman-correlation":
        a = _array(req.data)
        b = _array(req.dataB, "dataB")
        if a.size != b.size:
            raise ValueError("spearman-correlation requires equal-length samples")
        test = stats.spearmanr(a, b)
        result = {
            "correlation": float(test.statistic),
            "pValueTwoSided": float(test.pvalue),
            "count": int(a.size),
        }
        method = "scipy-spearmanr"

    elif op == "covariance":
        a = _array(req.data)
        b = _array(req.dataB, "dataB")
        if a.size != b.size:
            raise ValueError("covariance requires equal-length samples")
        matrix = np.cov(a, b, ddof=1)
        result = {
            "covarianceSample": float(matrix[0, 1]),
            "covarianceMatrix": matrix.tolist(),
            "count": int(a.size),
        }
        details["ddof"] = 1

    elif op == "linear-regression":
        x = _array(req.data)
        y = _array(req.dataB, "dataB")
        if x.size != y.size:
            raise ValueError("linear-regression requires equal-length samples")
        fit = stats.linregress(x, y)
        predictions = fit.intercept + fit.slope * x
        residuals = y - predictions
        result = {
            "slope": float(fit.slope),
            "intercept": float(fit.intercept),
            "rValue": float(fit.rvalue),
            "rSquared": float(fit.rvalue ** 2),
            "pValueSlope": float(fit.pvalue),
            "standardErrorSlope": float(fit.stderr),
            "standardErrorIntercept": float(fit.intercept_stderr),
            "count": int(x.size),
        }
        verification = {
            "residualMean": float(np.mean(residuals)),
            "sumSquaredResiduals": float(np.sum(residuals ** 2)),
        }
        method = "scipy-linregress"

    else:
        raise ValueError(f"Unsupported statistics operation: {op}")

    body = {
        "ok": True,
        "schema": STATISTICS_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "scipy-numpy",
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
    statistics_req: ProbabilityStatisticsRequest,
):
    obj = build_calculation_object(req)
    result = execute_statistics(statistics_req)

    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["probabilityStatistics"] = result
    obj["result"]["probabilityStatistics"] = result["result"]
    obj["executionPlan"]["probabilityStatistics"] = {
        "runtime": "python",
        "engine": "scipy-numpy",
        "operation": statistics_req.operation,
        "method": result["method"],
    }
    obj["verification"]["probabilityStatistics"] = result["verification"]
    obj["provenance"]["probabilityStatisticsResultHash"] = result["resultHash"]
    if statistics_req.seed is not None:
        obj["provenance"]["randomSeed"] = statistics_req.seed
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Probability & Statistics Engine",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "scipy-numpy",
        "wordpressRequired": False,
        "capabilities": {
            "descriptiveStatistics": True,
            "moments": True,
            "continuousDistributions": True,
            "discreteDistributions": True,
            "pdfPmfCdfSurvivalQuantiles": True,
            "deterministicRandomSampling": True,
            "confidenceIntervals": True,
            "oneSampleTTest": True,
            "twoSampleTTest": True,
            "pairedTTest": True,
            "pearsonCorrelation": True,
            "spearmanCorrelation": True,
            "covariance": True,
            "linearRegression": True,
            "calculationObjectExtension": True,
        },
        "distributions": [
            "normal", "student-t", "chi-square", "f", "exponential", "uniform",
            "beta", "gamma", "lognormal", "binomial", "poisson",
        ],
    }


@router.get("/v1180/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/statistics")
def statistics_route(req: ProbabilityStatisticsRequest):
    return execute_statistics(req)


@router.post("/calculation-engine/v1/statistics/calculation-object")
def statistics_calculation_object_route(req: StatisticsCalculationObjectRequest):
    return calculation_object_extension(
        req.calculationObjectRequest,
        req.statistics,
    )

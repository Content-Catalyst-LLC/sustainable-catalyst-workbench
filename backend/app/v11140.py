"""Workbench v11.14.0 — Complex Analysis & Special Functions.

Adds exact complex-variable decomposition, residues, series, poles/zeros,
high-precision special functions, and circular contour integration to the
unified v11 CalculationObject.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
import math

import mpmath as mp
import sympy as sp
from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-complex-analysis-special-functions-status/1.0"
RESULT_SCHEMA = "sc-workbench-complex-analysis-special-functions-result/1.0"

router = APIRouter(tags=["workbench-v11140-complex-analysis-special-functions"])


class ComplexAnalysisRequest(BaseModel):
    operation: Literal[
        "complex-evaluate",
        "decompose",
        "polar-form",
        "complex-roots",
        "residue",
        "laurent-series",
        "zeros-poles",
        "special-function",
        "contour-integral-circle",
    ]
    expression: Optional[str] = Field(default=None, max_length=20000)
    variable: str = Field(default="z", max_length=100)
    valueReal: Optional[float] = None
    valueImag: Optional[float] = None
    centerReal: float = 0.0
    centerImag: float = 0.0
    radius: float = Field(default=1.0, gt=0)
    order: int = Field(default=8, ge=1, le=100)
    rootDegree: Optional[int] = Field(default=None, ge=1, le=1000)
    specialFunction: Optional[Literal[
        "gamma","loggamma","beta","zeta","digamma","polygamma",
        "besselj","bessely","besseli","besselk","airyai","airybi",
        "erf","erfc","ei"
    ]] = None
    parameterA: Optional[float] = None
    parameterB: Optional[float] = None
    precisionDigits: int = Field(default=50, ge=15, le=2000)


class ComplexCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    complexAnalysis: ComplexAnalysisRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _sympy_setup(req: ComplexAnalysisRequest):
    z = sp.Symbol(req.variable)
    if not req.expression:
        raise ValueError(f"{req.operation} requires expression")
    expr = sp.sympify(req.expression, locals={req.variable: z, "I": sp.I, "pi": sp.pi})
    return z, expr


def _complex_payload(value, digits=30):
    c = complex(value)
    return {
        "real": float(c.real),
        "imag": float(c.imag),
        "magnitude": float(abs(c)),
        "argumentRadians": float(math.atan2(c.imag, c.real)),
        "text": mp.nstr(value, n=digits),
    }


def _mp_complex(req: ComplexAnalysisRequest):
    return mp.mpc(req.valueReal or 0.0, req.valueImag or 0.0)


def _special(req: ComplexAnalysisRequest):
    if req.specialFunction is None:
        raise ValueError("special-function requires specialFunction")
    z = _mp_complex(req)
    f = req.specialFunction
    a, b = req.parameterA, req.parameterB
    if f == "gamma":
        return mp.gamma(z)
    if f == "loggamma":
        return mp.loggamma(z)
    if f == "beta":
        if a is None:
            raise ValueError("beta requires parameterA")
        return mp.beta(z, a)
    if f == "zeta":
        return mp.zeta(z)
    if f == "digamma":
        return mp.digamma(z)
    if f == "polygamma":
        if a is None:
            raise ValueError("polygamma requires parameterA as derivative order")
        return mp.polygamma(int(a), z)
    if f == "besselj":
        if a is None:
            raise ValueError("besselj requires parameterA as order")
        return mp.besselj(a, z)
    if f == "bessely":
        if a is None:
            raise ValueError("bessely requires parameterA as order")
        return mp.bessely(a, z)
    if f == "besseli":
        if a is None:
            raise ValueError("besseli requires parameterA as order")
        return mp.besseli(a, z)
    if f == "besselk":
        if a is None:
            raise ValueError("besselk requires parameterA as order")
        return mp.besselk(a, z)
    if f == "airyai":
        return mp.airyai(z)
    if f == "airybi":
        return mp.airybi(z)
    if f == "erf":
        return mp.erf(z)
    if f == "erfc":
        return mp.erfc(z)
    if f == "ei":
        return mp.ei(z)
    raise ValueError(f"unsupported specialFunction: {f}")


def execute_complex_analysis(req: ComplexAnalysisRequest) -> Dict[str, Any]:
    op = req.operation
    verification: Dict[str, Any] = {}
    details: Dict[str, Any] = {}
    method = op

    if op == "complex-evaluate":
        z, expr = _sympy_setup(req)
        point = sp.Float(req.valueReal or 0.0) + sp.I*sp.Float(req.valueImag or 0.0)
        val = sp.N(expr.subs(z, point), req.precisionDigits)
        result: Any = {
            "exactExpression": str(expr),
            "value": {
                "real": float(sp.re(val)),
                "imag": float(sp.im(val)),
                "text": str(val),
            },
        }
        method = "sympy-complex-substitution"

    elif op == "decompose":
        _, expr = _sympy_setup(req)
        expanded = sp.expand_complex(expr)
        result = {
            "expanded": str(expanded),
            "realPart": str(sp.re(expanded)),
            "imaginaryPart": str(sp.im(expanded)),
            "conjugate": str(sp.conjugate(expr)),
        }
        method = "sympy-complex-decomposition"

    elif op == "polar-form":
        zval = complex(req.valueReal or 0.0, req.valueImag or 0.0)
        mag = abs(zval)
        arg = math.atan2(zval.imag, zval.real)
        result = {
            "magnitude": mag,
            "argumentRadians": arg,
            "argumentDegrees": math.degrees(arg),
            "polarText": f"{mag} * exp(i*{arg})",
        }
        verification["reconstructionError"] = abs(zval - mag*complex(math.cos(arg), math.sin(arg)))

    elif op == "complex-roots":
        degree = req.rootDegree
        if degree is None:
            raise ValueError("complex-roots requires rootDegree")
        zval = complex(req.valueReal or 0.0, req.valueImag or 0.0)
        if zval == 0:
            roots = [0j] * degree
        else:
            r = abs(zval) ** (1.0/degree)
            theta = math.atan2(zval.imag, zval.real)
            roots = [
                r * complex(math.cos((theta+2*math.pi*k)/degree),
                            math.sin((theta+2*math.pi*k)/degree))
                for k in range(degree)
            ]
        result = {"degree": degree, "roots": [_complex_payload(x, 25) for x in roots]}
        verification["allRootsReconstruct"] = all(abs((x**degree)-zval) < 1e-8 for x in roots)
        method = "de-moivre-roots"

    elif op == "residue":
        z, expr = _sympy_setup(req)
        point = sp.nsimplify(req.centerReal) + sp.I*sp.nsimplify(req.centerImag)
        res = sp.residue(expr, z, point)
        result = {
            "point": str(point),
            "residueExact": str(res),
            "residueApproximate": str(sp.N(res, min(req.precisionDigits, 100))),
        }
        method = "sympy-residue"

    elif op == "laurent-series":
        z, expr = _sympy_setup(req)
        point = sp.nsimplify(req.centerReal) + sp.I*sp.nsimplify(req.centerImag)
        series = sp.series(expr, z, point, req.order)
        result = {"center": str(point), "series": str(series)}
        method = "sympy-series-laurent-capable"

    elif op == "zeros-poles":
        z, expr = _sympy_setup(req)
        numer, denom = sp.together(expr).as_numer_denom()
        zeros = sp.solve(sp.Eq(numer, 0), z)
        poles = sp.solve(sp.Eq(denom, 0), z)
        result = {
            "zeros": [str(v) for v in zeros],
            "poles": [str(v) for v in poles],
        }
        verification["zeroCount"] = len(zeros)
        verification["poleCount"] = len(poles)
        method = "sympy-rational-zero-pole-analysis"

    elif op == "special-function":
        with mp.workdps(req.precisionDigits):
            val = _special(req)
            result = {
                "function": req.specialFunction,
                "input": _complex_payload(_mp_complex(req), min(req.precisionDigits, 80)),
                "value": _complex_payload(val, min(req.precisionDigits, 200)),
                "precisionDigits": req.precisionDigits,
            }
        details["branchConvention"] = "mpmath principal branch where applicable"
        method = "mpmath-special-function"

    elif op == "contour-integral-circle":
        z, expr = _sympy_setup(req)
        center = mp.mpc(req.centerReal, req.centerImag)
        radius = req.radius
        with mp.workdps(req.precisionDigits):
            fn = sp.lambdify(z, expr, modules="mpmath")
            integrand = lambda t: fn(center + radius*mp.e**(1j*t)) * (1j*radius*mp.e**(1j*t))
            val = mp.quad(integrand, [0, 2*mp.pi])
            result = {
                "center": _complex_payload(center, 30),
                "radius": radius,
                "integral": _complex_payload(val, min(req.precisionDigits, 200)),
                "precisionDigits": req.precisionDigits,
            }
        method = "mpmath-circular-contour-quadrature"
        details["parameterization"] = "z(t)=center+radius*exp(i*t), t in [0,2*pi]"

    else:
        raise ValueError(f"Unsupported complex analysis operation: {op}")

    body = {
        "ok": True,
        "schema": RESULT_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "sympy-mpmath-complex",
        "runtime": "python",
        "method": method,
        "result": result,
        "details": details,
        "verification": verification,
        "wordpressRequired": False,
    }
    body["resultHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok","resultHash"}}
    )
    return body


def calculation_object_extension(req: UnifiedCalculationRequest, complex_req: ComplexAnalysisRequest):
    obj = build_calculation_object(req)
    result = execute_complex_analysis(complex_req)
    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["complexAnalysis"] = result
    obj["result"]["complexAnalysis"] = result["result"]
    obj["executionPlan"]["complexAnalysis"] = {
        "runtime": "python",
        "engine": "sympy-mpmath-complex",
        "operation": complex_req.operation,
        "method": result["method"],
        "precisionDigits": complex_req.precisionDigits,
    }
    obj["verification"]["complexAnalysis"] = result["verification"]
    obj["provenance"]["complexAnalysisResultHash"] = result["resultHash"]
    obj["provenance"]["complexPrecisionDigits"] = complex_req.precisionDigits
    obj["calculationObjectHash"] = _hash(
        {k:v for k,v in obj.items() if k not in {"ok","calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Complex Analysis & Special Functions",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "sympy-mpmath-complex",
        "wordpressRequired": False,
        "capabilities": {
            "complexEvaluation": True,
            "realImaginaryDecomposition": True,
            "polarForm": True,
            "complexRoots": True,
            "residues": True,
            "laurentSeries": True,
            "zeroPoleAnalysis": True,
            "highPrecisionSpecialFunctions": True,
            "circularContourIntegration": True,
            "branchMetadata": True,
            "calculationObjectExtension": True,
        },
        "specialFunctions": [
            "gamma","loggamma","beta","zeta","digamma","polygamma",
            "besselj","bessely","besseli","besselk","airyai","airybi",
            "erf","erfc","ei"
        ],
    }


@router.get("/v11140/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/complex-analysis")
def complex_analysis_route(req: ComplexAnalysisRequest):
    return execute_complex_analysis(req)


@router.post("/calculation-engine/v1/complex-analysis/calculation-object")
def complex_analysis_calculation_object_route(req: ComplexCalculationObjectRequest):
    return calculation_object_extension(req.calculationObjectRequest, req.complexAnalysis)

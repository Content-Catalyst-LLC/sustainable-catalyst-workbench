"""Workbench v11.2.0 — Advanced Calculus Engine.

Extends the unified CalculationObject with symbolic calculus capabilities:
higher-order derivatives, partial derivatives, exact/definite integrals,
limits, series, Taylor expansions, critical points, and extrema analysis.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import sympy as sp
from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-advanced-calculus-status/1.0"
CALCULUS_SCHEMA = "sc-workbench-calculus-result/1.0"

router = APIRouter(tags=["workbench-v1120-advanced-calculus-engine"])


class CalculusRequest(BaseModel):
    expression: str = Field(max_length=20000)
    operation: Literal[
        "differentiate",
        "partial-derivative",
        "integrate",
        "definite-integral",
        "limit",
        "series",
        "taylor",
        "critical-points",
        "extrema",
    ]
    variable: str = Field(default="x", max_length=200)
    variables: List[str] = Field(default_factory=list, max_length=20)
    orders: Dict[str, int] = Field(default_factory=dict)
    order: int = Field(default=1, ge=1, le=50)
    lower: Optional[Any] = None
    upper: Optional[Any] = None
    point: Optional[Any] = None
    direction: Literal["+", "-", "+-"] = "+-"
    seriesOrder: int = Field(default=6, ge=1, le=100)
    expansionPoint: Any = 0
    assumptions: Dict[str, List[str]] = Field(default_factory=dict)
    domain: Literal["real", "complex"] = "real"


class CalculusCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    calculus: CalculusRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _symbols(req: CalculusRequest) -> Dict[str, sp.Symbol]:
    names = set(req.variables)
    names.add(req.variable)
    names.update(req.orders.keys())
    names.update(req.assumptions.keys())
    table: Dict[str, sp.Symbol] = {}

    supported = {
        "real", "positive", "negative", "nonzero", "integer", "rational",
        "irrational", "finite", "nonnegative", "nonpositive",
    }
    for name in sorted(names):
        kwargs = {
            item: True
            for item in req.assumptions.get(name, [])
            if item in supported
        }
        table[name] = sp.Symbol(name, **kwargs)
    return table


def _parse(value: Any, symbols: Dict[str, sp.Symbol]) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return sp.sympify(value)
    return sp.sympify(str(value), locals=symbols)


def execute_calculus(req: CalculusRequest) -> Dict[str, Any]:
    symbols = _symbols(req)
    expr = _parse(req.expression, symbols)
    var = symbols.get(req.variable) or sp.Symbol(req.variable)
    op = req.operation
    details: Dict[str, Any] = {}

    if op == "differentiate":
        result = sp.diff(expr, var, req.order)
        details["order"] = req.order

    elif op == "partial-derivative":
        derivative_spec = []
        if req.orders:
            for name, order in req.orders.items():
                sym = symbols.get(name) or sp.Symbol(name)
                derivative_spec.extend([sym, int(order)])
            result = sp.diff(expr, *derivative_spec)
            details["orders"] = req.orders
        else:
            partial_vars = req.variables or [req.variable]
            result = expr
            for name in partial_vars:
                sym = symbols.get(name) or sp.Symbol(name)
                result = sp.diff(result, sym)
            details["variables"] = partial_vars

    elif op == "integrate":
        result = sp.integrate(expr, var)

    elif op == "definite-integral":
        if req.lower is None or req.upper is None:
            raise ValueError("definite-integral requires lower and upper")
        lower = _parse(req.lower, symbols)
        upper = _parse(req.upper, symbols)
        result = sp.integrate(expr, (var, lower, upper))
        details["bounds"] = [str(lower), str(upper)]

    elif op == "limit":
        if req.point is None:
            raise ValueError("limit requires point")
        point = _parse(req.point, symbols)
        dir_value = req.direction
        result = sp.limit(expr, var, point, dir=dir_value)
        details["point"] = str(point)
        details["direction"] = dir_value

    elif op == "series":
        point = _parse(req.expansionPoint, symbols)
        result = sp.series(expr, var, point, req.seriesOrder)
        details["expansionPoint"] = str(point)
        details["seriesOrder"] = req.seriesOrder

    elif op == "taylor":
        point = _parse(req.expansionPoint, symbols)
        result = sp.series(expr, var, point, req.seriesOrder).removeO()
        details["expansionPoint"] = str(point)
        details["seriesOrder"] = req.seriesOrder

    elif op == "critical-points":
        derivative = sp.diff(expr, var)
        points = sp.solve(sp.Eq(derivative, 0), var)
        result = [str(v) for v in points]
        details["derivative"] = str(derivative)

    elif op == "extrema":
        derivative = sp.diff(expr, var)
        second = sp.diff(expr, var, 2)
        points = sp.solve(sp.Eq(derivative, 0), var)
        extrema = []
        for point in points:
            second_value = sp.simplify(second.subs(var, point))
            value = sp.simplify(expr.subs(var, point))
            if second_value.is_positive:
                kind = "local-minimum"
            elif second_value.is_negative:
                kind = "local-maximum"
            else:
                kind = "undetermined"
            extrema.append({
                "point": str(point),
                "value": str(value),
                "secondDerivative": str(second_value),
                "classification": kind,
            })
        result = extrema
        details["firstDerivative"] = str(derivative)
        details["secondDerivative"] = str(second)

    else:
        raise ValueError(f"Unsupported calculus operation: {op}")

    result_value = str(result) if isinstance(result, sp.Basic) else result

    body = {
        "ok": True,
        "schema": CALCULUS_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "sympy",
        "exact": True,
        "input": {
            "expression": req.expression,
            "variable": req.variable,
            "variables": req.variables,
            "domain": req.domain,
            "assumptions": req.assumptions,
        },
        "result": result_value,
        "details": details,
        "wordpressRequired": False,
    }
    body["resultHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "resultHash"}}
    )
    return body


def calculation_object_extension(
    req: UnifiedCalculationRequest,
    calculus: CalculusRequest,
) -> Dict[str, Any]:
    obj = build_calculation_object(req)
    calculus_result = execute_calculus(calculus)

    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["calculus"] = calculus_result
    obj["result"]["calculus"] = calculus_result["result"]
    obj["executionPlan"]["calculus"] = {
        "engine": "sympy",
        "operation": calculus.operation,
        "exact": True,
    }
    obj["provenance"]["calculusResultHash"] = calculus_result["resultHash"]
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Advanced Calculus Engine",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "sympy",
        "wordpressRequired": False,
        "exactByDefault": True,
        "capabilities": {
            "higherOrderDerivatives": True,
            "partialDerivatives": True,
            "indefiniteIntegrals": True,
            "definiteIntegrals": True,
            "limits": True,
            "oneSidedLimits": True,
            "seriesExpansion": True,
            "taylorExpansion": True,
            "criticalPoints": True,
            "extremaClassification": True,
            "assumptionAwareSymbols": True,
            "calculationObjectExtension": True,
        },
    }


@router.get("/v1120/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/calculus")
def calculus_route(req: CalculusRequest):
    return execute_calculus(req)


@router.post("/calculation-engine/v1/calculus/calculation-object")
def calculus_calculation_object_route(req: CalculusCalculationObjectRequest):
    return calculation_object_extension(
        req.calculationObjectRequest,
        req.calculus,
    )

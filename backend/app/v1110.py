"""Workbench v11.1.0 — Advanced Symbolic Algebra.

Extends the unified CalculationObject with deeper exact algebra operations while
preserving the v11 calculation engine contract.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import sympy as sp
from fastapi import APIRouter
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import (
    UnifiedCalculationRequest,
    build_calculation_object,
    build_execution_plan,
    normalize_request,
)
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-advanced-symbolic-algebra-status/1.0"
ALGEBRA_SCHEMA = "sc-workbench-symbolic-algebra-result/1.0"
POLY_SCHEMA = "sc-workbench-symbolic-polynomial-result/1.0"
IDENTITY_SCHEMA = "sc-workbench-symbolic-identity-result/1.0"

router = APIRouter(tags=["workbench-v1110-advanced-symbolic-algebra"])


class SymbolicAlgebraRequest(BaseModel):
    expression: str = Field(max_length=20000)
    variable: Optional[str] = Field(default=None, max_length=200)
    variables: List[str] = Field(default_factory=list, max_length=50)
    operation: Literal[
        "expand",
        "factor",
        "cancel",
        "together",
        "apart",
        "collect",
        "substitute",
        "roots",
        "degree",
        "leading-coefficient",
        "coefficients",
        "identity-check",
        "solve-system",
    ]
    substitution: Dict[str, Any] = Field(default_factory=dict)
    collectBy: Optional[str] = Field(default=None, max_length=200)
    equations: List[str] = Field(default_factory=list, max_length=100)
    assumptions: Dict[str, List[str]] = Field(default_factory=dict)
    domain: Literal["complex", "real"] = "complex"


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _symbol_table(req: SymbolicAlgebraRequest) -> Dict[str, sp.Symbol]:
    names = set(req.variables)
    if req.variable:
        names.add(req.variable)
    for name in req.assumptions:
        names.add(name)

    table: Dict[str, sp.Symbol] = {}
    for name in sorted(names):
        kwargs: Dict[str, Any] = {}
        for assumption in req.assumptions.get(name, []):
            if assumption in {
                "real", "positive", "negative", "nonzero", "integer",
                "rational", "irrational", "finite", "nonnegative",
                "nonpositive", "even", "odd",
            }:
                kwargs[assumption] = True
        table[name] = sp.Symbol(name, **kwargs)
    return table


def _parse(expr: str, symbols: Dict[str, sp.Symbol]) -> sp.Expr:
    return sp.sympify(expr, locals=symbols)


def execute_symbolic_algebra(req: SymbolicAlgebraRequest) -> Dict[str, Any]:
    symbols = _symbol_table(req)

    result: Any
    details: Dict[str, Any] = {}
    op = req.operation

    # Equation-oriented operations may contain "=" and must not be passed
    # through generic sympify before their sides are separated.
    expr = None
    if op not in {"identity-check", "solve-system"}:
        expr = _parse(req.expression, symbols)

    if op == "expand":
        result = sp.expand(expr)
    elif op == "factor":
        result = sp.factor(expr)
    elif op == "cancel":
        result = sp.cancel(expr)
    elif op == "together":
        result = sp.together(expr)
    elif op == "apart":
        var = symbols.get(req.variable) if req.variable else None
        result = sp.apart(expr, var)
    elif op == "collect":
        target_name = req.collectBy or req.variable
        if not target_name:
            raise ValueError("collect requires collectBy or variable")
        target = symbols.get(target_name) or sp.Symbol(target_name)
        result = sp.collect(expr, target)
    elif op == "substitute":
        subs = {}
        for key, value in req.substitution.items():
            sym = symbols.get(key) or sp.Symbol(key)
            subs[sym] = sp.sympify(value, locals=symbols)
        result = sp.simplify(expr.subs(subs))
        details["substitution"] = {str(k): str(v) for k, v in subs.items()}
    elif op == "roots":
        var_name = req.variable or (req.variables[0] if req.variables else None)
        if not var_name:
            raise ValueError("roots requires variable")
        var = symbols.get(var_name) or sp.Symbol(var_name)
        roots = sp.roots(expr, var)
        result = {str(root): int(mult) for root, mult in roots.items()}
        details["rootCountWithMultiplicity"] = int(sum(roots.values()))
    elif op == "degree":
        var_name = req.variable or (req.variables[0] if req.variables else None)
        if not var_name:
            raise ValueError("degree requires variable")
        var = symbols.get(var_name) or sp.Symbol(var_name)
        result = int(sp.Poly(expr, var).degree())
    elif op == "leading-coefficient":
        var_name = req.variable or (req.variables[0] if req.variables else None)
        if not var_name:
            raise ValueError("leading-coefficient requires variable")
        var = symbols.get(var_name) or sp.Symbol(var_name)
        result = sp.Poly(expr, var).LC()
    elif op == "coefficients":
        var_name = req.variable or (req.variables[0] if req.variables else None)
        if not var_name:
            raise ValueError("coefficients requires variable")
        var = symbols.get(var_name) or sp.Symbol(var_name)
        poly = sp.Poly(expr, var)
        result = [str(v) for v in poly.all_coeffs()]
        details["degree"] = int(poly.degree())
    elif op == "identity-check":
        if "=" in req.expression:
            left, right = req.expression.split("=", 1)
            lhs = _parse(left, symbols)
            rhs = _parse(right, symbols)
            difference = sp.simplify(lhs - rhs)
        else:
            difference = sp.simplify(expr)
        result = bool(difference == 0)
        details["simplifiedDifference"] = str(difference)
    elif op == "solve-system":
        equations = req.equations or [req.expression]
        parsed = []
        for equation in equations:
            if "=" in equation:
                left, right = equation.split("=", 1)
                parsed.append(sp.Eq(_parse(left, symbols), _parse(right, symbols)))
            else:
                parsed.append(sp.Eq(_parse(equation, symbols), 0))
        solve_vars = [symbols.get(v) or sp.Symbol(v) for v in req.variables]
        if not solve_vars and req.variable:
            solve_vars = [symbols.get(req.variable) or sp.Symbol(req.variable)]
        result = sp.solve(parsed, solve_vars, dict=True)
        result = [{str(k): str(v) for k, v in item.items()} for item in result]
        details["equationCount"] = len(parsed)
        details["variableCount"] = len(solve_vars)
    else:
        raise ValueError(f"Unsupported symbolic operation: {op}")

    if isinstance(result, sp.Basic):
        result_value: Any = str(result)
    else:
        result_value = result

    body = {
        "ok": True,
        "schema": ALGEBRA_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "sympy",
        "input": {
            "expression": req.expression,
            "variable": req.variable,
            "variables": req.variables,
            "assumptions": req.assumptions,
            "domain": req.domain,
        },
        "result": result_value,
        "details": details,
        "wordpressRequired": False,
    }
    body["resultHash"] = _hash(
        {k: v for k, v in body.items() if k not in {"ok", "resultHash"}}
    )
    return body


def calculation_object_extension(req: UnifiedCalculationRequest, algebra: SymbolicAlgebraRequest) -> Dict[str, Any]:
    obj = build_calculation_object(req)
    algebra_result = execute_symbolic_algebra(algebra)

    obj["extensions"] = {
        "symbolicAlgebra": algebra_result
    }
    obj["result"]["symbolicAlgebra"] = algebra_result["result"]
    obj["executionPlan"]["symbolicAlgebra"] = {
        "engine": "sympy",
        "operation": algebra.operation,
        "exact": True,
    }
    obj["provenance"]["symbolicAlgebraResultHash"] = algebra_result["resultHash"]
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


class SymbolicCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    symbolicAlgebra: SymbolicAlgebraRequest


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Advanced Symbolic Algebra",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "engine": "sympy",
        "exactByDefault": True,
        "capabilities": {
            "expand": True,
            "factor": True,
            "cancelRationalExpressions": True,
            "combineRationalExpressions": True,
            "partialFractions": True,
            "collectTerms": True,
            "substitution": True,
            "polynomialRoots": True,
            "polynomialDegree": True,
            "leadingCoefficient": True,
            "polynomialCoefficients": True,
            "identityChecking": True,
            "symbolicSystems": True,
            "symbolAssumptions": True,
            "calculationObjectExtension": True,
        },
    }


@router.get("/v1110/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/symbolic/algebra")
def symbolic_algebra_route(req: SymbolicAlgebraRequest):
    return execute_symbolic_algebra(req)


@router.post("/calculation-engine/v1/symbolic/calculation-object")
def symbolic_calculation_object_route(req: SymbolicCalculationObjectRequest):
    return calculation_object_extension(
        req.calculationObjectRequest,
        req.symbolicAlgebra,
    )

"""Workbench v5.1.0 — Universal Mathematics & CAS Engine Foundation.

This module intentionally avoids Python eval/exec for user expressions. A restricted
Python-expression AST is converted to SymPy objects through an explicit allow-list.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from typing import Any, Dict, List, Literal, Optional

import sympy as sp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

VERSION = "5.1.0"
SCHEMA = "sc-workbench-math-object/1.0"
MAX_EXPRESSION_LENGTH = 2000
MAX_AST_NODES = 500
MAX_SYSTEM_EQUATIONS = 12
MAX_PRECISION = 100
MAX_DERIVATIVE_ORDER = 8
MAX_SERIES_ORDER = 50

router = APIRouter(prefix="/v510", tags=["workbench-v510-mathematics"])

ALLOWED_FUNCTIONS: Dict[str, Any] = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "exp": sp.exp, "log": sp.log, "ln": sp.log, "sqrt": sp.sqrt,
    "abs": sp.Abs, "Abs": sp.Abs, "sign": sp.sign,
    "floor": sp.floor, "ceil": sp.ceiling, "ceiling": sp.ceiling,
    "factorial": sp.factorial, "gamma": sp.gamma,
}
ALLOWED_CONSTANTS: Dict[str, Any] = {
    "pi": sp.pi, "E": sp.E, "e": sp.E, "I": sp.I, "oo": sp.oo,
}
ALLOWED_BINARY = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a ** b,
    ast.Mod: lambda a, b: sp.Mod(a, b),
}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def _normalize_expression(text: str) -> str:
    value = (text or "").strip().replace("^", "**").replace("−", "-").replace("×", "*").replace("÷", "/")
    if not value:
        raise ValueError("Expression is required.")
    if len(value) > MAX_EXPRESSION_LENGTH:
        raise ValueError(f"Expression exceeds {MAX_EXPRESSION_LENGTH} characters.")
    return value


class RestrictedSympyParser:
    def __init__(self, symbols: Optional[List[str]] = None):
        self.symbols: Dict[str, sp.Symbol] = {}
        for name in symbols or []:
            self.symbol(name)

    def symbol(self, name: str) -> sp.Symbol:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name or ""):
            raise ValueError(f"Invalid symbol name: {name!r}")
        if name in ALLOWED_FUNCTIONS:
            raise ValueError(f"Reserved function name cannot be used as a symbol: {name}")
        if name in ALLOWED_CONSTANTS:
            return ALLOWED_CONSTANTS[name]
        self.symbols.setdefault(name, sp.Symbol(name))
        return self.symbols[name]

    def parse(self, text: str) -> sp.Expr:
        normalized = _normalize_expression(text)
        try:
            tree = ast.parse(normalized, mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"Invalid mathematical expression: {exc.msg}") from exc
        if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
            raise ValueError(f"Expression exceeds the {MAX_AST_NODES}-node complexity limit.")
        return self._convert(tree.body)

    def equation(self, text: str) -> sp.Expr:
        normalized = _normalize_expression(text)
        # Single '=' is equation syntax. Python comparisons and assignment-like syntax are not accepted.
        if "=" in normalized:
            if any(token in normalized for token in ("==", "!=", ">=", "<=")):
                raise ValueError("Use a single '=' for equations; comparison operators are not supported in CAS expressions.")
            parts = normalized.split("=")
            if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
                raise ValueError("Equation must contain exactly one '=' with expressions on both sides.")
            return sp.Eq(self.parse(parts[0]), self.parse(parts[1]))
        return self.parse(normalized)

    def _convert(self, node: ast.AST) -> sp.Expr:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError("Only numeric constants are permitted.")
            if isinstance(node.value, int):
                return sp.Integer(node.value)
            return sp.Rational(str(node.value))
        if isinstance(node, ast.Name):
            if node.id in ALLOWED_CONSTANTS:
                return ALLOWED_CONSTANTS[node.id]
            return self.symbol(node.id)
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINARY:
            left = self._convert(node.left)
            right = self._convert(node.right)
            return ALLOWED_BINARY[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = self._convert(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCTIONS:
                raise ValueError("Function is not in the approved mathematics allow-list.")
            if node.keywords:
                raise ValueError("Keyword arguments are not supported in mathematical functions.")
            return ALLOWED_FUNCTIONS[node.func.id](*[self._convert(arg) for arg in node.args])
        raise ValueError(f"Unsupported expression construct: {type(node).__name__}")


class ParseInput(BaseModel):
    expression: str
    symbols: List[str] = Field(default_factory=list)
    precision: int = Field(default=15, ge=1, le=MAX_PRECISION)


class ComputeInput(ParseInput):
    operation: Literal["simplify", "expand", "factor", "evaluate"] = "simplify"


class CalculusInput(ParseInput):
    operation: Literal["differentiate", "integrate", "limit", "series"]
    variable: str = "x"
    order: int = Field(default=1, ge=1, le=MAX_DERIVATIVE_ORDER)
    lower: Optional[str] = None
    upper: Optional[str] = None
    point: str = "0"
    direction: Literal["+", "-", "+-"] = "+-"
    seriesOrder: int = Field(default=6, ge=1, le=MAX_SERIES_ORDER)


class SolveInput(BaseModel):
    equations: List[str] = Field(min_length=1, max_length=MAX_SYSTEM_EQUATIONS)
    variables: List[str] = Field(default_factory=list, max_length=MAX_SYSTEM_EQUATIONS)
    precision: int = Field(default=15, ge=1, le=MAX_PRECISION)


class SubstituteInput(ParseInput):
    substitutions: Dict[str, str] = Field(default_factory=dict)


def _numeric_text(value: Any, precision: int) -> str:
    try:
        return str(sp.N(value, precision))
    except Exception:
        return str(value)


def _math_object(source: str, value: Any, precision: int, operation: str = "parse") -> Dict[str, Any]:
    if isinstance(value, sp.Equality):
        free_symbols = sorted(str(symbol) for symbol in value.free_symbols)
        exact = str(value)
        latex = sp.latex(value)
        numeric = str(sp.Eq(sp.N(value.lhs, precision), sp.N(value.rhs, precision)))
        kind = "equation"
    else:
        free_symbols = sorted(str(symbol) for symbol in getattr(value, "free_symbols", set()))
        exact = str(value)
        latex = sp.latex(value)
        numeric = _numeric_text(value, precision)
        kind = "expression"
    record = {
        "schema": SCHEMA,
        "version": VERSION,
        "kind": kind,
        "operation": operation,
        "source": source,
        "exactText": exact,
        "decimalText": numeric,
        "latex": latex,
        "freeSymbols": free_symbols,
        "precision": precision,
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
    }
    record["mathObjectHash"] = content_hash(record)
    return record


def _serialize_solution(value: Any, precision: int) -> Any:
    if isinstance(value, dict):
        return {str(k): {"exact": str(v), "decimal": _numeric_text(v, precision), "latex": sp.latex(v)} for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_solution(item, precision) for item in value]
    if isinstance(value, sp.Basic):
        return {"exact": str(value), "decimal": _numeric_text(value, precision), "latex": sp.latex(value)}
    return value


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-mathematics-status/1.0",
        "version": VERSION,
        "engine": "SymPy",
        "engineVersion": sp.__version__,
        "parser": "restricted-ast",
        "capabilities": [
            "exact-arithmetic", "symbolic-expressions", "simplify", "expand", "factor",
            "numeric-evaluation", "equation-solving", "systems-of-equations", "differentiation",
            "indefinite-integration", "definite-integration", "limits", "series", "substitution",
            "latex-representation", "canonical-math-objects",
        ],
        "limits": {
            "maxExpressionLength": MAX_EXPRESSION_LENGTH,
            "maxAstNodes": MAX_AST_NODES,
            "maxSystemEquations": MAX_SYSTEM_EQUATIONS,
            "maxPrecision": MAX_PRECISION,
            "maxDerivativeOrder": MAX_DERIVATIVE_ORDER,
            "maxSeriesOrder": MAX_SERIES_ORDER,
        },
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
    }


def parse_math(payload: ParseInput) -> Dict[str, Any]:
    parser = RestrictedSympyParser(payload.symbols)
    value = parser.equation(payload.expression)
    return {"ok": True, "result": _math_object(payload.expression, value, payload.precision)}


def compute_math(payload: ComputeInput) -> Dict[str, Any]:
    parser = RestrictedSympyParser(payload.symbols)
    value = parser.parse(payload.expression)
    if payload.operation == "simplify":
        result = sp.simplify(value)
    elif payload.operation == "expand":
        result = sp.expand(value)
    elif payload.operation == "factor":
        result = sp.factor(value)
    else:
        result = sp.N(value, payload.precision)
    return {"ok": True, "result": _math_object(payload.expression, result, payload.precision, payload.operation)}


def calculus_math(payload: CalculusInput) -> Dict[str, Any]:
    parser = RestrictedSympyParser(payload.symbols + [payload.variable])
    expr = parser.parse(payload.expression)
    var = parser.symbol(payload.variable)
    if payload.operation == "differentiate":
        result = sp.diff(expr, var, payload.order)
    elif payload.operation == "integrate":
        if (payload.lower is None) ^ (payload.upper is None):
            raise ValueError("Definite integration requires both lower and upper bounds.")
        if payload.lower is not None and payload.upper is not None:
            result = sp.integrate(expr, (var, parser.parse(payload.lower), parser.parse(payload.upper)))
        else:
            result = sp.integrate(expr, var)
    elif payload.operation == "limit":
        point = parser.parse(payload.point)
        direction = payload.direction if payload.direction in {"+", "-"} else "+-"
        result = sp.limit(expr, var, point, dir=direction)
    else:
        point = parser.parse(payload.point)
        result = sp.series(expr, var, point, payload.seriesOrder)
    return {"ok": True, "result": _math_object(payload.expression, result, payload.precision, payload.operation)}


def solve_math(payload: SolveInput) -> Dict[str, Any]:
    parser = RestrictedSympyParser(payload.variables)
    equations = [parser.equation(text) for text in payload.equations]
    variables = [parser.symbol(name) for name in payload.variables] if payload.variables else sorted(
        set().union(*(eq.free_symbols for eq in equations)), key=lambda item: str(item)
    )
    if not variables:
        raise ValueError("At least one solve variable must be present or inferable.")
    result = sp.solve(equations, variables, dict=True)
    record = {
        "schema": "sc-workbench-math-solution/1.0",
        "version": VERSION,
        "equations": payload.equations,
        "variables": [str(v) for v in variables],
        "solutionCount": len(result),
        "solutions": _serialize_solution(result, payload.precision),
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
    }
    record["solutionHash"] = content_hash(record)
    return {"ok": True, "result": record}


def substitute_math(payload: SubstituteInput) -> Dict[str, Any]:
    parser = RestrictedSympyParser(payload.symbols + list(payload.substitutions))
    expr = parser.parse(payload.expression)
    substitutions = {parser.symbol(name): parser.parse(value) for name, value in payload.substitutions.items()}
    result = sp.simplify(expr.subs(substitutions))
    response = _math_object(payload.expression, result, payload.precision, "substitute")
    response["substitutions"] = {key: str(value) for key, value in payload.substitutions.items()}
    response["mathObjectHash"] = content_hash({k: v for k, v in response.items() if k != "mathObjectHash"})
    return {"ok": True, "result": response}


def _guard(callable_):
    try:
        return callable_()
    except (ValueError, TypeError, ZeroDivisionError, NotImplementedError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Mathematics engine could not complete the operation: {exc}") from exc


@router.get("/status")
def status() -> Dict[str, Any]:
    return status_record()


@router.post("/parse")
def parse_endpoint(payload: ParseInput) -> Dict[str, Any]:
    return _guard(lambda: parse_math(payload))


@router.post("/compute")
def compute_endpoint(payload: ComputeInput) -> Dict[str, Any]:
    return _guard(lambda: compute_math(payload))


@router.post("/calculus")
def calculus_endpoint(payload: CalculusInput) -> Dict[str, Any]:
    return _guard(lambda: calculus_math(payload))


@router.post("/solve")
def solve_endpoint(payload: SolveInput) -> Dict[str, Any]:
    return _guard(lambda: solve_math(payload))


@router.post("/substitute")
def substitute_endpoint(payload: SubstituteInput) -> Dict[str, Any]:
    return _guard(lambda: substitute_math(payload))

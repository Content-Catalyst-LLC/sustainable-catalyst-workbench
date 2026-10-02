"""Workbench v11.3.0 — Equation & Solver Laboratory.

Adds exact and numerical equation solving, nonlinear systems, inequalities,
root isolation, residual diagnostics, and solver verification to the unified
v11 CalculationObject architecture.
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
STATUS_SCHEMA = "sc-workbench-equation-solver-laboratory-status/1.0"
SOLVER_SCHEMA = "sc-workbench-equation-solver-result/1.0"

router = APIRouter(tags=["workbench-v1130-equation-solver-laboratory"])


class SolverRequest(BaseModel):
    operation: Literal[
        "solve-exact",
        "solve-numeric",
        "solve-system",
        "solve-inequality",
        "reduce-inequalities",
        "isolate-roots",
        "verify-solution",
    ]
    equation: Optional[str] = Field(default=None, max_length=20000)
    equations: List[str] = Field(default_factory=list, max_length=100)
    variable: str = Field(default="x", max_length=200)
    variables: List[str] = Field(default_factory=list, max_length=20)
    initialGuess: Optional[Any] = None
    initialGuesses: List[Any] = Field(default_factory=list, max_length=20)
    interval: Optional[List[Any]] = Field(default=None, min_length=2, max_length=2)
    solution: Optional[Any] = None
    assumptions: Dict[str, List[str]] = Field(default_factory=dict)
    domain: Literal["real", "complex"] = "real"
    maxSteps: int = Field(default=100, ge=1, le=10000)
    tolerance: float = Field(default=1e-12, gt=0)


class SolverCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    solver: SolverRequest


def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)


def _symbols(req: SolverRequest) -> Dict[str, sp.Symbol]:
    names = set(req.variables)
    names.add(req.variable)
    names.update(req.assumptions.keys())
    supported = {
        "real", "positive", "negative", "nonzero", "integer",
        "rational", "irrational", "finite", "nonnegative", "nonpositive",
    }
    table: Dict[str, sp.Symbol] = {}
    for name in sorted(names):
        kwargs = {
            a: True for a in req.assumptions.get(name, [])
            if a in supported
        }
        table[name] = sp.Symbol(name, **kwargs)
    return table


def _expr(text: str, symbols: Dict[str, sp.Symbol]) -> sp.Expr:
    return sp.sympify(text, locals=symbols)


def _equation(text: str, symbols: Dict[str, sp.Symbol]) -> sp.Equality:
    if "=" in text:
        left, right = text.split("=", 1)
        return sp.Eq(_expr(left, symbols), _expr(right, symbols))
    return sp.Eq(_expr(text, symbols), 0)


def _residual(eq: sp.Equality, substitutions: Dict[sp.Symbol, Any]) -> sp.Expr:
    return sp.simplify((eq.lhs - eq.rhs).subs(substitutions))


def _serialize_solution(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_solution(v) for v in value]
    if isinstance(value, sp.Set):
        return str(value)
    if isinstance(value, sp.Basic):
        return str(value)
    return value


def execute_solver(req: SolverRequest) -> Dict[str, Any]:
    symbols = _symbols(req)
    var = symbols.get(req.variable) or sp.Symbol(req.variable)
    op = req.operation
    details: Dict[str, Any] = {}
    verification: Dict[str, Any] = {}
    method = "sympy"

    if op == "solve-exact":
        if not req.equation:
            raise ValueError("solve-exact requires equation")
        eq = _equation(req.equation, symbols)
        domain = sp.S.Reals if req.domain == "real" else sp.S.Complexes
        result = sp.solveset(eq.lhs - eq.rhs, var, domain=domain)
        details["domain"] = req.domain
        verification["symbolicEquation"] = str(eq)

    elif op == "solve-numeric":
        if not req.equation:
            raise ValueError("solve-numeric requires equation")
        eq = _equation(req.equation, symbols)
        guess = req.initialGuess if req.initialGuess is not None else 0
        root = sp.nsolve(eq.lhs - eq.rhs, var, sp.sympify(guess), tol=req.tolerance, maxsteps=req.maxSteps)
        result = root
        residual = sp.N(_residual(eq, {var: root}))
        verification = {
            "equation": str(eq),
            "residual": str(residual),
            "residualAcceptable": bool(abs(complex(residual)) <= max(req.tolerance * 10, 1e-10)),
        }
        method = "sympy-nsolve"

    elif op == "solve-system":
        equations = req.equations or ([req.equation] if req.equation else [])
        if not equations:
            raise ValueError("solve-system requires equations")
        parsed = [_equation(e, symbols) for e in equations]
        solve_vars = [symbols.get(v) or sp.Symbol(v) for v in req.variables]
        if not solve_vars:
            solve_vars = [var]
        result = sp.solve(parsed, solve_vars, dict=True)
        residuals = []
        for solution in result:
            residuals.append([
                str(_residual(eq, solution))
                for eq in parsed
            ])
        verification = {
            "equationCount": len(parsed),
            "variableCount": len(solve_vars),
            "residuals": residuals,
            "allResidualsZero": all(
                all(r == "0" for r in group)
                for group in residuals
            ) if residuals else True,
        }

    elif op == "solve-inequality":
        if not req.equation:
            raise ValueError("solve-inequality requires equation")
        relation = _expr(req.equation, symbols)
        result = sp.solve_univariate_inequality(relation, var, relational=False)
        details["relationalInput"] = req.equation

    elif op == "reduce-inequalities":
        expressions = req.equations or ([req.equation] if req.equation else [])
        if not expressions:
            raise ValueError("reduce-inequalities requires expressions")
        relations = [_expr(e, symbols) for e in expressions]
        solve_vars = [symbols.get(v) or sp.Symbol(v) for v in req.variables] or [var]
        result = sp.reduce_inequalities(relations, solve_vars)

    elif op == "isolate-roots":
        if not req.equation:
            raise ValueError("isolate-roots requires equation")
        eq = _equation(req.equation, symbols)
        poly = sp.Poly(eq.lhs - eq.rhs, var)
        if req.interval:
            a = sp.sympify(req.interval[0])
            b = sp.sympify(req.interval[1])
            intervals = sp.polys.polytools.intervals(poly, eps=req.tolerance)
            intervals = [
                (iv, mult) for iv, mult in intervals
                if iv[1] >= a and iv[0] <= b
            ]
        else:
            intervals = sp.polys.polytools.intervals(poly, eps=req.tolerance)
        result = [
            {
                "interval": [str(iv[0]), str(iv[1])],
                "multiplicity": int(mult),
            }
            for iv, mult in intervals
        ]
        details["degree"] = int(poly.degree())

    elif op == "verify-solution":
        if not req.equation:
            raise ValueError("verify-solution requires equation")
        if req.solution is None:
            raise ValueError("verify-solution requires solution")
        eq = _equation(req.equation, symbols)
        sol = sp.sympify(req.solution)
        residual = sp.simplify(_residual(eq, {var: sol}))
        result = residual == 0
        verification = {
            "equation": str(eq),
            "solution": str(sol),
            "residual": str(residual),
            "verified": bool(result),
        }

    else:
        raise ValueError(f"Unsupported solver operation: {op}")

    result_value = _serialize_solution(result)

    body = {
        "ok": True,
        "schema": SOLVER_SCHEMA,
        "version": VERSION,
        "operation": op,
        "engine": "sympy",
        "method": method,
        "input": {
            "equation": req.equation,
            "equations": req.equations,
            "variable": req.variable,
            "variables": req.variables,
            "domain": req.domain,
            "tolerance": req.tolerance,
        },
        "result": result_value,
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
    solver: SolverRequest,
) -> Dict[str, Any]:
    obj = build_calculation_object(req)
    solver_result = execute_solver(solver)

    obj["extensions"] = dict(obj.get("extensions") or {})
    obj["extensions"]["solverLaboratory"] = solver_result
    obj["result"]["solverLaboratory"] = solver_result["result"]
    obj["executionPlan"]["solverLaboratory"] = {
        "engine": solver_result["engine"],
        "method": solver_result["method"],
        "operation": solver.operation,
    }
    obj["verification"]["solverLaboratory"] = solver_result["verification"]
    obj["provenance"]["solverResultHash"] = solver_result["resultHash"]
    obj["calculationObjectHash"] = _hash(
        {k: v for k, v in obj.items() if k not in {"ok", "calculationObjectHash"}}
    )
    return obj


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Equation & Solver Laboratory",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "engine": "sympy",
        "wordpressRequired": False,
        "capabilities": {
            "exactEquationSolving": True,
            "numericRootSolving": True,
            "symbolicSystems": True,
            "inequalitySolving": True,
            "inequalityReduction": True,
            "polynomialRootIsolation": True,
            "solutionVerification": True,
            "residualDiagnostics": True,
            "assumptionAwareSymbols": True,
            "calculationObjectExtension": True,
        },
    }


@router.get("/v1130/status")
def status_route():
    return status()


@router.post("/calculation-engine/v1/solver")
def solver_route(req: SolverRequest):
    return execute_solver(req)


@router.post("/calculation-engine/v1/solver/calculation-object")
def solver_calculation_object_route(req: SolverCalculationObjectRequest):
    return calculation_object_extension(
        req.calculationObjectRequest,
        req.solver,
    )

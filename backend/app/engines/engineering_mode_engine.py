from __future__ import annotations

import re
from typing import Any

import sympy as sp

from .common import result
from .symbolic_engine import (
    parse_symbolic_input,
    chalkboard_preview,
    normalize_keyboard_math,
    _select_variable,
    _try_pint_unit_analysis,
    _unit_lines,
    _split_equation,
    _eval_quantity_expression,
)

_DOMAIN_PATTERNS: list[tuple[str, set[str], list[str], list[str]]] = [
    (
        "mechanical / structural",
        {"F", "m", "a", "sigma", "stress", "strain", "E", "A", "L", "delta", "I", "M", "V"},
        ["Linear elastic behavior unless otherwise stated.", "Static loading unless time dependence is explicit.", "Geometry, supports, and material properties are user supplied."],
        ["Check factor of safety against the governing code or design standard.", "Confirm whether loads are service, factored, static, dynamic, or fatigue-related."],
    ),
    (
        "electrical / power",
        {"V", "I", "R", "P", "C", "L", "Q", "omega", "f", "Z"},
        ["Steady-state or lumped-element behavior unless the input defines a transient model.", "Component values are assumed ideal unless tolerances are supplied."],
        ["Check voltage, current, thermal, insulation, and component rating limits.", "Include tolerance and derating analysis for real hardware."],
    ),
    (
        "fluids / thermal / energy",
        {"Q", "T", "h", "k", "rho", "mu", "P", "A", "v", "cp", "Delta"},
        ["Continuum behavior and consistent thermodynamic state variables are assumed.", "Boundary conditions must be reviewed before using the result."],
        ["Check Reynolds/flow regime, heat-transfer correlations, pressure limits, and boundary assumptions.", "Validate material and fluid properties at operating temperature."],
    ),
]

_DEFAULT_ASSUMPTIONS = [
    "Inputs are user-provided and not independently verified.",
    "Units must be consistent across formula terms.",
    "The calculation is a first-pass analytical note, not a certified design calculation.",
]

_DEFAULT_REVIEW_CHECKS = [
    "Confirm units and dimensional consistency.",
    "Confirm operating range, domain limits, and invalid values such as division by zero or negative square-root arguments.",
    "Run sensitivity checks on high-uncertainty parameters.",
    "Compare with a known case, hand calculation, published formula, standard, or simulation when available.",
]

_SYMBOL_MEANINGS = {
    "F": "force",
    "m": "mass or slope, depending on context",
    "a": "acceleration or coefficient",
    "A": "area or amplitude",
    "sigma": "stress or standard deviation",
    "E": "elastic modulus, energy, or mathematical constant depending on context",
    "I": "current or second moment of area depending on context",
    "V": "voltage, volume, or shear depending on context",
    "R": "resistance or radius depending on context",
    "P": "power, pressure, or load depending on context",
    "Q": "heat flow, charge, or flow rate depending on context",
    "k": "stiffness, rate constant, or conductivity depending on context",
    "omega": "angular frequency",
    "theta": "angle",
    "x": "independent variable or position",
    "t": "time",
}


def _fallback_unit_analysis(raw: str) -> dict[str, Any] | None:
    """Small fallback when Pint is unavailable in local tests.

    It does not simplify dimensions; it preserves the unit algebra as a review aid.
    Production deployments should use Pint from requirements.txt for stronger unit handling.
    """
    formula_lines, assignment_lines = _unit_lines(raw)
    if not assignment_lines:
        return None
    values: dict[str, float] = {}
    units: dict[str, str] = {}
    warnings: list[str] = ["Using lightweight unit fallback because Pint is unavailable or did not produce a result. Unit algebra is not fully simplified."]
    for line in assignment_lines:
        lhs, rhs = _split_equation(line)
        if not lhs:
            continue
        name = re.sub(r"[^A-Za-z0-9_]", "", lhs.strip())
        match = re.match(r"^\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*(.*)$", rhs.strip())
        if not match:
            warnings.append(f"Could not parse numeric/unit assignment {line!r}.")
            continue
        values[name] = float(match.group(1))
        units[name] = match.group(2).strip() or "dimensionless"
    if not formula_lines or not values:
        return {"assignments": {k: f"{values[k]} {units.get(k,'')}" for k in values}, "warnings": warnings}
    formula = formula_lines[0]
    lhs, rhs = _split_equation(formula)
    if not lhs or not rhs:
        return {"assignments": {k: f"{values[k]} {units.get(k,'')}" for k in values}, "warnings": warnings}
    target = re.sub(r"[^A-Za-z0-9_]", "", lhs.strip()) or lhs.strip()
    try:
        magnitude = _eval_quantity_expression(rhs, values)
        unit_expr = normalize_keyboard_math(rhs)
        # Replace longer variable names first so F_load does not partially replace F.
        for name in sorted(units, key=len, reverse=True):
            unit_expr = re.sub(rf"\b{re.escape(name)}\b", f"({units[name]})", unit_expr)
        unit_expr = unit_expr.replace("**", "^").replace("*", " * ").replace("/", " / ")
        return {
            "target": target,
            "formula": formula,
            "quantity": f"{magnitude:g} {unit_expr}",
            "magnitude": float(magnitude),
            "units": unit_expr,
            "assignments": {k: f"{values[k]:g} {units.get(k,'')}" for k in values},
            "warnings": warnings,
        }
    except Exception as exc:
        warnings.append(f"Could not evaluate fallback unit formula: {exc}")
        return {"assignments": {k: f"{values[k]} {units.get(k,'')}" for k in values}, "warnings": warnings}


def _infer_domain(symbols: list[str], raw: str) -> tuple[str, list[str], list[str]]:
    raw_l = raw.lower()
    symbol_set = set(symbols)
    best = ("general engineering", list(_DEFAULT_ASSUMPTIONS), list(_DEFAULT_REVIEW_CHECKS))
    best_score = 0
    for domain, keys, assumptions, checks in _DOMAIN_PATTERNS:
        score = len(symbol_set.intersection(keys))
        if domain.split(" / ")[0] in raw_l:
            score += 2
        if score > best_score:
            best_score = score
            best = (domain, list(dict.fromkeys(_DEFAULT_ASSUMPTIONS + assumptions)), list(dict.fromkeys(_DEFAULT_REVIEW_CHECKS + checks)))
    return best


def _variables_table(parsed_symbols: list[str], unit_analysis: dict[str, Any] | None) -> list[dict[str, Any]]:
    assignments = (unit_analysis or {}).get("assignments") or {}
    table: list[dict[str, Any]] = []
    for name in parsed_symbols:
        table.append({
            "symbol": name,
            "meaning": _SYMBOL_MEANINGS.get(name, "user-defined variable or parameter"),
            "assigned_value": assignments.get(name, "not supplied"),
            "review_note": "Confirm definition, units, and valid range before relying on output.",
        })
    for name, value in assignments.items():
        if name not in parsed_symbols:
            table.append({
                "symbol": name,
                "meaning": _SYMBOL_MEANINGS.get(name, "assigned engineering input"),
                "assigned_value": value,
                "review_note": "Used as a unit-aware assignment if referenced by the formula.",
            })
    return table


def _formula_summary(raw: str, parsed: Any) -> dict[str, Any]:
    formula_lines, assignment_lines = _unit_lines(raw)
    first_formula = formula_lines[0] if formula_lines else parsed.expression_text
    lhs, rhs = _split_equation(first_formula)
    return {
        "primary_formula": first_formula,
        "target": lhs or "expression",
        "right_hand_side": rhs if lhs else parsed.rhs_text,
        "assignment_count": len(assignment_lines),
        "assignments_detected": assignment_lines,
    }


def _domain_warnings(parsed: Any, unit_analysis: dict[str, Any] | None, include_safety_boundary: bool = True) -> list[str]:
    warnings: list[str] = list(parsed.warnings)
    if unit_analysis:
        warnings.extend(unit_analysis.get("warnings", []))
    else:
        warnings.append("No complete unit-aware numerical evaluation was produced. Add lines such as m = 12 kg or A = 0.02 m^2 for engineering-unit checking.")
    if parsed.expression is not None:
        free = [str(s) for s in parsed.expression.free_symbols]
        if free:
            warnings.append("Unassigned symbols remain: " + ", ".join(free) + ". Treat the output as symbolic until numerical values and units are supplied.")
    if include_safety_boundary:
        warnings.append("Engineering Mode is not a stamped, code-compliant, safety-critical, or licensed professional engineering calculation.")
    return list(dict.fromkeys([w for w in warnings if w]))


def _solve_candidates(parsed: Any, variable: str | None) -> dict[str, Any]:
    if parsed.expression is None:
        return {"status": "not_available"}
    try:
        x = _select_variable(parsed, variable)
        target = parsed.equation if parsed.equation is not None else sp.Eq(parsed.expression, 0)
        sol = sp.solve(target, x)
        return {
            "solve_for": str(x),
            "solutions": [sp.sstr(s) for s in sol],
            "latex_solutions": [sp.latex(s) for s in sol],
            "status": "closed_form_found" if sol else "no_closed_form_solution_found",
        }
    except Exception as exc:
        return {"status": "solve_failed", "error": str(exc)}


def _engineering_note(parsed: Any, unit_analysis: dict[str, Any] | None, assumptions: list[str], checks: list[str]) -> dict[str, Any]:
    formula = _formula_summary(parsed.raw, parsed)
    quantity = None
    if unit_analysis and unit_analysis.get("quantity"):
        quantity = {
            "target": unit_analysis.get("target"),
            "quantity": unit_analysis.get("quantity"),
            "magnitude": unit_analysis.get("magnitude"),
            "units": unit_analysis.get("units"),
        }
    return {
        "calculation_note_sections": [
            "Problem / relationship",
            "Inputs and units",
            "Formula and symbolic form",
            "Computation result",
            "Assumptions",
            "Validation checks",
            "Limitations and next review",
        ],
        "problem_relationship": formula,
        "computed_result": quantity or "No numerical unit-aware result yet. Supply numerical assignments with units to compute one.",
        "assumptions": assumptions,
        "validation_checks": checks,
        "sensitivity_template": [
            "Identify the parameter with the largest uncertainty.",
            "Vary that parameter across a low / nominal / high range.",
            "Regenerate Graph Studio output or rerun Engineering Mode for each case.",
            "Record whether the decision changes across the tested range.",
        ],
    }


def engineering_mode_analyzer(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = str(inputs.get("input") or inputs.get("expression") or "F = m*a\nm = 12 kg\na = 3.5 m/s^2")
    variable = str(inputs.get("variable") or "").strip() or None
    include_solve = inputs.get("include_solve") in {True, "true", "1", 1, "yes"}

    parsed = parse_symbolic_input(raw)
    unit_analysis = _try_pint_unit_analysis(raw) or _fallback_unit_analysis(raw)
    domain, assumptions, checks = _infer_domain(parsed.variables, raw)
    variables = _variables_table(parsed.variables, unit_analysis)
    formula = _formula_summary(raw, parsed)
    note = _engineering_note(parsed, unit_analysis, assumptions, checks)

    values: dict[str, Any] = {
        "keyboard_input": raw,
        "chalkboard_preview": parsed.chalkboard or chalkboard_preview(raw),
        "latex": parsed.latex,
        "sympy_code": parsed.sympy_code,
        "engineering_domain": domain,
        "formula_summary": formula,
        "variables": variables,
        "unit_analysis": unit_analysis or {},
        "engineering_note": note,
        "recommended_output_template": {
            "1_problem": "State the engineering relationship and objective.",
            "2_inputs": "List variables, values, units, and sources.",
            "3_formula": "Show the chalkboard equation, LaTeX, and machine-readable expression.",
            "4_result": "Show exact/symbolic and numerical unit-aware result if available.",
            "5_graph_or_sensitivity": "Use Graph Studio when parameters vary or a curve is more informative than one number.",
            "6_assumptions": "List assumptions explicitly.",
            "7_review": "List code, safety, tolerance, and professional-review checks.",
        },
    }
    if include_solve:
        values["symbolic_solve"] = _solve_candidates(parsed, variable)

    warnings = _domain_warnings(parsed, unit_analysis)
    method = [
        "Parsed the keyboard/chalkboard expression into symbolic form.",
        "Separated formula lines from numerical unit assignments.",
        "Attempted unit-aware computation with Pint where enough assignments were supplied.",
        "Inferred an engineering-domain template from symbols and context.",
        "Produced a reviewable calculation-note structure with assumptions, checks, and limitations.",
    ]
    interpretation = [
        "Use Engineering Mode when the user needs a calculation note rather than only an answer.",
        "Use Graph Studio next when a parameter, load, frequency, distance, time, or operating range should be varied.",
        "Use a licensed professional review path for safety-critical, code-governed, or regulated engineering decisions.",
    ]
    return result(
        "Engineering Mode",
        "Generated an engineering-style output template with variables, unit checks, assumptions, validation checks, warnings, and a calculation-note structure.",
        values,
        warnings,
        [],
        method,
        "python/sympy + pint + engineering-mode template",
        interpretation,
    ) | {"engineering_mode": values["engineering_note"]}

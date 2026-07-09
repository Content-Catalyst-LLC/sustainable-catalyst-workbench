from __future__ import annotations

import ast
import io
import math
import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
    function_exponentiation,
)

from .common import result, svg_from_figure

TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
    function_exponentiation,
)

_SAFE_SYMBOL_NAMES = {
    "x", "y", "z", "t", "a", "b", "c", "d", "e", "f", "g", "h", "k", "m", "n", "r",
    "theta", "phi", "omega", "lambda", "mu", "sigma", "alpha", "beta", "gamma", "delta", "rho", "tau",
    "F", "A", "V", "I", "R", "P", "E", "L", "T", "Q", "C", "G", "M", "N", "K",
}

_FUNCTION_NAMES = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh, "sqrt": sp.sqrt, "log": sp.log, "ln": sp.log,
    "exp": sp.exp, "abs": sp.Abs, "floor": sp.floor, "ceiling": sp.ceiling,
}

_GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "theta": "θ", "lambda": "λ",
    "mu": "μ", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "phi": "φ", "omega": "ω", "Delta": "Δ",
    "Omega": "Ω", "Sigma": "Σ",
}

_SUPERSCRIPTS = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
_SUBSCRIPTS = str.maketrans("0123456789+-=()n", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₙ")


@dataclass
class ParsedMath:
    raw: str
    expression_text: str
    lhs_text: str | None
    rhs_text: str
    expression: sp.Expr | None
    equation: sp.Eq | None
    variables: list[str]
    latex: str
    sympy_code: str
    chalkboard: str
    warnings: list[str]


def _base_locals() -> dict[str, Any]:
    locals_map: dict[str, Any] = dict(_FUNCTION_NAMES)
    for name in _SAFE_SYMBOL_NAMES:
        locals_map[name] = sp.Symbol(name)
    locals_map.update({"pi": sp.pi, "E": sp.E, "oo": sp.oo, "inf": sp.oo})
    return locals_map


def normalize_keyboard_math(text: str) -> str:
    """Normalize ordinary keyboard math into parser-friendly expression text."""
    s = (text or "").strip()
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("×", "*").replace("·", "*").replace("÷", "/")
    s = s.replace("^", "**")
    s = re.sub(r"\bln\s*\(", "log(", s)
    s = re.sub(r"\bπ\b", "pi", s)
    s = re.sub(r"\b∞\b", "oo", s)
    for word, greek in _GREEK.items():
        # Greek unicode back to parser word when user pasted a symbol.
        s = s.replace(greek, word)
    return s


def chalkboard_preview(text: str) -> str:
    """Create a readable unicode approximation for immediate chalkboard preview."""
    s = (text or "").strip()
    replacements = {
        "theta": "θ", "lambda": "λ", "mu": "μ", "sigma": "σ", "omega": "ω", "alpha": "α", "beta": "β",
        "gamma": "γ", "delta": "δ", "phi": "φ", "pi": "π", "sqrt": "√", "*": "·", "<=": "≤", ">=": "≥",
        "!=": "≠", "->": "→", "+-": "±", "infty": "∞", "inf": "∞",
    }
    for a, b in replacements.items():
        s = re.sub(rf"(?<![A-Za-z]){re.escape(a)}(?![A-Za-z])", b, s) if a.isalpha() else s.replace(a, b)
    # Simple exponent/subscript typography for common keyboard forms.
    s = re.sub(r"\^\{([^{}]+)\}", lambda m: m.group(1).translate(_SUPERSCRIPTS), s)
    s = re.sub(r"\^([A-Za-z0-9+\-=()]+)", lambda m: m.group(1).translate(_SUPERSCRIPTS), s)
    s = re.sub(r"_\{([^{}]+)\}", lambda m: m.group(1).translate(_SUBSCRIPTS), s)
    s = re.sub(r"_([A-Za-z0-9+\-=()]+)", lambda m: m.group(1).translate(_SUBSCRIPTS), s)
    return s


def _split_equation(text: str) -> tuple[str | None, str]:
    # Avoid treating <=, >=, !=, == as assignment/equation delimiters in the simple split.
    match = re.search(r"(?<![<>!=])=(?![=])", text)
    if not match:
        return None, text
    return text[:match.start()].strip(), text[match.end():].strip()


def _parse_side(side: str) -> sp.Expr:
    side = normalize_keyboard_math(side)
    return parse_expr(side, local_dict=_base_locals(), transformations=TRANSFORMATIONS, evaluate=True)


def parse_symbolic_input(text: str) -> ParsedMath:
    warnings: list[str] = []
    raw = text or ""
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    expression_text = lines[0] if lines else raw.strip()
    lhs_text, rhs_text = _split_equation(expression_text)
    equation = None
    expression = None
    try:
        if lhs_text:
            # Handle f(x)=... as y=... for plotting/computation while preserving original lhs in output.
            lhs_parse_text = lhs_text
            if re.match(r"^[A-Za-z_]\w*\s*\([^)]*\)$", lhs_parse_text):
                lhs_parse_text = "y"
            lhs = _parse_side(lhs_parse_text)
            rhs = _parse_side(rhs_text)
            equation = sp.Eq(lhs, rhs)
            expression = rhs if str(lhs) in {"y", "f"} or re.match(r"^[A-Za-z_]\w*\s*\([^)]*\)$", lhs_text) else lhs - rhs
            latex = sp.latex(equation)
            sympy_code = f"Eq({sp.sstr(lhs)}, {sp.sstr(rhs)})"
        else:
            expression = _parse_side(rhs_text)
            latex = sp.latex(expression)
            sympy_code = sp.sstr(expression)
    except Exception as exc:
        warnings.append(f"Could not fully parse symbolic expression: {exc}")
        latex = raw.strip()
        sympy_code = normalize_keyboard_math(raw)
    free_symbols = sorted([str(s) for s in (expression.free_symbols if expression is not None else [])])
    return ParsedMath(
        raw=raw,
        expression_text=expression_text,
        lhs_text=lhs_text,
        rhs_text=rhs_text,
        expression=expression,
        equation=equation,
        variables=free_symbols,
        latex=latex,
        sympy_code=sympy_code,
        chalkboard=chalkboard_preview(expression_text),
        warnings=warnings,
    )


def _select_variable(parsed: ParsedMath, requested: str | None = None) -> sp.Symbol:
    if requested:
        return sp.Symbol(str(requested).strip())
    if "x" in parsed.variables:
        return sp.Symbol("x")
    if parsed.variables:
        return sp.Symbol(parsed.variables[0])
    return sp.Symbol("x")


def _unit_lines(raw: str) -> tuple[list[str], list[str]]:
    formula_lines: list[str] = []
    assignment_lines: list[str] = []
    for line in [ln.strip() for ln in raw.splitlines() if ln.strip()]:
        if "=" in line:
            lhs, rhs = _split_equation(line)
            if lhs and re.search(r"\d", rhs) and re.search(r"[A-Za-zµΩ°]", rhs):
                assignment_lines.append(line)
            else:
                formula_lines.append(line)
        else:
            formula_lines.append(line)
    return formula_lines, assignment_lines


def _try_pint_unit_analysis(raw: str) -> dict[str, Any] | None:
    try:
        import pint  # type: ignore
    except Exception:
        return None
    ureg = pint.UnitRegistry(auto_reduce_dimensions=True)
    formula_lines, assignment_lines = _unit_lines(raw)
    if not assignment_lines:
        return None
    assignments: dict[str, Any] = {}
    warnings: list[str] = []
    for line in assignment_lines:
        lhs, rhs = _split_equation(line)
        if not lhs:
            continue
        name = re.sub(r"[^A-Za-z0-9_]", "", lhs.strip())
        rhs_norm = normalize_keyboard_math(rhs).replace("**", "^")
        try:
            assignments[name] = ureg.parse_expression(rhs_norm)
        except Exception as exc:
            warnings.append(f"Could not parse unit assignment {line!r}: {exc}")
    if not formula_lines or not assignments:
        return {"assignments": {k: str(v) for k, v in assignments.items()}, "warnings": warnings}
    formula = formula_lines[0]
    lhs, rhs = _split_equation(formula)
    if not lhs or not rhs:
        return {"assignments": {k: str(v) for k, v in assignments.items()}, "warnings": warnings}
    target = re.sub(r"[^A-Za-z0-9_]", "", lhs.strip()) or lhs.strip()
    try:
        quantity = _eval_quantity_expression(rhs, assignments)
        return {
            "target": target,
            "formula": formula,
            "quantity": str(quantity),
            "magnitude": float(quantity.magnitude) if getattr(quantity, "magnitude", None) is not None and np.isfinite(float(quantity.magnitude)) else str(getattr(quantity, "magnitude", "")),
            "units": str(quantity.units),
            "assignments": {k: str(v) for k, v in assignments.items()},
            "warnings": warnings,
        }
    except Exception as exc:
        warnings.append(f"Could not evaluate unit-aware formula: {exc}")
        return {"assignments": {k: str(v) for k, v in assignments.items()}, "warnings": warnings}


def _eval_quantity_expression(expr: str, values: dict[str, Any]) -> Any:
    """Small safe evaluator for quantity arithmetic; supports + - * / ** and selected math functions."""
    tree = ast.parse(normalize_keyboard_math(expr), mode="eval")
    def ev(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in values:
                return values[node.id]
            if node.id == "pi":
                return math.pi
            raise ValueError(f"Unknown variable {node.id}")
        if isinstance(node, ast.UnaryOp):
            value = ev(node.operand)
            if isinstance(node.op, ast.USub): return -value
            if isinstance(node.op, ast.UAdd): return value
        if isinstance(node, ast.BinOp):
            left, right = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
            if isinstance(node.op, ast.Pow): return left ** right
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fname = node.func.id
            args = [ev(a) for a in node.args]
            if fname in {"sin", "cos", "tan", "sqrt", "log", "exp"}:
                return getattr(math, fname)(*args)
        raise ValueError(f"Unsupported unit expression syntax: {ast.dump(node, include_attributes=False)}")
    return ev(tree)


def _symbolic_action(parsed: ParsedMath, action: str, variable: str | None = None) -> dict[str, Any]:
    values: dict[str, Any] = {}
    warnings: list[str] = []
    steps: list[str] = []
    if parsed.expression is None:
        return values | {"symbolic_result": "unparsed"}
    x = _select_variable(parsed, variable)
    expr = parsed.expression
    action = (action or "translate").lower()
    if action == "simplify":
        out = sp.simplify(expr)
        values.update({"symbolic_result": sp.sstr(out), "latex_result": sp.latex(out), "operation": "simplify"})
        steps.append("Simplified the expression symbolically.")
    elif action == "factor":
        out = sp.factor(expr)
        values.update({"symbolic_result": sp.sstr(out), "latex_result": sp.latex(out), "operation": "factor"})
        steps.append("Factored the expression where possible.")
    elif action == "expand":
        out = sp.expand(expr)
        values.update({"symbolic_result": sp.sstr(out), "latex_result": sp.latex(out), "operation": "expand"})
        steps.append("Expanded products and powers where possible.")
    elif action == "differentiate":
        out = sp.diff(expr, x)
        values.update({"symbolic_result": sp.sstr(out), "latex_result": sp.latex(out), "operation": f"differentiate with respect to {x}"})
        steps.append(f"Differentiated with respect to {x}.")
    elif action == "integrate":
        out = sp.integrate(expr, x)
        values.update({"symbolic_result": sp.sstr(out), "latex_result": sp.latex(out), "operation": f"integrate with respect to {x}"})
        steps.append(f"Integrated with respect to {x}.")
    elif action == "solve":
        target_expr = parsed.equation if parsed.equation is not None else sp.Eq(expr, 0)
        sol = sp.solve(target_expr, x)
        values.update({"symbolic_result": [sp.sstr(s) for s in sol], "latex_result": [sp.latex(s) for s in sol], "operation": f"solve for {x}"})
        steps.append(f"Solved the expression/equation for {x}.")
        if not sol:
            warnings.append("No closed-form solution was found for the selected variable.")
    else:
        values.update({"symbolic_result": sp.sstr(expr), "latex_result": parsed.latex, "operation": "translate"})
        steps.append("Translated keyboard notation into symbolic code and mathematical notation.")
    return {"values": values, "warnings": warnings, "steps": steps}


def _graph_expression(parsed: ParsedMath, variable: str | None, x_min: float, x_max: float) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    graphs: list[dict[str, Any]] = []
    if parsed.expression is None:
        return graphs, ["Expression could not be parsed for graphing."]
    x = _select_variable(parsed, variable)
    free = [str(s) for s in parsed.expression.free_symbols]
    non_x = [s for s in free if s != str(x)]
    if non_x:
        warnings.append("Graph uses default value 1.0 for non-axis parameters: " + ", ".join(non_x))
    expr = parsed.expression.subs({sp.Symbol(s): 1.0 for s in non_x})
    try:
        fn = sp.lambdify(x, expr, modules=["numpy"])
        xs = np.linspace(float(x_min), float(x_max), 700)
        ys = np.array(fn(xs), dtype=float)
        ys[~np.isfinite(ys)] = np.nan
        fig, ax = plt.subplots(figsize=(8.2, 4.8))
        ax.plot(xs, ys, linewidth=2)
        ax.axhline(0, linewidth=0.9, color="black", alpha=0.35)
        ax.axvline(0, linewidth=0.9, color="black", alpha=0.35)
        ax.grid(alpha=0.24)
        ax.set_xlabel(str(x))
        ax.set_ylabel("f(" + str(x) + ")")
        ax.set_title("Symbolic function graph")
        fig.tight_layout()
        graphs.append({"title": "Symbolic function graph", "type": "function", "svg": svg_from_figure(fig)})
        plt.close(fig)
    except Exception as exc:
        warnings.append(f"Could not graph expression: {exc}")
    return graphs, warnings


def symbolic_math_analyzer(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = str(inputs.get("input") or inputs.get("expression") or "x^2 + 3x - 4")
    action = str(inputs.get("action") or "translate").lower()
    variable = str(inputs.get("variable") or "").strip() or None
    x_min = float(inputs.get("x_min", -10))
    x_max = float(inputs.get("x_max", 10))
    if x_min >= x_max:
        x_min, x_max = -10, 10
    parsed = parse_symbolic_input(raw)
    op = _symbolic_action(parsed, action, variable)
    values = {
        "keyboard_input": raw,
        "chalkboard_preview": parsed.chalkboard,
        "latex": parsed.latex,
        "sympy_code": parsed.sympy_code,
        "variables": parsed.variables,
        "selected_variable": str(_select_variable(parsed, variable)),
        **op.get("values", {}),
    }
    warnings = list(parsed.warnings) + op.get("warnings", [])
    steps = op.get("steps", [])
    unit_analysis = _try_pint_unit_analysis(raw)
    if unit_analysis:
        values["unit_analysis"] = unit_analysis
        warnings.extend(unit_analysis.get("warnings", []))
        steps.append("Parsed unit assignments and evaluated unit-aware formula where possible.")
    graphs: list[dict[str, Any]] = []
    if action == "graph" or inputs.get("include_graph") in {True, "true", "1", 1}:
        graph_list, graph_warnings = _graph_expression(parsed, variable, x_min, x_max)
        graphs.extend(graph_list)
        warnings.extend(graph_warnings)
        if graph_list:
            steps.append("Generated a function graph over the selected domain.")
    return result(
        "Chalkboard Translator + Symbolic Math",
        "Translated keyboard math into chalkboard-style notation, LaTeX, SymPy code, symbolic output, unit-aware engineering notes, and optional graph output.",
        values,
        warnings,
        graphs,
        steps,
        "python/sympy + pint + matplotlib",
    )

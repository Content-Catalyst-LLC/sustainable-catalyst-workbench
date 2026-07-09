from __future__ import annotations

import math
from typing import Any

import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

from .common import result, svg_from_figure
from .symbolic_engine import parse_symbolic_input, _select_variable, chalkboard_preview


def _safe_float(value: Any, default: float) -> float:
    try:
        out = float(value)
        if math.isfinite(out):
            return out
    except Exception:
        pass
    return default


def _parameter_defaults(parsed_symbols: list[str], axis: str, supplied: dict[str, Any] | None = None) -> dict[str, float]:
    supplied = supplied or {}
    defaults: dict[str, float] = {}
    for name in parsed_symbols:
        if name == axis:
            continue
        defaults[name] = _safe_float(supplied.get(name), 1.0)
    return defaults


def _slider_spec(name: str, value: float) -> dict[str, Any]:
    # Conservative defaults that work for coefficients, amplitudes, rates, and offsets.
    span = max(5.0, abs(value) * 5.0)
    lo = min(-span, value - span)
    hi = max(span, value + span)
    # Positive-only conventional parameters get a more useful initial range.
    if name.lower() in {"a", "b", "c", "k", "r", "m", "n", "sigma", "omega", "lambda", "mu"} and value >= 0:
        lo = 0.0
        hi = max(10.0, value * 5.0 if value else 10.0)
    return {
        "name": name,
        "label": name,
        "value": value,
        "min": round(lo, 6),
        "max": round(hi, 6),
        "step": 0.05 if hi - lo <= 20 else 0.1,
    }


def _sample_function(expr: sp.Expr, axis_symbol: sp.Symbol, params: dict[str, float], x_min: float, x_max: float, points: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    warnings: list[str] = []
    safe_points = int(max(80, min(points, 2000)))
    xs = np.linspace(x_min, x_max, safe_points)
    substitutions = {sp.Symbol(k): v for k, v in params.items()}
    expr_subbed = expr.subs(substitutions)
    fn = sp.lambdify(axis_symbol, expr_subbed, modules=["numpy"])
    try:
        ys = np.asarray(fn(xs), dtype=float)
        if ys.shape == ():
            ys = np.full_like(xs, float(ys))
    except Exception as exc:
        raise ValueError(f"Could not evaluate function across the selected domain: {exc}") from exc
    bad = ~np.isfinite(ys)
    if np.any(bad):
        warnings.append("Some graph samples were undefined, infinite, or outside the real-valued plotting range; those points were omitted.")
        ys = ys.astype(float)
        ys[bad] = np.nan
    return xs, ys, warnings


def _make_function_graph(title: str, latex: str, axis: str, xs: np.ndarray, ys: np.ndarray, params: dict[str, float], show_derivative: bool, derivative_y: np.ndarray | None = None) -> dict[str, Any]:
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    ax.plot(xs, ys, linewidth=2.25, label="f(" + axis + ")")
    if show_derivative and derivative_y is not None:
        ax.plot(xs, derivative_y, linewidth=1.65, linestyle="--", label="derivative")
    ax.axhline(0, linewidth=0.9, color="black", alpha=0.35)
    ax.axvline(0, linewidth=0.9, color="black", alpha=0.35)
    ax.grid(alpha=0.24)
    ax.set_xlabel(axis)
    ax.set_ylabel("value")
    subtitle = ", ".join(f"{k}={v:g}" for k, v in params.items())
    ax.set_title(title if not subtitle else f"{title} ({subtitle})")
    if show_derivative and derivative_y is not None:
        ax.legend(loc="best")
    fig.tight_layout()
    svg = svg_from_figure(fig)
    plt.close(fig)
    return {
        "title": title,
        "type": "graph_studio_function",
        "latex": latex,
        "svg": svg,
    }


def graph_studio_analyzer(inputs: dict[str, Any]) -> dict[str, Any]:
    raw = str(inputs.get("input") or inputs.get("expression") or "y = a*sin(b*x)")
    variable = str(inputs.get("variable") or "x").strip() or "x"
    x_min = _safe_float(inputs.get("x_min"), -10.0)
    x_max = _safe_float(inputs.get("x_max"), 10.0)
    if x_min >= x_max:
        x_min, x_max = -10.0, 10.0
    points = int(_safe_float(inputs.get("points"), 700))
    show_derivative = bool(inputs.get("show_derivative") in {True, "true", "1", 1, "yes"})
    parameter_values = inputs.get("parameters") if isinstance(inputs.get("parameters"), dict) else {}

    parsed = parse_symbolic_input(raw)
    warnings = list(parsed.warnings)
    if parsed.expression is None:
        return result(
            "Graph Studio",
            "Graph Studio could not parse the expression into a graphable symbolic function.",
            {
                "keyboard_input": raw,
                "chalkboard_preview": chalkboard_preview(raw),
                "latex": parsed.latex,
                "sympy_code": parsed.sympy_code,
            },
            warnings + ["Use an explicit function such as y = a*sin(b*x), f(x)=x^2, or y = exp(-k*x)*sin(x)."],
            [],
            ["Tried to parse the keyboard expression as a single-variable graphable function."],
            "python/sympy + numpy + matplotlib",
        )

    axis_symbol = _select_variable(parsed, variable)
    axis_name = str(axis_symbol)
    params = _parameter_defaults(parsed.variables, axis_name, parameter_values)
    controls = [_slider_spec(name, value) for name, value in params.items()]
    try:
        xs, ys, sample_warnings = _sample_function(parsed.expression, axis_symbol, params, x_min, x_max, points)
        warnings.extend(sample_warnings)
        derivative_y = None
        derivative_latex = None
        if show_derivative:
            try:
                derivative_expr = sp.diff(parsed.expression.subs({sp.Symbol(k): v for k, v in params.items()}), axis_symbol)
                derivative_latex = sp.latex(derivative_expr)
                _, derivative_y, derivative_warnings = _sample_function(derivative_expr, axis_symbol, {}, x_min, x_max, points)
                warnings.extend(derivative_warnings)
            except Exception as exc:
                warnings.append(f"Could not graph derivative: {exc}")
        graph = _make_function_graph("Graph Studio function", parsed.latex, axis_name, xs, ys, params, show_derivative, derivative_y)
        finite_y = ys[np.isfinite(ys)]
        y_min = float(np.nanmin(finite_y)) if finite_y.size else None
        y_max = float(np.nanmax(finite_y)) if finite_y.size else None
        values = {
            "keyboard_input": raw,
            "chalkboard_preview": parsed.chalkboard,
            "latex": parsed.latex,
            "sympy_code": parsed.sympy_code,
            "axis_variable": axis_name,
            "parameters": params,
            "x_range": [x_min, x_max],
            "sample_points": len(xs),
            "y_min": y_min,
            "y_max": y_max,
        }
        if derivative_latex:
            values["derivative_latex"] = derivative_latex
        return result(
            "Graph Studio",
            "Generated a parameter-aware function graph with slider-ready controls and exportable SVG/PNG output.",
            values,
            warnings,
            [graph],
            [
                "Parsed keyboard or chalkboard-style input into a symbolic expression.",
                "Detected non-axis symbols as adjustable parameters.",
                "Substituted slider parameter values and sampled the function across the selected domain.",
                "Generated an exportable graph for review and article placement.",
            ],
            "python/sympy + numpy + matplotlib",
        ) | {"graph_controls": {"parameters": controls, "x_min": x_min, "x_max": x_max, "variable": axis_name, "show_derivative": show_derivative}}
    except Exception as exc:
        return result(
            "Graph Studio",
            "Graph Studio parsed the expression but could not generate a graph for the selected range.",
            {
                "keyboard_input": raw,
                "chalkboard_preview": parsed.chalkboard,
                "latex": parsed.latex,
                "sympy_code": parsed.sympy_code,
                "axis_variable": axis_name,
                "parameters": params,
            },
            warnings + [str(exc)],
            [],
            ["Parsed the expression, detected variables and parameters, then attempted numerical sampling."],
            "python/sympy + numpy + matplotlib",
        ) | {"graph_controls": {"parameters": controls, "x_min": x_min, "x_max": x_max, "variable": axis_name, "show_derivative": show_derivative}}

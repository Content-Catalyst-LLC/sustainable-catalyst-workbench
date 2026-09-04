"""Workbench v5.2.0 — Interactive Graph Mathematics.

Graph sampling and analysis are built on the v5.1 restricted SymPy parser. User
expressions never pass to Python eval/exec and graph results are returned as
portable, content-hashed graph objects rather than executable code.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Tuple

import sympy as sp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.v510 import RestrictedSympyParser, content_hash

VERSION = "5.2.0"
GRAPH_SCHEMA = "sc-workbench-graph-object/1.0"
MAX_SAMPLES = 1001
MAX_IMPLICIT_GRID = 81
MAX_VECTOR_GRID = 21
MAX_SURFACE_GRID = 51
MAX_PARAMETERS = 8

router = APIRouter(prefix="/v520", tags=["workbench-v520-graph-mathematics"])


def _validate_range(lo: float, hi: float, label: str) -> None:
    if not (math.isfinite(lo) and math.isfinite(hi)) or lo >= hi:
        raise ValueError(f"{label} minimum must be finite and less than maximum.")


def _linspace(lo: float, hi: float, count: int) -> List[float]:
    if count <= 1:
        return [float(lo)]
    step = (hi - lo) / (count - 1)
    return [lo + step * i for i in range(count)]


def _safe_real(expr: sp.Expr, substitutions: Dict[sp.Symbol, Any]) -> Optional[float]:
    try:
        value = sp.N(expr.subs(substitutions), 17)
        if value.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
            return None
        if getattr(value, "is_real", None) is False:
            return None
        result = float(value)
        return result if math.isfinite(result) else None
    except Exception:
        return None


def _parameter_substitutions(parser: RestrictedSympyParser, parameters: Dict[str, float]) -> Dict[sp.Symbol, float]:
    if len(parameters) > MAX_PARAMETERS:
        raise ValueError(f"At most {MAX_PARAMETERS} graph parameters are supported.")
    output: Dict[sp.Symbol, float] = {}
    for name, value in parameters.items():
        if not math.isfinite(value):
            raise ValueError(f"Parameter {name} must be finite.")
        symbol = parser.symbol(name)
        if not isinstance(symbol, sp.Symbol):
            raise ValueError(f"Parameter {name} collides with a reserved mathematical constant.")
        output[symbol] = float(value)
    return output


def _point(x: float, y: float) -> Dict[str, float]:
    return {"x": round(float(x), 12), "y": round(float(y), 12)}


def _graph_object(kind: str, source: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "schema": GRAPH_SCHEMA,
        "version": VERSION,
        "kind": kind,
        "source": source,
        **payload,
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
    }
    record["graphObjectHash"] = content_hash(record)
    return record


class ParameterizedInput(BaseModel):
    parameters: Dict[str, float] = Field(default_factory=dict)


class GraphInput(ParameterizedInput):
    mode: Literal["cartesian", "parametric", "polar", "implicit"] = "cartesian"
    expression: str
    expressionY: Optional[str] = None
    xMin: float = -10.0
    xMax: float = 10.0
    yMin: float = -10.0
    yMax: float = 10.0
    samples: int = Field(default=401, ge=25, le=MAX_SAMPLES)
    tMin: float = 0.0
    tMax: float = float(2 * math.pi)
    gridSize: int = Field(default=45, ge=15, le=MAX_IMPLICIT_GRID)
    derivativeOverlay: bool = False
    integralLower: Optional[float] = None
    integralUpper: Optional[float] = None

    @model_validator(mode="after")
    def validate_graph(self):
        _validate_range(self.xMin, self.xMax, "x range")
        _validate_range(self.yMin, self.yMax, "y range")
        _validate_range(self.tMin, self.tMax, "parameter range")
        if self.mode == "parametric" and not self.expressionY:
            raise ValueError("Parametric graphs require expressionY.")
        if (self.integralLower is None) != (self.integralUpper is None):
            raise ValueError("Integral overlay requires both lower and upper bounds.")
        if self.integralLower is not None and self.integralLower >= self.integralUpper:
            raise ValueError("Integral lower bound must be less than upper bound.")
        return self


class AnalysisInput(ParameterizedInput):
    expression: str
    comparisonExpression: Optional[str] = None
    variable: str = "x"
    xMin: float = -10.0
    xMax: float = 10.0
    samples: int = Field(default=241, ge=31, le=MAX_SAMPLES)
    analyses: List[Literal["roots", "extrema", "intersections"]] = Field(default_factory=lambda: ["roots", "extrema"])

    @model_validator(mode="after")
    def validate_analysis(self):
        _validate_range(self.xMin, self.xMax, "x range")
        if "intersections" in self.analyses and not self.comparisonExpression:
            raise ValueError("Intersection analysis requires comparisonExpression.")
        return self


class VectorFieldInput(ParameterizedInput):
    uExpression: str = "-y"
    vExpression: str = "x"
    xMin: float = -5.0
    xMax: float = 5.0
    yMin: float = -5.0
    yMax: float = 5.0
    gridSize: int = Field(default=13, ge=5, le=MAX_VECTOR_GRID)
    normalize: bool = True

    @model_validator(mode="after")
    def validate_vector(self):
        _validate_range(self.xMin, self.xMax, "x range")
        _validate_range(self.yMin, self.yMax, "y range")
        return self


class SurfaceInput(ParameterizedInput):
    expression: str = "sin(sqrt(x^2+y^2))"
    xMin: float = -6.0
    xMax: float = 6.0
    yMin: float = -6.0
    yMax: float = 6.0
    gridSize: int = Field(default=31, ge=9, le=MAX_SURFACE_GRID)

    @model_validator(mode="after")
    def validate_surface(self):
        _validate_range(self.xMin, self.xMax, "x range")
        _validate_range(self.yMin, self.yMax, "y range")
        return self


def _sample_cartesian(payload: GraphInput) -> Dict[str, Any]:
    parser = RestrictedSympyParser(["x", *payload.parameters.keys()])
    x = parser.symbol("x")
    expr = parser.parse(payload.expression)
    params = _parameter_substitutions(parser, payload.parameters)
    points: List[Optional[Dict[str, float]]] = []
    for xv in _linspace(payload.xMin, payload.xMax, payload.samples):
        yv = _safe_real(expr, {x: xv, **params})
        points.append(_point(xv, yv) if yv is not None else None)
    series: List[Dict[str, Any]] = [{"role": "function", "expression": str(expr), "latex": sp.latex(expr), "points": points}]

    if payload.derivativeOverlay:
        derivative = sp.diff(expr, x)
        derivative_points: List[Optional[Dict[str, float]]] = []
        for xv in _linspace(payload.xMin, payload.xMax, payload.samples):
            yv = _safe_real(derivative, {x: xv, **params})
            derivative_points.append(_point(xv, yv) if yv is not None else None)
        series.append({"role": "derivative", "expression": str(derivative), "latex": sp.latex(derivative), "points": derivative_points})

    integral = None
    if payload.integralLower is not None and payload.integralUpper is not None:
        lower, upper = payload.integralLower, payload.integralUpper
        area_count = max(25, min(payload.samples, 301))
        area_points: List[Optional[Dict[str, float]]] = []
        for xv in _linspace(lower, upper, area_count):
            yv = _safe_real(expr, {x: xv, **params})
            area_points.append(_point(xv, yv) if yv is not None else None)
        symbolic = sp.integrate(expr.subs(params), (x, sp.nsimplify(lower), sp.nsimplify(upper)))
        integral = {
            "lower": lower,
            "upper": upper,
            "exactText": str(symbolic),
            "decimalText": str(sp.N(symbolic, 15)),
            "latex": sp.latex(symbolic),
            "points": area_points,
        }
    return {"series": series, "integralOverlay": integral}


def _sample_parametric(payload: GraphInput) -> Dict[str, Any]:
    parser = RestrictedSympyParser(["t", *payload.parameters.keys()])
    t = parser.symbol("t")
    x_expr = parser.parse(payload.expression)
    y_expr = parser.parse(payload.expressionY or "0")
    params = _parameter_substitutions(parser, payload.parameters)
    points: List[Optional[Dict[str, float]]] = []
    for tv in _linspace(payload.tMin, payload.tMax, payload.samples):
        xv = _safe_real(x_expr, {t: tv, **params})
        yv = _safe_real(y_expr, {t: tv, **params})
        points.append(_point(xv, yv) if xv is not None and yv is not None else None)
    return {"series": [{"role": "parametric", "xExpression": str(x_expr), "yExpression": str(y_expr), "latex": [sp.latex(x_expr), sp.latex(y_expr)], "points": points}], "integralOverlay": None}


def _sample_polar(payload: GraphInput) -> Dict[str, Any]:
    parser = RestrictedSympyParser(["theta", *payload.parameters.keys()])
    theta = parser.symbol("theta")
    r_expr = parser.parse(payload.expression)
    params = _parameter_substitutions(parser, payload.parameters)
    points: List[Optional[Dict[str, float]]] = []
    for tv in _linspace(payload.tMin, payload.tMax, payload.samples):
        rv = _safe_real(r_expr, {theta: tv, **params})
        if rv is None:
            points.append(None)
        else:
            points.append(_point(rv * math.cos(tv), rv * math.sin(tv)))
    return {"series": [{"role": "polar", "rExpression": str(r_expr), "latex": sp.latex(r_expr), "points": points}], "integralOverlay": None}


def _edge_cross(p1: Tuple[float, float, Optional[float]], p2: Tuple[float, float, Optional[float]]) -> Optional[Tuple[float, float]]:
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    if z1 is None or z2 is None:
        return None
    if z1 == 0:
        return (x1, y1)
    if z2 == 0:
        return (x2, y2)
    if z1 * z2 > 0:
        return None
    denominator = abs(z1) + abs(z2)
    ratio = abs(z1) / denominator if denominator else 0.5
    return (x1 + (x2 - x1) * ratio, y1 + (y2 - y1) * ratio)


def _sample_implicit(payload: GraphInput) -> Dict[str, Any]:
    parser = RestrictedSympyParser(["x", "y", *payload.parameters.keys()])
    x, y = parser.symbol("x"), parser.symbol("y")
    text = payload.expression
    if "=" in text:
        eq = parser.equation(text)
        if not isinstance(eq, sp.Equality):
            raise ValueError("Implicit graph must be an expression or equation.")
        expr = eq.lhs - eq.rhs
    else:
        expr = parser.parse(text)
    params = _parameter_substitutions(parser, payload.parameters)
    xs = _linspace(payload.xMin, payload.xMax, payload.gridSize)
    ys = _linspace(payload.yMin, payload.yMax, payload.gridSize)
    values: List[List[Optional[float]]] = []
    for yv in ys:
        row = []
        for xv in xs:
            row.append(_safe_real(expr, {x: xv, y: yv, **params}))
        values.append(row)

    segments: List[List[Dict[str, float]]] = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            corners = [
                (xs[i], ys[j], values[j][i]),
                (xs[i + 1], ys[j], values[j][i + 1]),
                (xs[i + 1], ys[j + 1], values[j + 1][i + 1]),
                (xs[i], ys[j + 1], values[j + 1][i]),
            ]
            hits = []
            for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
                hit = _edge_cross(corners[a], corners[b])
                if hit is not None and all(abs(hit[0] - h[0]) > 1e-10 or abs(hit[1] - h[1]) > 1e-10 for h in hits):
                    hits.append(hit)
            if len(hits) >= 2:
                segments.append([_point(*hits[0]), _point(*hits[1])])
                if len(hits) >= 4:
                    segments.append([_point(*hits[2]), _point(*hits[3])])
    return {"series": [{"role": "implicit", "expression": str(expr), "latex": sp.latex(sp.Eq(expr, 0)), "segments": segments}], "integralOverlay": None}


def graph(payload: GraphInput) -> Dict[str, Any]:
    try:
        if payload.mode == "cartesian":
            content = _sample_cartesian(payload)
        elif payload.mode == "parametric":
            content = _sample_parametric(payload)
        elif payload.mode == "polar":
            content = _sample_polar(payload)
        else:
            content = _sample_implicit(payload)
        source = {
            "mode": payload.mode,
            "expression": payload.expression,
            "expressionY": payload.expressionY,
            "parameters": payload.parameters,
            "viewport": {"xMin": payload.xMin, "xMax": payload.xMax, "yMin": payload.yMin, "yMax": payload.yMax},
            "samples": payload.samples,
        }
        return {"ok": True, "result": _graph_object(payload.mode, source, content)}
    except (ValueError, TypeError, sp.SympifyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _finite_real_roots(expr: sp.Expr, variable: sp.Symbol, lo: float, hi: float, samples: int, params: Dict[sp.Symbol, float]) -> List[float]:
    substituted = sp.simplify(expr.subs(params))
    candidates: List[float] = []
    try:
        solved = sp.solveset(substituted, variable, domain=sp.Interval(lo, hi))
        if isinstance(solved, sp.FiniteSet):
            for item in solved:
                val = _safe_real(item, {})
                if val is not None and lo - 1e-9 <= val <= hi + 1e-9:
                    candidates.append(val)
    except Exception:
        pass

    xs = _linspace(lo, hi, samples)
    vals = [_safe_real(substituted, {variable: xv}) for xv in xs]
    for i in range(len(xs) - 1):
        a, b, fa, fb = xs[i], xs[i + 1], vals[i], vals[i + 1]
        if fa is None or fb is None:
            continue
        if abs(fa) < 1e-9:
            candidates.append(a)
        if fa * fb < 0:
            left, right, fl, fr = a, b, fa, fb
            for _ in range(45):
                mid = (left + right) / 2
                fm = _safe_real(substituted, {variable: mid})
                if fm is None:
                    break
                if abs(fm) < 1e-12:
                    left = right = mid
                    break
                if fl * fm <= 0:
                    right, fr = mid, fm
                else:
                    left, fl = mid, fm
            candidates.append((left + right) / 2)
    unique: List[float] = []
    for value in sorted(candidates):
        if not unique or abs(value - unique[-1]) > 1e-6:
            unique.append(value)
    return unique[:100]


def analyze(payload: AnalysisInput) -> Dict[str, Any]:
    try:
        parser = RestrictedSympyParser([payload.variable, *payload.parameters.keys()])
        variable = parser.symbol(payload.variable)
        expr = parser.parse(payload.expression)
        params = _parameter_substitutions(parser, payload.parameters)
        results: Dict[str, Any] = {}
        if "roots" in payload.analyses:
            roots = _finite_real_roots(expr, variable, payload.xMin, payload.xMax, payload.samples, params)
            results["roots"] = [{"x": x, "y": 0.0} for x in roots]
        if "extrema" in payload.analyses:
            derivative = sp.diff(expr, variable)
            critical = _finite_real_roots(derivative, variable, payload.xMin, payload.xMax, payload.samples, params)
            extrema = []
            second = sp.diff(expr, variable, 2)
            for xv in critical:
                yv = _safe_real(expr, {variable: xv, **params})
                curvature = _safe_real(second, {variable: xv, **params})
                if yv is None:
                    continue
                classification = "minimum" if curvature is not None and curvature > 1e-8 else "maximum" if curvature is not None and curvature < -1e-8 else "stationary"
                extrema.append({"x": round(xv, 12), "y": round(yv, 12), "classification": classification})
            results["extrema"] = extrema
        if "intersections" in payload.analyses:
            other = parser.parse(payload.comparisonExpression or "0")
            roots = _finite_real_roots(expr - other, variable, payload.xMin, payload.xMax, payload.samples, params)
            intersections = []
            for xv in roots:
                yv = _safe_real(expr, {variable: xv, **params})
                if yv is not None:
                    intersections.append({"x": round(xv, 12), "y": round(yv, 12)})
            results["intersections"] = intersections
        record = _graph_object("analysis", {"expression": payload.expression, "comparisonExpression": payload.comparisonExpression, "variable": payload.variable, "parameters": payload.parameters, "xMin": payload.xMin, "xMax": payload.xMax}, {"analysis": results})
        return {"ok": True, "result": record}
    except (ValueError, TypeError, sp.SympifyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def vector_field(payload: VectorFieldInput) -> Dict[str, Any]:
    try:
        parser = RestrictedSympyParser(["x", "y", *payload.parameters.keys()])
        x, y = parser.symbol("x"), parser.symbol("y")
        u_expr, v_expr = parser.parse(payload.uExpression), parser.parse(payload.vExpression)
        params = _parameter_substitutions(parser, payload.parameters)
        arrows = []
        for yv in _linspace(payload.yMin, payload.yMax, payload.gridSize):
            for xv in _linspace(payload.xMin, payload.xMax, payload.gridSize):
                u = _safe_real(u_expr, {x: xv, y: yv, **params})
                v = _safe_real(v_expr, {x: xv, y: yv, **params})
                if u is None or v is None:
                    continue
                magnitude = math.hypot(u, v)
                du, dv = u, v
                if payload.normalize and magnitude > 1e-12:
                    du, dv = u / magnitude, v / magnitude
                arrows.append({"x": round(xv, 12), "y": round(yv, 12), "u": round(du, 12), "v": round(dv, 12), "magnitude": round(magnitude, 12)})
        record = _graph_object("vector-field", {"uExpression": payload.uExpression, "vExpression": payload.vExpression, "parameters": payload.parameters, "viewport": {"xMin": payload.xMin, "xMax": payload.xMax, "yMin": payload.yMin, "yMax": payload.yMax}}, {"arrows": arrows, "normalized": payload.normalize})
        return {"ok": True, "result": record}
    except (ValueError, TypeError, sp.SympifyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def surface(payload: SurfaceInput) -> Dict[str, Any]:
    try:
        parser = RestrictedSympyParser(["x", "y", *payload.parameters.keys()])
        x, y = parser.symbol("x"), parser.symbol("y")
        expr = parser.parse(payload.expression)
        params = _parameter_substitutions(parser, payload.parameters)
        xs = _linspace(payload.xMin, payload.xMax, payload.gridSize)
        ys = _linspace(payload.yMin, payload.yMax, payload.gridSize)
        rows = []
        z_values = []
        for yv in ys:
            row = []
            for xv in xs:
                zv = _safe_real(expr, {x: xv, y: yv, **params})
                row.append(None if zv is None else round(zv, 12))
                if zv is not None:
                    z_values.append(zv)
            rows.append(row)
        z_range = {"min": min(z_values), "max": max(z_values)} if z_values else {"min": None, "max": None}
        record = _graph_object("surface-3d", {"expression": payload.expression, "parameters": payload.parameters, "xMin": payload.xMin, "xMax": payload.xMax, "yMin": payload.yMin, "yMax": payload.yMax}, {"x": xs, "y": ys, "z": rows, "zRange": z_range, "latex": sp.latex(expr)})
        return {"ok": True, "result": record}
    except (ValueError, TypeError, sp.SympifyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-graph-mathematics-status/1.0",
        "version": VERSION,
        "foundation": "v5.1 restricted SymPy CAS",
        "capabilities": [
            "cartesian-functions", "parametric-curves", "polar-curves", "implicit-equations",
            "contour-extraction", "live-parameters", "derivative-overlays", "definite-integral-overlays",
            "roots", "extrema", "intersections", "vector-fields", "3d-surfaces", "canonical-graph-objects",
        ],
        "limits": {"maxSamples": MAX_SAMPLES, "maxImplicitGrid": MAX_IMPLICIT_GRID, "maxVectorGrid": MAX_VECTOR_GRID, "maxSurfaceGrid": MAX_SURFACE_GRID, "maxParameters": MAX_PARAMETERS},
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
    }


@router.get("/status")
def status_endpoint() -> Dict[str, Any]:
    return status_record()


@router.post("/graph")
def graph_endpoint(payload: GraphInput) -> Dict[str, Any]:
    return graph(payload)


@router.post("/analyze")
def analyze_endpoint(payload: AnalysisInput) -> Dict[str, Any]:
    return analyze(payload)


@router.post("/vector-field")
def vector_field_endpoint(payload: VectorFieldInput) -> Dict[str, Any]:
    return vector_field(payload)


@router.post("/surface")
def surface_endpoint(payload: SurfaceInput) -> Dict[str, Any]:
    return surface(payload)

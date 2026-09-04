"""Workbench v5.4.0 — Advanced Graph Mathematics II.

Adds multi-expression graph objects, per-series domain restrictions, pairwise
intersections, exact/approximate analysis markers, tangent/normal construction,
asymptote/discontinuity inspection, inequality regions, and value tables while
preserving the v5.1 restricted AST -> SymPy security boundary.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Tuple

import sympy as sp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.v510 import RestrictedSympyParser, content_hash
from app.v520 import _finite_real_roots, _linspace, _parameter_substitutions, _safe_real

VERSION = "5.4.0"
GRAPH_SCHEMA = "sc-workbench-advanced-graph-object/2.0"
MAX_SERIES = 8
MAX_SAMPLES = 1001
MAX_TABLE_ROWS = 201
MAX_PARAMETERS = 8

router = APIRouter(prefix="/v540", tags=["workbench-v540-advanced-graph-mathematics"])


def _validate_range(lo: float, hi: float, label: str) -> None:
    if not (math.isfinite(lo) and math.isfinite(hi)) or lo >= hi:
        raise ValueError(f"{label} minimum must be finite and less than maximum.")


def _point(x: float, y: float) -> Dict[str, float]:
    return {"x": round(float(x), 12), "y": round(float(y), 12)}


def _record(kind: str, source: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "schema": GRAPH_SCHEMA,
        "version": VERSION,
        "kind": kind,
        "source": source,
        **payload,
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
    }
    value["graphObjectHash"] = content_hash(value)
    return value


class SeriesSpec(BaseModel):
    expression: str
    label: str = ""
    visible: bool = True
    domainMin: Optional[float] = None
    domainMax: Optional[float] = None
    derivativeOrder: int = Field(default=0, ge=0, le=2)

    @model_validator(mode="after")
    def validate_domain(self):
        if (self.domainMin is None) != (self.domainMax is None):
            raise ValueError("Series domain restriction requires both domainMin and domainMax.")
        if self.domainMin is not None:
            _validate_range(self.domainMin, self.domainMax, "series domain")
        return self


class RegionSpec(BaseModel):
    expression: str
    comparator: Literal["lt", "lte", "gt", "gte"] = "lte"
    level: float = 0.0
    label: str = "region"


class MultiGraphInput(BaseModel):
    series: List[SeriesSpec] = Field(min_length=1, max_length=MAX_SERIES)
    xMin: float = -10.0
    xMax: float = 10.0
    yMin: float = -10.0
    yMax: float = 10.0
    samples: int = Field(default=501, ge=25, le=MAX_SAMPLES)
    parameters: Dict[str, float] = Field(default_factory=dict)
    analyses: List[Literal["roots", "extrema", "intersections", "asymptotes", "discontinuities"]] = Field(
        default_factory=lambda: ["roots", "extrema", "intersections"]
    )
    tangentAt: Optional[float] = None
    includeNormal: bool = False
    region: Optional[RegionSpec] = None

    @model_validator(mode="after")
    def validate_graph(self):
        _validate_range(self.xMin, self.xMax, "x range")
        _validate_range(self.yMin, self.yMax, "y range")
        if len(self.parameters) > MAX_PARAMETERS:
            raise ValueError(f"At most {MAX_PARAMETERS} parameters are supported.")
        if self.tangentAt is not None and not math.isfinite(self.tangentAt):
            raise ValueError("Tangent x must be finite.")
        return self


class TableInput(BaseModel):
    series: List[SeriesSpec] = Field(min_length=1, max_length=MAX_SERIES)
    xMin: float = -5.0
    xMax: float = 5.0
    rows: int = Field(default=21, ge=2, le=MAX_TABLE_ROWS)
    parameters: Dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_table(self):
        _validate_range(self.xMin, self.xMax, "table x range")
        if len(self.parameters) > MAX_PARAMETERS:
            raise ValueError(f"At most {MAX_PARAMETERS} parameters are supported.")
        return self


def _domain_bounds(spec: SeriesSpec, lo: float, hi: float) -> Tuple[float, float]:
    if spec.domainMin is None:
        return lo, hi
    return max(lo, spec.domainMin), min(hi, spec.domainMax)


def _in_domain(spec: SeriesSpec, x: float) -> bool:
    if spec.domainMin is None:
        return True
    return spec.domainMin - 1e-12 <= x <= spec.domainMax + 1e-12


def _finite_set_values(value: Any, lo: float, hi: float) -> List[float]:
    out: List[float] = []
    if isinstance(value, sp.FiniteSet):
        for item in value:
            n = _safe_real(item, {})
            if n is not None and lo - 1e-9 <= n <= hi + 1e-9:
                out.append(n)
    return sorted(set(round(x, 12) for x in out))


def _discontinuities(expr: sp.Expr, x: sp.Symbol, lo: float, hi: float, params: Dict[sp.Symbol, float], samples: int) -> List[Dict[str, Any]]:
    substituted = sp.simplify(expr.subs(params))
    candidates: List[float] = []
    try:
        singular = sp.singularities(substituted, x)
        candidates.extend(_finite_set_values(singular, lo, hi))
    except Exception:
        pass
    try:
        denominator = sp.together(substituted).as_numer_denom()[1]
        if denominator != 1:
            candidates.extend(_finite_real_roots(denominator, x, lo, hi, samples, {}))
    except Exception:
        pass

    unique: List[float] = []
    for value in sorted(candidates):
        if not unique or abs(value - unique[-1]) > 1e-7:
            unique.append(value)

    output = []
    for value in unique[:50]:
        left = right = None
        try:
            left = sp.limit(substituted, x, value, dir="-")
        except Exception:
            pass
        try:
            right = sp.limit(substituted, x, value, dir="+")
        except Exception:
            pass
        left_num = _safe_real(left, {}) if left is not None else None
        right_num = _safe_real(right, {}) if right is not None else None
        infinite = any(v in (sp.oo, -sp.oo, sp.zoo) or getattr(v, "is_infinite", False) for v in (left, right) if v is not None)
        classification = "vertical-asymptote" if infinite else "removable-or-jump"
        output.append({
            "x": round(value, 12),
            "classification": classification,
            "leftLimit": None if left_num is None else round(left_num, 12),
            "rightLimit": None if right_num is None else round(right_num, 12),
        })
    return output


def _horizontal_asymptotes(expr: sp.Expr, x: sp.Symbol, params: Dict[sp.Symbol, float]) -> List[Dict[str, Any]]:
    substituted = sp.simplify(expr.subs(params))
    output: List[Dict[str, Any]] = []
    for direction, point in (("+∞", sp.oo), ("−∞", -sp.oo)):
        try:
            limit = sp.limit(substituted, x, point)
            y = _safe_real(limit, {})
            if y is not None:
                output.append({"axis": "horizontal", "direction": direction, "y": round(y, 12)})
        except Exception:
            pass
    unique: List[Dict[str, Any]] = []
    seen = set()
    for item in output:
        key = round(item["y"], 10)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _sample_expression(expr: sp.Expr, x: sp.Symbol, spec: SeriesSpec, payload: MultiGraphInput, params: Dict[sp.Symbol, float]) -> List[Optional[Dict[str, float]]]:
    points: List[Optional[Dict[str, float]]] = []
    for xv in _linspace(payload.xMin, payload.xMax, payload.samples):
        if not _in_domain(spec, xv):
            points.append(None)
            continue
        yv = _safe_real(expr, {x: xv, **params})
        points.append(_point(xv, yv) if yv is not None else None)
    return points


def _series_analysis(expr: sp.Expr, x: sp.Symbol, spec: SeriesSpec, payload: MultiGraphInput, params: Dict[sp.Symbol, float]) -> Dict[str, Any]:
    lo, hi = _domain_bounds(spec, payload.xMin, payload.xMax)
    if lo >= hi:
        return {"roots": [], "extrema": [], "discontinuities": [], "asymptotes": []}
    result: Dict[str, Any] = {}
    if "roots" in payload.analyses:
        result["roots"] = [_point(v, 0) for v in _finite_real_roots(expr, x, lo, hi, payload.samples, params)]
    if "extrema" in payload.analyses:
        derivative = sp.diff(expr, x)
        second = sp.diff(expr, x, 2)
        extrema = []
        for xv in _finite_real_roots(derivative, x, lo, hi, payload.samples, params):
            yv = _safe_real(expr, {x: xv, **params})
            curvature = _safe_real(second, {x: xv, **params})
            if yv is None:
                continue
            classification = "minimum" if curvature is not None and curvature > 1e-8 else "maximum" if curvature is not None and curvature < -1e-8 else "stationary"
            extrema.append({"x": round(xv, 12), "y": round(yv, 12), "classification": classification})
        result["extrema"] = extrema
    discontinuities: List[Dict[str, Any]] = []
    if "discontinuities" in payload.analyses or "asymptotes" in payload.analyses:
        discontinuities = _discontinuities(expr, x, lo, hi, params, payload.samples)
    if "discontinuities" in payload.analyses:
        result["discontinuities"] = discontinuities
    if "asymptotes" in payload.analyses:
        vertical = [{"axis": "vertical", "x": d["x"]} for d in discontinuities if d["classification"] == "vertical-asymptote"]
        result["asymptotes"] = vertical + _horizontal_asymptotes(expr, x, params)
    return result


def _line_from_point_slope(x0: float, y0: float, slope: float, lo: float, hi: float, role: str) -> Dict[str, Any]:
    if not math.isfinite(slope):
        return {"role": role, "vertical": True, "x": round(x0, 12), "points": [_point(x0, -1e6), _point(x0, 1e6)]}
    return {
        "role": role,
        "slope": round(slope, 12),
        "point": _point(x0, y0),
        "points": [_point(lo, y0 + slope * (lo - x0)), _point(hi, y0 + slope * (hi - x0))],
    }


def _region_intervals(region: RegionSpec, parser: RestrictedSympyParser, x: sp.Symbol, payload: MultiGraphInput, params: Dict[sp.Symbol, float]) -> Dict[str, Any]:
    expr = parser.parse(region.expression)
    level = float(region.level)
    xs = _linspace(payload.xMin, payload.xMax, min(payload.samples, 801))

    def satisfied(v: Optional[float]) -> bool:
        if v is None:
            return False
        if region.comparator == "lt":
            return v < level
        if region.comparator == "lte":
            return v <= level
        if region.comparator == "gt":
            return v > level
        return v >= level

    flags = [satisfied(_safe_real(expr, {x: xv, **params})) for xv in xs]
    intervals = []
    start = None
    for idx, flag in enumerate(flags):
        if flag and start is None:
            start = xs[idx]
        if start is not None and (not flag or idx == len(flags) - 1):
            end_index = idx if flag and idx == len(flags) - 1 else max(0, idx - 1)
            intervals.append({"xMin": round(start, 12), "xMax": round(xs[end_index], 12)})
            start = None
    return {
        "label": region.label,
        "expression": str(expr),
        "latex": sp.latex(expr),
        "comparator": region.comparator,
        "level": level,
        "intervals": intervals,
    }


def multi_graph(payload: MultiGraphInput) -> Dict[str, Any]:
    try:
        symbols = ["x", *payload.parameters.keys()]
        parser = RestrictedSympyParser(symbols)
        x = parser.symbol("x")
        params = _parameter_substitutions(parser, payload.parameters)

        series_out = []
        analyses_out: Dict[str, Any] = {"series": [], "intersections": []}
        parsed: List[Tuple[SeriesSpec, sp.Expr]] = []

        for idx, spec in enumerate(payload.series):
            expr = parser.parse(spec.expression)
            parsed.append((spec, expr))
            label = spec.label.strip() or f"f{idx + 1}(x)"
            points = _sample_expression(expr, x, spec, payload, params) if spec.visible else []
            derived = None
            if spec.derivativeOrder:
                derivative = sp.diff(expr, x, spec.derivativeOrder)
                derived = {
                    "order": spec.derivativeOrder,
                    "expression": str(derivative),
                    "latex": sp.latex(derivative),
                    "points": _sample_expression(derivative, x, spec, payload, params) if spec.visible else [],
                }
            series_out.append({
                "id": idx,
                "label": label,
                "expression": str(expr),
                "latex": sp.latex(expr),
                "visible": spec.visible,
                "domain": None if spec.domainMin is None else {"min": spec.domainMin, "max": spec.domainMax},
                "points": points,
                "derivative": derived,
            })
            analyses_out["series"].append({"id": idx, "label": label, **_series_analysis(expr, x, spec, payload, params)})

        if "intersections" in payload.analyses:
            for i in range(len(parsed)):
                spec_a, expr_a = parsed[i]
                if not spec_a.visible:
                    continue
                for j in range(i + 1, len(parsed)):
                    spec_b, expr_b = parsed[j]
                    if not spec_b.visible:
                        continue
                    lo = max(_domain_bounds(spec_a, payload.xMin, payload.xMax)[0], _domain_bounds(spec_b, payload.xMin, payload.xMax)[0])
                    hi = min(_domain_bounds(spec_a, payload.xMin, payload.xMax)[1], _domain_bounds(spec_b, payload.xMin, payload.xMax)[1])
                    if lo >= hi:
                        continue
                    roots = _finite_real_roots(expr_a - expr_b, x, lo, hi, payload.samples, params)
                    points = []
                    for xv in roots[:50]:
                        yv = _safe_real(expr_a, {x: xv, **params})
                        if yv is not None:
                            points.append(_point(xv, yv))
                    if points:
                        analyses_out["intersections"].append({"series": [i, j], "points": points})

        constructions: List[Dict[str, Any]] = []
        if payload.tangentAt is not None and parsed:
            spec, expr = parsed[0]
            x0 = payload.tangentAt
            if _in_domain(spec, x0):
                y0 = _safe_real(expr, {x: x0, **params})
                slope = _safe_real(sp.diff(expr, x), {x: x0, **params})
                if y0 is not None and slope is not None:
                    constructions.append(_line_from_point_slope(x0, y0, slope, payload.xMin, payload.xMax, "tangent"))
                    if payload.includeNormal:
                        normal_slope = math.inf if abs(slope) < 1e-12 else -1.0 / slope
                        constructions.append(_line_from_point_slope(x0, y0, normal_slope, payload.xMin, payload.xMax, "normal"))

        region_out = _region_intervals(payload.region, parser, x, payload, params) if payload.region else None
        source = {
            "series": [item.model_dump() for item in payload.series],
            "viewport": {"xMin": payload.xMin, "xMax": payload.xMax, "yMin": payload.yMin, "yMax": payload.yMax},
            "samples": payload.samples,
            "parameters": payload.parameters,
            "analyses": payload.analyses,
            "tangentAt": payload.tangentAt,
            "includeNormal": payload.includeNormal,
            "region": payload.region.model_dump() if payload.region else None,
        }
        return {"ok": True, "result": _record("advanced-cartesian", source, {
            "series": series_out,
            "analysis": analyses_out,
            "constructions": constructions,
            "region": region_out,
            "piecewiseByDomainRestriction": True,
        })}
    except (ValueError, TypeError, sp.SympifyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def table(payload: TableInput) -> Dict[str, Any]:
    try:
        parser = RestrictedSympyParser(["x", *payload.parameters.keys()])
        x = parser.symbol("x")
        params = _parameter_substitutions(parser, payload.parameters)
        parsed = [(spec, parser.parse(spec.expression)) for spec in payload.series]
        rows = []
        for xv in _linspace(payload.xMin, payload.xMax, payload.rows):
            values = []
            for spec, expr in parsed:
                yv = _safe_real(expr, {x: xv, **params}) if _in_domain(spec, xv) else None
                values.append(None if yv is None else round(yv, 12))
            rows.append({"x": round(xv, 12), "values": values})
        labels = [spec.label.strip() or f"f{i+1}(x)" for i, spec in enumerate(payload.series)]
        return {"ok": True, "result": _record("value-table", {
            "series": [item.model_dump() for item in payload.series],
            "xMin": payload.xMin,
            "xMax": payload.xMax,
            "rows": payload.rows,
            "parameters": payload.parameters,
        }, {"labels": labels, "rows": rows})}
    except (ValueError, TypeError, sp.SympifyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-advanced-graph-status/1.0",
        "version": VERSION,
        "foundation": "v5.1 restricted SymPy CAS + v5.2 graph mathematics",
        "capabilities": [
            "multi-expression-stack", "per-series-domain-restrictions", "piecewise-by-domain",
            "derivative-series", "roots", "extrema", "pairwise-intersections",
            "tangent-lines", "normal-lines", "discontinuity-analysis", "vertical-asymptotes",
            "horizontal-asymptotes", "inequality-regions", "value-tables", "parameterized-series",
            "zoom", "pan", "trace", "fullscreen", "canonical-advanced-graph-objects",
        ],
        "limits": {
            "maxSeries": MAX_SERIES,
            "maxSamples": MAX_SAMPLES,
            "maxTableRows": MAX_TABLE_ROWS,
            "maxParameters": MAX_PARAMETERS,
        },
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
    }


@router.get("/status")
def status() -> Dict[str, Any]:
    return status_record()


@router.post("/multi-graph")
def multi_graph_endpoint(payload: MultiGraphInput) -> Dict[str, Any]:
    return multi_graph(payload)


@router.post("/table")
def table_endpoint(payload: TableInput) -> Dict[str, Any]:
    return table(payload)

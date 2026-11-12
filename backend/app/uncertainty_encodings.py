"""SC-FIG-05.3 — uncertainty-first encodings drawn only from runtime-computed records.

The Workspace runtimes compute regression bands (R ``stats::predict.lm``) and ensemble quantile fans (the
uncertainty runtime); the Workspace export copies them after checking them. This module re-checks those records
and turns them into Plotly traces, legend entries and table columns. It never computes a band, a quantile or an
interval from point estimates: a record that is missing is reported as unavailable, and a record that is
inconsistent is refused.

Checks (all on the runtime's own numbers):

* origin ``computedBy: runtime``; level, method, distribution and degrees of freedom present;
* x strictly increasing; ``lower <= fit <= upper``; Student-t bands symmetric about the fit;
* with both bands: same level and x, prediction contains confidence, and the residual variance implied by
  ``(prediction half-width^2 - confidence half-width^2) / t^2`` is the same at every x (``sigma^2`` of one model);
* optional ``linearFit``: the fit equals the exported intercept + slope * x;
* fans: at least five members, increasing central levels, ``min <= wider <= narrower <= median`` at every step.
"""
from __future__ import annotations

import html
import math
from typing import Any, Dict, List, Optional

BAND_KEYS = {"semantics", "predictor", "level", "method", "distribution", "degreesOfFreedom", "evaluatedAt", "computedBy", "points"}
FAN_KEYS = {"semantics", "centralLevels", "memberCount", "method", "evaluatedAt", "computedBy", "steps"}
MAX_POINTS = 500
# Okabe-Ito blue for every uncertainty area: one hue, so bands differ by opacity, outline and label, never by
# hue alone (colour-vision safe and legible in greyscale).
BAND_RGB = (0, 114, 178)
FIT_COLOUR = "#000000"
BAND_STYLE = {"prediction-band": {"alpha": 0.14, "dash": "dash", "width": 1.2},
              "confidence-band": {"alpha": 0.34, "dash": "solid", "width": 0.0}}
FAN_ALPHA = (0.42, 0.27, 0.16, 0.10)  # innermost level first


class UncertaintyRecordError(ValueError):
    pass


def _num(v: Any) -> bool:
    return not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(v)


def rgba(alpha: float) -> str:
    return f"rgba({BAND_RGB[0]},{BAND_RGB[1]},{BAND_RGB[2]},{alpha:.2f})"


def _tol(*vals: float) -> float:
    return 1e-8 * max([1.0] + [abs(v) for v in vals])


def check_bands(bands: Any, at: str, values: Optional[Dict[str, Any]] = None,
                linear_fit: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(bands, list) or not 1 <= len(bands) <= 2:
        raise UncertaintyRecordError(f"{at}: bands must be the export's list of one or two runtime band records")
    out, by = [], {}
    for b in bands:
        if not isinstance(b, dict) or set(b) != BAND_KEYS or b.get("computedBy") != "runtime":
            raise UncertaintyRecordError(f"{at}: a band is not the runtime's band record (computedBy runtime, level, method, df, points)")
        sem = b["semantics"]
        if sem not in BAND_STYLE or sem in by:
            raise UncertaintyRecordError(f"{at}: unknown or repeated band semantics {sem!r}")
        level, df = b["level"], b["degreesOfFreedom"]
        if not (_num(level) and 0.5 <= level < 1 and _num(df) and df >= 1 and isinstance(b["method"], str) and b["method"].strip()
                and b["distribution"] == "Student t" and isinstance(b["predictor"], str) and b["predictor"]):
            raise UncertaintyRecordError(f"{at}: {sem} needs a level in [0.5, 1), df >= 1, a method and the Student t distribution")
        pts = b["points"]
        if not isinstance(pts, list) or not 2 <= len(pts) <= MAX_POINTS:
            raise UncertaintyRecordError(f"{at}: {sem} needs 2-{MAX_POINTS} points")
        prev = None
        for p in pts:
            if not (isinstance(p, list) and len(p) == 4 and all(_num(v) for v in p)):
                raise UncertaintyRecordError(f"{at}: {sem} point is not [x, fit, lower, upper]")
            x, fit, lo, hi = p
            if prev is not None and x <= prev:
                raise UncertaintyRecordError(f"{at}: {sem} x values must be strictly increasing")
            if not lo <= fit <= hi:
                raise UncertaintyRecordError(f"{at}: {sem} lower <= fit <= upper fails at x={x:g}")
            if abs((hi - fit) - (fit - lo)) > _tol(fit, hi, lo):
                raise UncertaintyRecordError(f"{at}: {sem} is not symmetric about the fit at x={x:g} (Student t bands are)")
            prev = x
        by[sem] = b
        out.append(b)
    consistency = ["symmetric-student-t"]
    conf, pred = by.get("confidence-band"), by.get("prediction-band")
    if conf and pred:
        if conf["level"] != pred["level"] or conf["degreesOfFreedom"] != pred["degreesOfFreedom"] \
                or [p[0] for p in conf["points"]] != [p[0] for p in pred["points"]]:
            raise UncertaintyRecordError(f"{at}: confidence and prediction bands must share level, df and x")
        from scipy.stats import t as student_t
        q = float(student_t.ppf((1 + conf["level"]) / 2, conf["degreesOfFreedom"]))
        sig2 = []
        for c, p in zip(conf["points"], pred["points"]):
            if abs(c[1] - p[1]) > _tol(c[1]) or not (p[2] <= c[2] and c[3] <= p[3]):
                raise UncertaintyRecordError(f"{at}: the prediction band must share the fit and contain the confidence band")
            hc, hp = (c[3] - c[2]) / 2, (p[3] - p[2]) / 2
            sig2.append((hp * hp - hc * hc) / (q * q))
        if min(sig2) <= 0 or max(sig2) - min(sig2) > 1e-7 * max(1.0, max(sig2)):
            raise UncertaintyRecordError(f"{at}: the bands imply different residual variances at different x; not one model")
        consistency.append("prediction-confidence-residual-variance-constant")
    if linear_fit:
        a, b_ = (values or {}).get(linear_fit.get("interceptKey", "")), (values or {}).get(linear_fit.get("slopeKey", ""))
        if not (_num(a) and _num(b_)):
            raise UncertaintyRecordError(f"{at}: linearFit keys are not finite exported values")
        for band in out:
            for x, fit, _lo, _hi in band["points"]:
                if abs(fit - (a + b_ * x)) > _tol(fit, a, b_ * x):
                    raise UncertaintyRecordError(f"{at}: the band fit differs from the exported intercept + slope * x at x={x:g}")
        consistency.append("fit-equals-exported-coefficients")
    order = {"prediction-band": 0, "confidence-band": 1}  # wider first so the narrower band is drawn on top
    return {"kind": "band", "bands": sorted(out, key=lambda b: order[b["semantics"]]), "consistency": consistency}


def check_fan(fan: Any, at: str) -> Dict[str, Any]:
    if not isinstance(fan, dict) or set(fan) != FAN_KEYS or fan.get("computedBy") != "runtime" \
            or fan.get("semantics") != "ensemble-quantile-fan":
        raise UncertaintyRecordError(f"{at}: quantileBands must be the runtime's ensemble-quantile-fan record")
    levels, members, steps = fan["centralLevels"], fan["memberCount"], fan["steps"]
    if not (isinstance(levels, list) and 1 <= len(levels) <= 4 and all(_num(v) and 0 < v < 1 for v in levels)
            and levels == sorted(set(levels))):
        raise UncertaintyRecordError(f"{at}: fan central levels must be 1-4 increasing values in (0, 1)")
    if not isinstance(members, int) or isinstance(members, bool) or members < 5:
        raise UncertaintyRecordError(f"{at}: a fan needs the runtime's member count (at least 5)")
    if not (isinstance(fan["method"], str) and fan["method"].strip()):
        raise UncertaintyRecordError(f"{at}: a fan needs the runtime's method")
    if not isinstance(steps, list) or not 2 <= len(steps) <= MAX_POINTS:
        raise UncertaintyRecordError(f"{at}: a fan needs 2-{MAX_POINTS} steps")
    prev = None
    for st in steps:
        if not isinstance(st, dict) or set(st) != {"x", "median", "min", "max", "bands"} \
                or not all(_num(st[k]) for k in ("x", "median", "min", "max")) \
                or not isinstance(st["bands"], list) or len(st["bands"]) != len(levels):
            raise UncertaintyRecordError(f"{at}: a fan step is not {{x, median, min, max, bands}}")
        if prev is not None and st["x"] <= prev:
            raise UncertaintyRecordError(f"{at}: fan steps must be strictly increasing")
        lo_in = hi_in = st["median"]
        for pair in st["bands"]:
            if not (isinstance(pair, list) and len(pair) == 2 and all(_num(v) for v in pair)
                    and st["min"] <= pair[0] <= lo_in and hi_in <= pair[1] <= st["max"]):
                raise UncertaintyRecordError(f"{at}: fan bands are not nested around the median at x={st['x']:g}")
            lo_in, hi_in = pair
        prev = st["x"]
    return {"kind": "fan", "fan": fan, "consistency": ["nested-quantiles", "within-member-range"]}


def _num_text(v: float) -> str:
    return f"{v:.6g}"


def band_label(b: Dict[str, Any]) -> str:
    kind = "prediction" if b["semantics"] == "prediction-band" else "confidence"
    return (f"{b['level'] * 100:g}% {kind} band (Student t, df {b['degreesOfFreedom']:g}; computed by the Workspace runtime)")


def fan_label(level: float, members: int) -> str:
    return f"central {level * 100:g}% of {members} ensemble members (empirical quantiles; computed by the Workspace runtime)"


def band_traces(rec: Dict[str, Any], axes: Dict[str, str], unit: str, panel_id: str, fit_label: str,
                record_sha: str = "") -> List[Dict[str, Any]]:
    traces = []
    for i, b in enumerate(rec["bands"]):
        st = BAND_STYLE[b["semantics"]]
        xs = [p[0] for p in b["points"]]
        traces.append({
            "type": "scatter", **axes, "mode": "lines", "fill": "toself", "fillcolor": rgba(st["alpha"]),
            "x": xs + xs[::-1], "y": [p[3] for p in b["points"]] + [p[2] for p in b["points"]][::-1],
            "line": {"color": rgba(min(1.0, st["alpha"] + 0.5)), "width": st["width"], "dash": st["dash"]},
            "name": html.escape(band_label(b)), "hoverinfo": "skip", "showlegend": True,
            "meta": {"scUncertainty": {"panelId": panel_id, "role": "band", "semantics": b["semantics"], "level": b["level"],
                                       "recordSha256": record_sha}},
        })
    first = rec["bands"][-1]
    others = rec["bands"]
    custom = [[_num_text(b["points"][j][2]) + " to " + _num_text(b["points"][j][3]) for b in others] for j in range(len(first["points"]))]
    hover = "x: %{x}<br>" + html.escape(fit_label) + ": %{y} " + html.escape(unit) + "".join(
        f"<br>{b['level'] * 100:g}% {'prediction' if b['semantics'] == 'prediction-band' else 'confidence'}: %{{customdata[{k}]}}"
        for k, b in enumerate(others)) + "<extra></extra>"
    traces.append({
        "type": "scatter", **axes, "mode": "lines", "x": [p[0] for p in first["points"]], "y": [p[1] for p in first["points"]],
        "line": {"color": FIT_COLOUR, "width": 2}, "name": html.escape(fit_label + " (runtime fit)"),
        "customdata": custom, "hovertemplate": hover,
        "meta": {"scUncertainty": {"panelId": panel_id, "role": "fit"}},
    })
    return traces


def fan_traces(rec: Dict[str, Any], axes: Dict[str, str], unit: str, panel_id: str, median_label: str,
               record_sha: str = "") -> List[Dict[str, Any]]:
    fan, traces = rec["fan"], []
    xs = [s["x"] for s in fan["steps"]]
    n = len(fan["centralLevels"])
    for k in range(n - 1, -1, -1):  # widest first
        level = fan["centralLevels"][k]
        traces.append({
            "type": "scatter", **axes, "mode": "lines", "fill": "toself", "fillcolor": rgba(FAN_ALPHA[k]),
            "x": xs + xs[::-1], "y": [s["bands"][k][1] for s in fan["steps"]] + [s["bands"][k][0] for s in fan["steps"]][::-1],
            "line": {"width": 0}, "name": html.escape(fan_label(level, fan["memberCount"])), "hoverinfo": "skip",
            "meta": {"scUncertainty": {"panelId": panel_id, "role": "fan", "level": level, "recordSha256": record_sha}},
        })
    custom = [[_num_text(s["bands"][k][0]) + " to " + _num_text(s["bands"][k][1]) for k in range(n)] for s in fan["steps"]]
    hover = "step: %{x}<br>median: %{y} " + html.escape(unit) + "".join(
        f"<br>central {lv * 100:g}%: %{{customdata[{k}]}}" for k, lv in enumerate(fan["centralLevels"])) + "<extra></extra>"
    traces.append({
        "type": "scatter", **axes, "mode": "lines+markers", "x": xs, "y": [s["median"] for s in fan["steps"]],
        "line": {"color": FIT_COLOUR, "width": 2}, "marker": {"color": FIT_COLOUR, "size": 5, "symbol": "diamond"},
        "name": html.escape(median_label + " (ensemble median)"), "customdata": custom, "hovertemplate": hover,
        "meta": {"scUncertainty": {"panelId": panel_id, "role": "median"}},
    })
    return traces


def table_columns(rec: Optional[Dict[str, Any]], unit: str) -> List[Dict[str, Any]]:
    if rec is None:
        return []
    if rec["kind"] == "band":
        cols = [{"key": "fit", "label": "Fitted mean (runtime)", "unit": unit}]
        for b in rec["bands"][::-1]:
            kind = "prediction" if b["semantics"] == "prediction-band" else "confidence"
            cols += [{"key": f"{kind}.lower", "label": f"{b['level'] * 100:g}% {kind} lower", "unit": unit},
                     {"key": f"{kind}.upper", "label": f"{b['level'] * 100:g}% {kind} upper", "unit": unit}]
        return cols
    fan = rec["fan"]
    cols = [{"key": "median", "label": "Ensemble median", "unit": unit}]
    for lv in fan["centralLevels"]:
        cols += [{"key": f"q{lv:g}.lower", "label": f"central {lv * 100:g}% lower", "unit": unit},
                 {"key": f"q{lv:g}.upper", "label": f"central {lv * 100:g}% upper", "unit": unit}]
    return cols + [{"key": "min", "label": "Member minimum", "unit": unit}, {"key": "max", "label": "Member maximum", "unit": unit}]


def table_rows(rec: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if rec is None:
        return []
    if rec["kind"] == "band":
        base = rec["bands"][-1]["points"]
        rows = [{"x": p[0], "fit": p[1]} for p in base]
        for b in rec["bands"]:
            kind = "prediction" if b["semantics"] == "prediction-band" else "confidence"
            for row, p in zip(rows, b["points"]):
                row[f"{kind}.lower"], row[f"{kind}.upper"] = p[2], p[3]
        return rows
    fan = rec["fan"]
    rows = []
    for s in fan["steps"]:
        row = {"x": s["x"], "median": s["median"], "min": s["min"], "max": s["max"]}
        for lv, pair in zip(fan["centralLevels"], s["bands"]):
            row[f"q{lv:g}.lower"], row[f"q{lv:g}.upper"] = pair
        rows.append(row)
    return rows


def summary(rec: Optional[Dict[str, Any]], unavailable_reason: str) -> List[str]:
    if rec is None:
        return [f"Uncertainty unavailable: {unavailable_reason}"]
    if rec["kind"] == "band":
        out = []
        for b in rec["bands"][::-1]:
            widths = [p[3] - p[2] for p in b["points"]]
            out.append(f"{band_label(b)}: width {min(widths):.4g} to {max(widths):.4g} over {len(widths)} observed x values; "
                       f"method {b['method']}")
        return out
    fan = rec["fan"]
    return [f"{fan_label(lv, fan['memberCount'])}: width {min(s['bands'][k][1] - s['bands'][k][0] for s in fan['steps']):.4g} to "
            f"{max(s['bands'][k][1] - s['bands'][k][0] for s in fan['steps']):.4g} over {len(fan['steps'])} steps"
            for k, lv in enumerate(fan["centralLevels"])] + [f"method {fan['method']}"]

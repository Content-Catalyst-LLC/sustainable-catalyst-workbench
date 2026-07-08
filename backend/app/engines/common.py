from __future__ import annotations
import ast, io, math, re
from typing import Any
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SAFE_MATH = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
SAFE_MATH.update({"np": np, "numpy": np, "abs": abs, "min": min, "max": max, "sum": sum})

def parse_number_list(value: Any) -> list[float]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, np.ndarray)):
        return [float(x) for x in value]
    text = str(value).strip()
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)):
            return [float(x) for x in parsed]
    except Exception:
        pass
    return [float(x) for x in re.split(r"[\s,;]+", text) if x.strip()]

def parse_matrix(value: Any) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return value.astype(float)
    if isinstance(value, list):
        return np.array(value, dtype=float)
    text = str(value).strip()
    try:
        return np.array(ast.literal_eval(text), dtype=float)
    except Exception:
        rows = []
        for line in text.splitlines():
            nums = parse_number_list(line)
            if nums:
                rows.append(nums)
        return np.array(rows, dtype=float)

def parse_kv(text: Any) -> dict[str, Any]:
    if isinstance(text, dict):
        return text
    out: dict[str, Any] = {}
    if text is None:
        return out
    for part in re.split(r"[;\n]+", str(text)):
        if not part.strip():
            continue
        if '=' not in part:
            continue
        key, val = part.split('=', 1)
        key = key.strip().lower().replace(' ', '_')
        val = val.strip()
        if ',' in val:
            try:
                out[key] = [float(x.strip()) for x in val.split(',') if x.strip()]
                continue
            except Exception:
                pass
        try:
            out[key] = float(val)
        except Exception:
            out[key] = val
    return out

def parse_rows(value: Any) -> np.ndarray:
    if isinstance(value, list):
        return np.array(value, dtype=float)
    rows = []
    for line in str(value or '').splitlines():
        nums = parse_number_list(line)
        if nums:
            rows.append(nums)
    return np.array(rows, dtype=float) if rows else np.empty((0, 0))

def svg_from_figure(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format='svg', bbox_inches='tight')
    return buf.getvalue()

def result(tool: str, summary: str, values=None, warnings=None, graphs=None, method=None, engine="python", interpretation=None):
    return {
        "ok": True,
        "tool": tool,
        "engine": engine,
        "summary": summary,
        "values": values or {},
        "warnings": warnings or [],
        "graphs": graphs or [],
        "method": method or [],
        "interpretation": interpretation or [],
        "disclaimer": "Educational and analytical support only. Not a substitute for licensed professional judgment."
    }

def eval_function(expr: str, xs: np.ndarray) -> np.ndarray:
    safe = dict(SAFE_MATH)
    safe['x'] = xs
    return np.asarray(eval(expr, {"__builtins__": {}}, safe), dtype=float)

def bar_graph(labels, values, title, ylabel="Value"):
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.bar(range(len(values)), values)
    ax.set_xticks(range(len(labels)), labels, rotation=20, ha='right')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(axis='y', alpha=.25)
    svg = svg_from_figure(fig)
    plt.close(fig)
    return {"title": title, "type": "bar", "svg": svg}

from __future__ import annotations
import ast, io, math, re
from typing import Any
import numpy as np


def parse_number_list(text: str) -> list[float]:
    if text is None:
        return []
    text = str(text).strip()
    if not text:
        return []
    try:
        value = ast.literal_eval(text)
        if isinstance(value, (list, tuple)):
            return [float(x) for x in np.ravel(value)]
    except Exception:
        pass
    return [float(x) for x in re.split(r"[\s,;]+", text) if x.strip()]


def parse_matrix(text: str) -> np.ndarray:
    try:
        value = ast.literal_eval(str(text))
        return np.array(value, dtype=float)
    except Exception as exc:
        raise ValueError("Expected matrix format like [[2,1],[1,3]].") from exc


def parse_kv(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if not text:
        return out
    parts = re.split(r"[;\n]+", str(text))
    for part in parts:
        if not part.strip() or "=" not in part:
            continue
        k, v = part.split("=", 1)
        key = k.strip().lower().replace(" ", "_")
        val = v.strip()
        if "," in val:
            try:
                out[key] = [float(x.strip()) for x in val.split(",") if x.strip()]
                continue
            except Exception:
                pass
        try:
            out[key] = float(val)
        except ValueError:
            out[key] = val
    return out


def parse_rows(text: str) -> np.ndarray:
    rows = []
    for line in str(text or "").strip().splitlines():
        if not line.strip():
            continue
        rows.append(parse_number_list(line))
    if not rows:
        return np.empty((0, 0))
    width = max(len(r) for r in rows)
    if any(len(r) != width for r in rows):
        raise ValueError("All response rows must have the same number of item scores.")
    return np.array(rows, dtype=float)


def svg_from_figure(fig) -> str:
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    return buf.getvalue()


def safe_float(v: Any, default: float) -> float:
    try:
        if v in (None, ""):
            return default
        return float(v)
    except Exception:
        return default

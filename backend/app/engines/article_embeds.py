from __future__ import annotations

import re
from typing import Any

from app.core.model_registry import get_tool, list_tools


def _clean_formula(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text[:1200]


def _slugify_tool_title(tool_id: str) -> str:
    spec = get_tool(tool_id)
    if spec and spec.get("title"):
        return str(spec["title"])
    return str(tool_id or "workbench-tool").replace("-", " ").title()


def _add_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def infer_formula_embed(formula: str, context: str = "", preferred_tool: str = "") -> dict[str, Any]:
    """Infer the best near-formula Workbench embed type.

    This intentionally stays deterministic. It does not claim to prove mathematical
    meaning; it creates an editorial recommendation for where and how to embed a
    calculator beside article formulas.
    """
    f = _clean_formula(formula)
    haystack = (f + " " + str(context or "")).lower()
    tools: list[str] = []
    notes: list[str] = []
    domain = "Mathematical Modeling"
    embed_kind = "symbolic"
    action = "translate"

    if preferred_tool:
        _add_unique(tools, preferred_tool)
        notes.append("A preferred tool was supplied by the shortcode or placement recommendation.")

    graph_patterns = [
        r"(^|\s)y\s*=", r"f\s*\(\s*x\s*\)", r"sin\s*\(", r"cos\s*\(", r"tan\s*\(",
        r"exp\s*\(", r"log\s*\(", r"x\^", r"x\s*\*", r"\bx\b",
    ]
    if any(re.search(p, haystack) for p in graph_patterns):
        domain = "Graphable Functions and Calculus"
        embed_kind = "graph"
        action = "graph"
        _add_unique(tools, "graphable-function-explorer")
        _add_unique(tools, "calculus-function-analyzer")
        notes.append("The formula appears to be graphable as a single-variable function or expression.")

    if re.search(r"\\int|integral|derivative|d/dx|\\frac\{d|\\partial|lim_|\\nabla|dx|dy", haystack):
        domain = "Calculus and Differential Modeling"
        embed_kind = "symbolic"
        action = "differentiate" if "derivative" in haystack or "d/dx" in haystack else "translate"
        _add_unique(tools, "calculus-function-analyzer")
        _add_unique(tools, "differential-equation-simulator")
        notes.append("Calculus notation was detected; symbolic analysis is recommended near the formula.")

    if re.search(r"force|stress|strain|beam|load|deflection|sigma|\bsigma\b|τ|tau|pressure|pump|power|heat|thermal|voltage|current|resistance|ohm|rc|f\s*=\s*m\s*\*?\s*a|σ\s*=|sigma\s*=|f/a", haystack):
        domain = "Engineering Analysis"
        embed_kind = "engineering"
        action = "engineering_note"
        for tid in ["mechanical-systems-engineering-tool", "structural-engineering-tool", "electrical-circuit-tool"]:
            _add_unique(tools, tid)
        notes.append("Engineering quantities or notation were detected; an engineering-aware note is recommended.")

    if re.search(r"npv|roi|payback|discount|elasticity|marginal|cost|benefit", haystack):
        domain = "Economics and Tradeoff Analysis"
        embed_kind = "calculator"
        action = "calculate"
        _add_unique(tools, "economics-calculator")
        _add_unique(tools, "economics-forecasting-scenario-tool")
        notes.append("Economic or tradeoff notation was detected; a calculator or scenario tool should be placed near the formula.")

    if re.search(r"energy|emission|carbon|co2|kwh|efficiency|temperature|climate", haystack):
        domain = "Energy and Environmental Systems"
        embed_kind = "calculator"
        action = "calculate"
        _add_unique(tools, "energy-systems-calculator")
        _add_unique(tools, "environmental-science-calculator")
        notes.append("Energy, emissions, or environmental quantities were detected.")

    if embed_kind != "engineering" and re.search(r"probability|variance|standard deviation|\bmu\b|\sigma|bayes|distribution|normal|regression|r\^2", haystack):
        domain = "Probability, Statistics, and Forecasting"
        embed_kind = "calculator"
        action = "calculate"
        _add_unique(tools, "statistics-analyzer")
        _add_unique(tools, "regression-analyzer")
        notes.append("Statistical notation or modeling language was detected.")

    if not tools:
        _add_unique(tools, "systems-modeling-tool")
        _add_unique(tools, "systems-thinking-tool")
        notes.append("No narrow match was detected; a general symbolic/modeling embed is recommended.")

    confidence = "high" if len(notes) >= 2 or preferred_tool else "medium"
    if embed_kind == "symbolic" and not re.search(r"[=^_\\*/()+\-]|\b(sin|cos|sqrt|log|exp)\b", haystack):
        confidence = "low"

    return {
        "formula": f,
        "domain": domain,
        "recommended_tool_ids": tools[:6],
        "embed_kind": embed_kind,
        "action": action,
        "confidence": confidence,
        "notes": notes,
    }


def formula_shortcode(formula: str, tool_id: str = "", display: str = "inline", title: str = "Formula Calculator") -> str:
    safe_formula = _clean_formula(formula).replace('"', '&quot;')
    safe_tool = re.sub(r"[^a-z0-9\-]", "", str(tool_id or "").lower())
    safe_display = re.sub(r"[^a-z0-9\-]", "", str(display or "inline").lower()) or "inline"
    safe_title = str(title or "Formula Calculator").replace('"', '&quot;')[:160]
    tool_attr = f' tool="{safe_tool}"' if safe_tool else ""
    return f'[sc_workbench_formula_calculator display="{safe_display}" formula="{safe_formula}"{tool_attr} title="{safe_title}"]'


def article_formula_embed_analyzer(payload: dict[str, Any]) -> dict[str, Any]:
    formula = _clean_formula(payload.get("formula") or payload.get("equation") or payload.get("input") or "")
    context = str(payload.get("context") or "")[:2000]
    article_title = str(payload.get("article_title") or "")[:300]
    article_slug = str(payload.get("article_slug") or payload.get("article") or "")[:200]
    preferred_tool = re.sub(r"[^a-z0-9\-]", "", str(payload.get("tool") or payload.get("preferred_tool") or "").lower())
    preferred_display = re.sub(r"[^a-z0-9\-]", "", str(payload.get("display") or payload.get("preferred_display") or "inline").lower()) or "inline"

    if not formula:
        return {
            "ok": False,
            "tool": "Article Formula Embed Planner",
            "summary": "No formula was supplied.",
            "values": {},
            "warnings": ["Add a formula or equation attribute to the shortcode."],
            "disclaimer": "Educational support only.",
        }

    inference = infer_formula_embed(formula, context + " " + article_title, preferred_tool)
    primary_tool = preferred_tool or (inference["recommended_tool_ids"][0] if inference["recommended_tool_ids"] else "systems-modeling-tool")
    tool_title = _slugify_tool_title(primary_tool)
    short_title = f"{tool_title} for this formula"
    near_formula_shortcode = formula_shortcode(formula, primary_tool, preferred_display, short_title)
    drawer_shortcode = formula_shortcode(formula, primary_tool, "drawer", short_title)
    compact_shortcode = formula_shortcode(formula, primary_tool, "compact", short_title)
    full_workbench_shortcode = '[sc_workbench mode="tool" display="drawer" tool="' + primary_tool + '"' + ((' article="' + article_slug + '"') if article_slug else '') + ' title="' + short_title.replace('"', '&quot;') + '"]'

    registry = {t["id"]: t for t in list_tools(limit=300)}
    recommended_tools = []
    for tid in inference["recommended_tool_ids"]:
        spec = registry.get(tid)
        recommended_tools.append(spec or {"id": tid, "title": _slugify_tool_title(tid), "domain": inference["domain"], "description": "Formula-specific Workbench tool recommendation."})

    placement = "place directly after the formula block or paragraph where the formula is first interpreted"
    if preferred_display == "drawer":
        placement = "place after the formula paragraph as a collapsible drawer so the article stays readable"
    if inference["embed_kind"] == "graph":
        placement = "place directly below the graphable formula so readers can adjust parameters while reading"
    if inference["embed_kind"] == "engineering":
        placement = "place directly below the engineering formula, before any prose conclusion or design implication"

    interpretation = [
        "Keep the formula visible above or beside the embed so the calculator feels attached to the article argument.",
        "Use inline display for short formulas, compact display for primary article tools, and drawer display for secondary tools.",
        "Review the detected tool and confidence before publishing because symbolic notation can be ambiguous.",
    ]

    return {
        "ok": True,
        "version": "1.6.0",
        "tool": "Article Formula Embed Planner",
        "summary": "This formula has been converted into a near-formula Workbench calculator recommendation with copy-ready shortcodes.",
        "values": {
            "formula": formula,
            "article_title": article_title,
            "article_slug": article_slug,
            "primary_domain": inference["domain"],
            "embed_kind": inference["embed_kind"],
            "recommended_action": inference["action"],
            "recommended_tool_id": primary_tool,
            "recommended_tool_title": tool_title,
            "confidence": inference["confidence"],
            "suggested_placement": placement,
            "near_formula_shortcode": near_formula_shortcode,
            "drawer_shortcode": drawer_shortcode,
            "compact_shortcode": compact_shortcode,
            "full_workbench_shortcode": full_workbench_shortcode,
        },
        "recommended_tools": recommended_tools,
        "shortcodes": {
            "near_formula": near_formula_shortcode,
            "drawer": drawer_shortcode,
            "compact": compact_shortcode,
            "full_workbench": full_workbench_shortcode,
        },
        "warnings": [
            "Formula-to-calculator placement is deterministic guidance, not proof that the selected calculator is the only correct interpretation.",
            "Use professional review for engineering, safety-critical, financial, legal, medical, or compliance-sensitive formulas.",
        ],
        "method": "Rule-based formula classification, local tool-registry lookup, and shortcode generation for WordPress article placement.",
        "interpretation": interpretation,
        "disclaimer": "Educational and analytical support only. Verify formula meaning, assumptions, units, and domain constraints before public or professional use.",
    }

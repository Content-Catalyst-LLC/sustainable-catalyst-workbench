from __future__ import annotations

from datetime import datetime, timezone
from html import escape
import re
from typing import Any

REPORT_VERSION = "1.5.0"


def _safe_slug(value: Any, fallback: str = "calculation-report") -> str:
    text = str(value or fallback).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return (text or fallback)[:90]


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return ", ".join(f"{k}: {_stringify(v)}" for k, v in value.items())
    if isinstance(value, list):
        return "; ".join(_stringify(v) for v in value)
    return str(value)


def _as_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [_stringify(v) for v in value if _stringify(v).strip()]
    return [_stringify(value)]


def _table_markdown(rows: dict[str, Any] | list[Any], key_label: str = "Field", value_label: str = "Value") -> str:
    if not rows:
        return "_No entries supplied._\n"
    out = [f"| {key_label} | {value_label} |", "|---|---|"]
    if isinstance(rows, dict):
        iterator = rows.items()
    else:
        iterator = [(f"Item {i+1}", row) for i, row in enumerate(rows)]
    for key, value in iterator:
        value_text = _stringify(value).replace("\n", "<br>")
        out.append(f"| `{key}` | {value_text} |")
    return "\n".join(out) + "\n"


def _table_html(rows: dict[str, Any] | list[Any], key_label: str = "Field", value_label: str = "Value") -> str:
    if not rows:
        return '<p class="scwb-report-muted">No entries supplied.</p>'
    if isinstance(rows, dict):
        iterator = rows.items()
    else:
        iterator = [(f"Item {i+1}", row) for i, row in enumerate(rows)]
    body = "".join(
        f"<tr><th>{escape(str(key))}</th><td>{escape(_stringify(value))}</td></tr>"
        for key, value in iterator
    )
    return f"<table><thead><tr><th>{escape(key_label)}</th><th>{escape(value_label)}</th></tr></thead><tbody>{body}</tbody></table>"


def _list_markdown(items: list[str]) -> str:
    if not items:
        return "_None listed._\n"
    return "\n".join(f"- {item}" for item in items) + "\n"


def _list_html(items: list[str]) -> str:
    if not items:
        return '<p class="scwb-report-muted">None listed.</p>'
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _extract_note(source: dict[str, Any]) -> dict[str, Any]:
    values = source.get("values") if isinstance(source.get("values"), dict) else {}
    note = values.get("engineering_note") if isinstance(values.get("engineering_note"), dict) else {}
    engineering_mode = source.get("engineering_mode") if isinstance(source.get("engineering_mode"), dict) else {}
    if not note and isinstance(values.get("engineering_mode"), dict):
        note = values["engineering_mode"]
    if not note and engineering_mode:
        note = engineering_mode
    return note or {}


def _extract_report_fields(source: dict[str, Any]) -> dict[str, Any]:
    values = source.get("values") if isinstance(source.get("values"), dict) else {}
    note = _extract_note(source)
    title = note.get("calculation_title") or source.get("tool") or values.get("calculator_id") or "Workbench calculation"
    formula = note.get("formula") or values.get("formula") or ""
    inputs = note.get("inputs") if isinstance(note.get("inputs"), dict) else values.get("inputs") if isinstance(values.get("inputs"), dict) else {}
    results = note.get("results") if isinstance(note.get("results"), dict) else values.get("results") if isinstance(values.get("results"), dict) else {}
    assumptions = _as_list(note.get("assumptions"))
    checks = _as_list(note.get("validation_checks"))
    sections = _as_list(note.get("calculation_note_sections"))
    warnings = _as_list(source.get("warnings"))
    method = _as_list(source.get("method"))
    interpretation = _as_list(source.get("interpretation"))
    graphs = source.get("graphs") if isinstance(source.get("graphs"), list) else []
    return {
        "title": title,
        "summary": source.get("summary") or "",
        "tool": source.get("tool") or "Sustainable Catalyst Workbench",
        "engine": source.get("engine") or "python",
        "formula": formula,
        "inputs": inputs,
        "results": results,
        "assumptions": assumptions,
        "validation_checks": checks,
        "calculation_note_sections": sections,
        "warnings": warnings,
        "method": method,
        "interpretation": interpretation,
        "graphs": graphs,
        "disclaimer": source.get("disclaimer") or "Educational and analytical support only. Not a substitute for licensed professional judgment.",
    }


def _graph_markdown(graphs: list[dict[str, Any]], include_graphs: bool) -> str:
    if not graphs:
        return "_No graph generated for this calculation._\n"
    out = []
    for index, graph in enumerate(graphs, 1):
        title = graph.get("title") or f"Graph {index}"
        out.append(f"{index}. **{title}** — graph available in the HTML report and Workbench UI.")
        if include_graphs and graph.get("svg"):
            out.append("   - SVG included in HTML export; download SVG/PNG separately from the Workbench graph controls when needed.")
    return "\n".join(out) + "\n"


def _graph_html(graphs: list[dict[str, Any]], include_graphs: bool) -> str:
    if not graphs:
        return '<p class="scwb-report-muted">No graph generated for this calculation.</p>'
    items = []
    for index, graph in enumerate(graphs, 1):
        title = graph.get("title") or f"Graph {index}"
        svg = graph.get("svg") if include_graphs else ""
        # SVG originates from the Workbench backend graph engine. The report endpoint does not execute it.
        items.append(f'<figure><figcaption>{escape(title)}</figcaption>{svg or "<p>Graph available in the Workbench UI.</p>"}</figure>')
    return "".join(items)


def build_calculation_report(source_result: dict[str, Any], *, include_graphs: bool = True, report_type: str = "engineering_calculation_note") -> dict[str, Any]:
    fields = _extract_report_fields(source_result if isinstance(source_result, dict) else {})
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    filename_base = _safe_slug(fields["title"])

    markdown = f"""# {fields['title']}

**Generated by:** Sustainable Catalyst Workbench  
**Report type:** {report_type.replace('_', ' ')}  
**Generated at:** {generated_at}  
**Tool:** {fields['tool']}  
**Engine:** {fields['engine']}

## 1. Purpose and summary

{fields['summary'] or 'Calculation report generated from a Workbench result.'}

## 2. Formula

`{fields['formula'] or 'No formula returned.'}`

## 3. Inputs and units

{_table_markdown(fields['inputs'], 'Input', 'Value')}

## 4. Computed results

{_table_markdown(fields['results'], 'Result', 'Value')}

## 5. Sensitivity or graph review

{_graph_markdown(fields['graphs'], include_graphs)}

## 6. Assumptions

{_list_markdown(fields['assumptions'])}

## 7. Validation checks

{_list_markdown(fields['validation_checks'])}

## 8. Method

{_list_markdown(fields['method'])}

## 9. Interpretation and next review

{_list_markdown(fields['interpretation'])}

## 10. Warnings and professional boundary

{_list_markdown(fields['warnings'])}

**Boundary:** {fields['disclaimer']}
"""

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{escape(fields['title'])}</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;margin:34px;color:#111;line-height:1.55;}}
.scwb-report{{max-width:980px;margin:0 auto;}}
.scwb-report-kicker{{text-transform:uppercase;letter-spacing:.08em;color:#b40000;font-weight:800;font-size:.8rem;}}
h1{{font-size:2rem;line-height:1.1;margin:.2rem 0 1rem 0;}}
h2{{font-size:1.15rem;border-bottom:2px solid #eee;padding-bottom:.45rem;margin-top:1.8rem;}}
table{{border-collapse:collapse;width:100%;margin:.8rem 0;}}
th,td{{border:1px solid #ddd;padding:.55rem;text-align:left;vertical-align:top;}}
th{{background:#f7f7f7;width:30%;}}
figure{{border:1px solid #ddd;padding:12px;margin:14px 0;break-inside:avoid;}}
figure svg{{max-width:100%;height:auto;}}
figcaption{{font-weight:700;margin-bottom:8px;}}
.scwb-report-muted{{color:#666;}}
.scwb-report-boundary{{border-left:4px solid #b40000;padding:.7rem 1rem;background:#fff7f7;}}
@page{{margin:.6in;}}
</style>
</head>
<body>
<main class="scwb-report">
<p class="scwb-report-kicker">Sustainable Catalyst Workbench</p>
<h1>{escape(fields['title'])}</h1>
<p><strong>Report type:</strong> {escape(report_type.replace('_', ' '))}<br>
<strong>Generated at:</strong> {escape(generated_at)}<br>
<strong>Tool:</strong> {escape(fields['tool'])}<br>
<strong>Engine:</strong> {escape(fields['engine'])}</p>
<section><h2>1. Purpose and summary</h2><p>{escape(fields['summary'] or 'Calculation report generated from a Workbench result.')}</p></section>
<section><h2>2. Formula</h2><p><code>{escape(fields['formula'] or 'No formula returned.')}</code></p></section>
<section><h2>3. Inputs and units</h2>{_table_html(fields['inputs'], 'Input', 'Value')}</section>
<section><h2>4. Computed results</h2>{_table_html(fields['results'], 'Result', 'Value')}</section>
<section><h2>5. Sensitivity or graph review</h2>{_graph_html(fields['graphs'], include_graphs)}</section>
<section><h2>6. Assumptions</h2>{_list_html(fields['assumptions'])}</section>
<section><h2>7. Validation checks</h2>{_list_html(fields['validation_checks'])}</section>
<section><h2>8. Method</h2>{_list_html(fields['method'])}</section>
<section><h2>9. Interpretation and next review</h2>{_list_html(fields['interpretation'])}</section>
<section><h2>10. Warnings and professional boundary</h2>{_list_html(fields['warnings'])}<p class="scwb-report-boundary"><strong>Boundary:</strong> {escape(fields['disclaimer'])}</p></section>
</main>
</body>
</html>"""

    text = re.sub(r"<[^>]+>", "", markdown.replace("**", "").replace("`", ""))

    return {
        "ok": True,
        "version": REPORT_VERSION,
        "report_type": report_type,
        "report_title": fields["title"],
        "generated_at": generated_at,
        "filename_base": filename_base,
        "formats": {
            "markdown": markdown,
            "html": html,
            "text": text,
        },
        "sections": [
            "Purpose and summary",
            "Formula",
            "Inputs and units",
            "Computed results",
            "Sensitivity or graph review",
            "Assumptions",
            "Validation checks",
            "Method",
            "Interpretation and next review",
            "Warnings and professional boundary",
        ],
        "summary": "Generated an export-ready calculation report from a Workbench result.",
        "warnings": [
            "The report is generated from user-provided inputs and Workbench calculator output.",
            "Review all assumptions, units, graph behavior, and validation checks before professional use.",
        ],
    }

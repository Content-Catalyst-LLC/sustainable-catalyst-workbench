from __future__ import annotations
from typing import Any
import re
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.core.model_registry import get_tool, list_tools

router = APIRouter(prefix='/equations', tags=['equations'])

class EquationAnalyzeRequest(BaseModel):
    equation: str = Field(..., min_length=1)
    context: str = ""
    article_title: str = ""
    suggested_tools: list[str] = Field(default_factory=list)
    mode: str = "guided"


def _infer_tools(equation: str, context: str = "") -> tuple[str, list[str], list[str]]:
    text = (equation + " " + context).lower()
    tools: list[str] = []
    notes: list[str] = []
    domain = "Mathematical Modeling"
    def add(tool_id: str):
        if tool_id not in tools:
            tools.append(tool_id)
    rules = [
        (r"matrix|bmatrix|pmatrix|eigen|rank|det|\\lambda|vector", "Linear Algebra and Systems Modeling", ["linear-system-solver", "vector-geometry-calculator"], "Matrix/vector structure detected."),
        (r"\\int|integral|derivative|\\frac\{d|\\partial|dx|dy|lim_|\\nabla", "Calculus and Differential Modeling", ["calculus-function-analyzer", "differential-equation-simulator"], "Rate/change or accumulation structure detected."),
        (r"probability|variance|\\sigma|\\mu|var\(|e\(|p\(|bayes|\\sim|distribution", "Probability and Statistics", ["statistics-analyzer", "probability-distribution-calculator"], "Uncertainty/statistical notation detected."),
        (r"\\hat\{?y|regression|b_0|b_1|r\^2|forecast|time[- ]series|predict", "Predictive Analytics", ["regression-analyzer", "predictive-analytics-forecasting-tool", "time-series-diagnostics-tool"], "Prediction/model-fit structure detected."),
        (r"x_\{?t\+1|s_\{?t|stock|flow|feedback|carrying capacity|limits to growth", "Systems Dynamics", ["systems-modeling-tool", "limits-to-growth-system-dynamics-tool"], "State update, stock-flow, or feedback structure detected."),
        (r"elasticity|npv|discount|utility|demand|supply|gdp|inflation|econom", "Economics", ["economics-calculator", "economics-forecasting-and-scenario-tool", "econometrics-and-policy-model-tool"], "Economic model language detected."),
        (r"energy|carbon|co2|emission|kwh|lcoe|climate|temperature anomaly", "Energy, Climate, and Environmental Systems", ["energy-systems-calculator", "climate-change-scenario-tool", "environmental-science-calculator"], "Energy/climate/environmental quantities detected."),
        (r"force|torque|stress|strain|beam|load|pressure|velocity|acceleration|thermal|fluid", "Engineering Physics", ["physics-calculator", "mechanical-systems-engineering-tool", "structural-engineering-tool"], "Physical/engineering quantities detected."),
        (r"voltage|current|impedance|antenna|frequency|wavelength|rf|resonance|circuit", "Electrical, RF, and Electronics", ["electronics-engineering-calculator", "rf-and-antenna-calculator", "power-systems-engineering-tool"], "Electrical/RF variables detected."),
        (r"dose|prevalence|sensitivity|specificity|trial|clinical|diagnostic|health", "Clinical and Public Health Research", ["clinical-research-calculator", "health-and-medical-public-health-analytics-tool"], "Clinical/public-health metrics detected."),
    ]
    for pat, d, ids, note in rules:
        if re.search(pat, text):
            if domain == "Mathematical Modeling":
                domain = d
            for tid in ids: add(tid)
            notes.append(note)
    if not tools:
        tools = ["systems-modeling-tool", "systems-thinking-tool"]
        notes.append("No highly specific pattern was detected; general modeling and systems tools are recommended.")
    return domain, tools[:8], notes


def _graphability(equation: str) -> str:
    e = equation.lower()
    if any(token in e for token in ["x_{t+1}", "s_{t+1}", "t+1", "stock", "flow"]):
        return "High: can often be turned into a recurrence, stock-flow simulation, or scenario curve."
    if any(token in e for token in ["y=", "f(x)", "\\hat", "b_0", "b_1", "dx", "dt", "\\frac"]):
        return "Medium to high: likely graphable as a function, fitted relation, rate equation, or trajectory if variables and parameters are supplied."
    if any(token in e for token in ["matrix", "bmatrix", "pmatrix", "det", "rank", "eigen"]):
        return "Medium: graphability depends on whether the equation represents a matrix transformation, network, eigen-structure, or numerical system."
    return "Context-dependent: the Workbench can explain and map the equation now; graphing may require variable definitions and numeric assumptions."


@router.post('/analyze')
def analyze_equation(req: EquationAnalyzeRequest) -> dict[str, Any]:
    domain, inferred_tools, notes = _infer_tools(req.equation, req.context + " " + req.article_title)
    tool_ids = []
    for tid in (req.suggested_tools or []) + inferred_tools:
        if tid and tid not in tool_ids:
            tool_ids.append(tid)
    recommended = []
    registry = {t['id']: t for t in list_tools(limit=200)}
    for tid in tool_ids[:8]:
        spec = registry.get(tid)
        recommended.append(spec or {"id": tid, "title": tid.replace('-', ' ').title(), "domain": domain, "description": "Article-specific recommended Workbench tool."})
    summary = "This equation has been mapped into the Sustainable Catalyst Workbench equation layer. The analysis identifies the likely domain, candidate calculator tools, graphing potential, and interpretation path."
    interpretation = [
        "Read the equation first as a relationship among quantities, not just as notation.",
        "Define each variable, parameter, unit, and assumption before computing.",
        "Use the recommended calculator when numeric inputs, scenario comparison, or graph output are needed.",
        "For professional domains, treat outputs as educational or analytical support rather than certified advice.",
    ]
    return {
        "ok": True,
        "tool": "Equation-Aware Workbench Analyzer",
        "summary": summary,
        "values": {
            "equation": req.equation,
            "article_title": req.article_title,
            "suggested_domain": domain,
            "graphability": _graphability(req.equation),
            "recommended_tool_count": len(recommended),
        },
        "recommended_tools": recommended,
        "warnings": [
            "Automatically inferred tool mappings should be reviewed, especially for ambiguous notation.",
            "This is not licensed professional, clinical, legal, financial, or safety-critical advice.",
        ],
        "method": "Regex/domain inference plus Workbench model registry lookup. Future versions can add symbolic parsing and article-level vector retrieval.",
        "interpretation": interpretation,
        "disclaimer": "Educational and analytical support only. Verify equations, assumptions, units, and domain-specific constraints before use."
    }

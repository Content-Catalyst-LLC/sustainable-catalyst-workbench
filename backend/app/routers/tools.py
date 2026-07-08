from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.tool_registry import get_tool, list_tools
from app.schemas.tool import ToolRunRequest
from app.engines.math import linear_system_solver
from app.engines.decision import decision_matrix
from app.engines.sustainability import resilience_scorecard, tradeoff_matrix
from app.engines.governance import ai_governance_audit
from app.engines.interpretation import qualitative_matrix

router = APIRouter(tags=["tools"])

ENGINE_MAP = {
    "linear-system-solver": linear_system_solver.run,
    "decision-matrix": decision_matrix.run,
    "risk-resilience-scorecard": resilience_scorecard.run,
    "ai-governance-audit": ai_governance_audit.run,
    "sustainability-tradeoff-matrix": tradeoff_matrix.run,
    "qualitative-interpretation-matrix": qualitative_matrix.run,
}


@router.get("/tools")
def tools(topic: str | None = Query(default=None), domain: str | None = Query(default=None)) -> dict:
    return {"ok": True, "tools": list_tools(topic=topic, domain=domain)}


@router.get("/tools/{tool_id}")
def tool_detail(tool_id: str) -> dict:
    tool = get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"ok": True, "tool": tool}


@router.post("/tools/run")
def run_tool(request: ToolRunRequest) -> dict:
    tool = get_tool(request.tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    runner = ENGINE_MAP.get(request.tool_id)
    if not runner:
        return {
            "ok": False,
            "tool_id": request.tool_id,
            "result": {},
            "warnings": ["This tool is registered but does not have an executable engine yet."],
            "interpretation": "Use the registry entry to route users to the correct Research Library path until the engine is implemented.",
        }

    try:
        output = runner(request.inputs)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "ok": True,
        "tool_id": request.tool_id,
        "tool": tool,
        "result": output.get("result", {}),
        "warnings": output.get("warnings", []),
        "interpretation": output.get("interpretation"),
    }

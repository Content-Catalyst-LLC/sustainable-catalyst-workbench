from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from app.core.tool_registry import list_tools, get_tool
from app.schemas.requests import ToolRunRequest
from app.engines.runner import run_tool

router = APIRouter(prefix="/tools", tags=["tools"])

@router.get("")
def tools(topic: str = "", domain: str = "", limit: int = Query(36, ge=1, le=100)):
    return {"ok": True, "tools": list_tools(topic, domain, limit)}

@router.get("/{tool_id}")
def tool(tool_id: str):
    t = get_tool(tool_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"ok": True, "tool": t}

@router.post("/run")
def run(req: ToolRunRequest):
    try:
        out = run_tool(req.tool_id, req.inputs)
        out["tool_id"] = req.tool_id
        return out
    except Exception as exc:
        return {"ok": False, "tool_id": req.tool_id, "error": str(exc)}

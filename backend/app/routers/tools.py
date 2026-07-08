from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from app.core.model_registry import list_tools, get_tool
from app.schemas.requests import ToolRunRequest
from app.engines.runner import run_tool

router = APIRouter(prefix='/tools', tags=['tools'])

@router.get('')
def tools(domain: str | None = None, topic: str | None = None, limit: int | None = Query(default=None, ge=1, le=100)):
    return {"ok": True, "tools": list_tools(domain=domain, topic=topic, limit=limit)}

@router.get('/{tool_id}')
def tool(tool_id: str):
    spec = get_tool(tool_id)
    if not spec:
        raise HTTPException(status_code=404, detail='Tool not found')
    return {"ok": True, "tool": spec}

@router.post('/run')
def run(req: ToolRunRequest):
    try:
        return run_tool(req.tool_id, req.inputs, req.mode)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        return {"ok": False, "tool": req.tool_id, "error": str(exc)}

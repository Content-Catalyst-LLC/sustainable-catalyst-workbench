from fastapi import APIRouter
from app.core.model_registry import list_tools
from app.core.retrieval import PATHWAYS

router = APIRouter(prefix='/models', tags=['models'])

@router.get('/registry')
def registry():
    return {"ok": True, "tools": list_tools(), "pathways": PATHWAYS}

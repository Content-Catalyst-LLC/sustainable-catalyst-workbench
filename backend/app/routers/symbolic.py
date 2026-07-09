from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.engines.symbolic_engine import symbolic_math_analyzer, chalkboard_preview, normalize_keyboard_math

router = APIRouter(prefix='/symbolic', tags=['symbolic'])

class SymbolicAnalyzeRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=10000)
    action: str = Field(default='translate')
    variable: str | None = None
    x_min: float = -10
    x_max: float = 10
    include_graph: bool = False

@router.post('/analyze')
def analyze(req: SymbolicAnalyzeRequest) -> dict[str, Any]:
    return symbolic_math_analyzer(req.model_dump())

@router.post('/preview')
def preview(payload: dict[str, Any]) -> dict[str, Any]:
    raw = str(payload.get('input') or '')
    return {
        'ok': True,
        'keyboard_input': raw,
        'chalkboard_preview': chalkboard_preview(raw),
        'normalized_code': normalize_keyboard_math(raw),
    }

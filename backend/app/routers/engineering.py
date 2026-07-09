from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.engines.engineering_mode_engine import engineering_mode_analyzer

router = APIRouter(prefix='/engineering', tags=['engineering'])

class EngineeringAnalyzeRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=10000)
    variable: str | None = None
    include_solve: bool = False

@router.post('/analyze')
def analyze(req: EngineeringAnalyzeRequest) -> dict[str, Any]:
    return engineering_mode_analyzer(req.model_dump())

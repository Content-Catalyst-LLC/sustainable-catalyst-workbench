from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.engines.graph_studio_engine import graph_studio_analyzer

router = APIRouter(prefix='/graph', tags=['graph'])

class GraphStudioRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=10000)
    variable: str | None = 'x'
    x_min: float = -10
    x_max: float = 10
    points: int = 700
    parameters: dict[str, float] = Field(default_factory=dict)
    show_derivative: bool = False

@router.post('/studio')
def studio(req: GraphStudioRequest) -> dict[str, Any]:
    return graph_studio_analyzer(req.model_dump())

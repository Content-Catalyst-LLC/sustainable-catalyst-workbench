from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.engines.core_engineering_calculators import list_core_engineering_calculators, get_core_engineering_calculator, run_core_engineering_calculator

router = APIRouter(prefix='/engineering', tags=['engineering-calculators'])

class EngineeringCalculatorRequest(BaseModel):
    calculator_id: str = Field(..., min_length=1, max_length=100)
    inputs: dict[str, Any] = Field(default_factory=dict)

@router.get('/calculators')
def calculators() -> dict[str, Any]:
    return {"ok": True, "version": "1.5.0", "calculators": list_core_engineering_calculators()}

@router.get('/calculators/{calculator_id}')
def calculator(calculator_id: str) -> dict[str, Any]:
    spec = get_core_engineering_calculator(calculator_id)
    if not spec:
        return {"ok": False, "error": "Engineering calculator not found", "calculator_id": calculator_id}
    return {"ok": True, "calculator": spec}

@router.post('/calculate')
def calculate(req: EngineeringCalculatorRequest) -> dict[str, Any]:
    return run_core_engineering_calculator(req.calculator_id, req.inputs)

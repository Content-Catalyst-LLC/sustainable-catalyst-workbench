from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.engines.calculation_reports import build_calculation_report

router = APIRouter(prefix='/reports', tags=['calculation-reports'])


class CalculationReportRequest(BaseModel):
    source_result: dict[str, Any] = Field(default_factory=dict)
    include_graphs: bool = True
    report_type: str = Field(default='engineering_calculation_note', max_length=80)


@router.post('/calculation')
def calculation_report(req: CalculationReportRequest) -> dict[str, Any]:
    return build_calculation_report(req.source_result, include_graphs=req.include_graphs, report_type=req.report_type)

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ToolRunRequest(BaseModel):
    tool_id: str = Field(..., min_length=1)
    inputs: dict[str, Any] = Field(default_factory=dict)


class ToolRunResponse(BaseModel):
    ok: bool
    tool_id: str
    result: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)
    interpretation: str | None = None

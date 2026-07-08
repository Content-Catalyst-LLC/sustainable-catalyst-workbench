from typing import Any
from pydantic import BaseModel, Field

class ToolRunRequest(BaseModel):
    tool_id: str = Field(..., min_length=1)
    inputs: dict[str, Any] = Field(default_factory=dict)
    mode: str = "guided"
    topic: str | None = None

class AskRequest(BaseModel):
    question: str
    topic: str = "research-library"
    mode: str = "guided"
    scope_gate_enabled: bool = True

class AskResponse(BaseModel):
    ok: bool
    answer: str
    scope: dict[str, Any] = Field(default_factory=dict)
    recommended_tools: list[dict[str, Any]] = Field(default_factory=list)
    provider: str = "disabled"
    model: str | None = None

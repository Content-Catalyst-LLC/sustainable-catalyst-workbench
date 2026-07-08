from pydantic import BaseModel, Field
from typing import Any

class ToolRunRequest(BaseModel):
    tool_id: str
    inputs: dict[str, Any] = Field(default_factory=dict)

class AskRequest(BaseModel):
    question: str = ""
    topic: str = ""
    mode: str = "library-guide"
    scope_gate_enabled: bool = True

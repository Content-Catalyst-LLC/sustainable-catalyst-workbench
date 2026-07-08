from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.scope_gate import check_scope, OUT_OF_SCOPE_MESSAGE
from app.core.tool_registry import list_tools

router = APIRouter(prefix="/ai", tags=["site-scoped-ai"])


class AskLibraryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    mode: str = "library-guide"
    topic: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


@router.post("/ask-library")
def ask_library(request: AskLibraryRequest) -> dict:
    scope = check_scope(" ".join([request.question, request.topic or "", request.mode]))
    if not scope["in_scope"]:
        return {
            "ok": True,
            "in_scope": False,
            "answer": OUT_OF_SCOPE_MESSAGE,
            "matched_topics": [],
            "recommended_tools": [],
            "limitations": ["The AI assistant is intentionally restricted to the Sustainable Catalyst knowledge map."],
        }

    matched_topic_ids = [topic["id"] for topic in scope["matched_topics"]]
    recommended_tools = []
    for topic_id in matched_topic_ids:
        recommended_tools.extend(list_tools(topic=topic_id))
    # Deduplicate by ID while preserving order.
    seen = set()
    deduped = []
    for tool in recommended_tools:
        if tool["id"] not in seen:
            seen.add(tool["id"])
            deduped.append(tool)

    answer = _starter_answer(request, scope, deduped)
    return {
        "ok": True,
        "in_scope": True,
        "mode": request.mode,
        "answer": answer,
        "matched_topics": scope["matched_topics"],
        "recommended_tools": deduped[:6],
        "limitations": [
            "This v0.1 backend uses deterministic scope gating and registry routing.",
            "Live retrieval and AI generation are intentionally disabled until the Research Library index is connected.",
        ],
    }


def _starter_answer(request: AskLibraryRequest, scope: dict, tools: list[dict]) -> str:
    topics = ", ".join(topic["title"] for topic in scope["matched_topics"][:3])
    tool_names = ", ".join(tool["title"] for tool in tools[:3]) or "Research Library Assistant"
    return (
        f"This question is in scope for Sustainable Catalyst. It currently connects most strongly to: {topics}. "
        f"Recommended Workbench path: start with {tool_names}. "
        "In the production version, this response should retrieve relevant Sustainable Catalyst pages, article maps, references, and repository metadata before generating a cited answer."
    )

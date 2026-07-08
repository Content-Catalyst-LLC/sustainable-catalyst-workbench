from __future__ import annotations

from app.core.topic_registry import match_topics

OUT_OF_SCOPE_MESSAGE = (
    "That question is outside the Sustainable Catalyst knowledge map. "
    "I can help connect it to sustainability, governance, systems thinking, natural science, "
    "technology, psychology, philosophy, meaning, mathematical modeling, systems modeling, "
    "or problem-solving if there is a relevant angle."
)


def check_scope(question: str) -> dict:
    matches = match_topics(question or "")
    return {
        "in_scope": bool(matches),
        "matched_topics": matches,
        "message": None if matches else OUT_OF_SCOPE_MESSAGE,
    }

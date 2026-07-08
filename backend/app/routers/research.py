from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.topic_registry import all_topics, match_topics

router = APIRouter(prefix="/research", tags=["research"])


@router.get("/topics")
def topics() -> dict:
    return {"ok": True, "topics": all_topics()}


@router.get("/search")
def search(q: str = Query(..., min_length=1)) -> dict:
    matches = match_topics(q)
    return {
        "ok": True,
        "query": q,
        "matches": matches,
        "note": "This is a topic-registry search stub. Replace with PostgreSQL/pgvector retrieval after indexing pages and references.",
    }

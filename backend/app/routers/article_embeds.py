from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.engines.article_embeds import article_formula_embed_analyzer

router = APIRouter(prefix='/articles', tags=['article-embeds'])


class FormulaEmbedRequest(BaseModel):
    formula: str = Field(default='')
    equation: str = Field(default='')
    input: str = Field(default='')
    context: str = Field(default='')
    article_title: str = Field(default='')
    article_slug: str = Field(default='')
    article: str = Field(default='')
    tool: str = Field(default='')
    preferred_tool: str = Field(default='')
    display: str = Field(default='inline')
    preferred_display: str = Field(default='inline')


@router.post('/formula-embed')
def formula_embed(req: FormulaEmbedRequest) -> dict[str, Any]:
    return article_formula_embed_analyzer(req.model_dump())

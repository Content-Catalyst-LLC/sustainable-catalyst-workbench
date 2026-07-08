from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.core.model_registry import get_tool
from app.routers.equations import _infer_tools

router = APIRouter(prefix='/routing', tags=['routing'])

class ShortcodeRecommendRequest(BaseModel):
    article_title: str = ''
    article_slug: str = ''
    equations: list[str] = Field(default_factory=list)
    context: str = ''

def _confidence(equation_count: int, top_hits: int) -> str:
    if equation_count >= 4 and top_hits >= 3:
        return 'high'
    if equation_count >= 2 and top_hits >= 2:
        return 'medium'
    return 'low'

@router.post('/shortcode-recommend')
def recommend_shortcode(req: ShortcodeRecommendRequest) -> dict[str, Any]:
    tool_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}
    notes: list[str] = []
    for eq in req.equations:
        domain, tools, inferred_notes = _infer_tools(eq, req.context + ' ' + req.article_title)
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        for tool_id in tools:
            tool_counts[tool_id] = tool_counts.get(tool_id, 0) + 1
        notes.extend(inferred_notes[:1])
    if not tool_counts:
        tool_counts = {'systems-modeling-tool': 1}
        domain_counts = {'Mathematical Modeling': 1}
    top_tool, top_hits = sorted(tool_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    domain = sorted(domain_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    spec = get_tool(top_tool) or {'id': top_tool, 'title': top_tool.replace('-', ' ').title()}
    shortcode = f'[sc_workbench mode="tool" tool="{top_tool}" article="{req.article_slug}" title="{spec.get("title", top_tool)} for this article"]'
    return {
        'ok': True,
        'recommended_tool_id': top_tool,
        'recommended_tool_title': spec.get('title', top_tool),
        'primary_domain': domain,
        'confidence': _confidence(len(req.equations), top_hits),
        'embed_shortcode': shortcode,
        'article_shortcode': f'[sc_workbench mode="auto" article="{req.article_slug}"]',
        'equation_count': len(req.equations),
        'reason': 'Recommended from equation-to-tool routing across the supplied article equations.',
        'notes': list(dict.fromkeys(notes))[:5],
        'disclaimer': 'Review recommendations before embedding calculators on public pages.'
    }

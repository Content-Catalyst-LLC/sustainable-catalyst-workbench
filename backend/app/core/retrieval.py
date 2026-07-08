from __future__ import annotations
from .model_registry import search_tools, list_tools

PATHWAYS = [
    {"title":"Systems Reasoning", "url":"/systems-thinking/", "summary":"Feedback, resilience, thresholds, interdependence, and long-term change."},
    {"title":"Scientific and Mathematical Reasoning", "url":"/mathematical-thinking/", "summary":"Symbols, models, probability, statistics, calculus, and interpretation."},
    {"title":"Computational and Algorithmic Reasoning", "url":"/algorithms-computational-reasoning/", "summary":"Formal procedure, data structures, search, optimization, automation, and AI governance."},
    {"title":"Sustainable Human Futures", "url":"/sustainable-development/", "summary":"Development, ecological limits, risk, resilience, energy systems, and governance."},
    {"title":"Engineering and Built Environment", "url":"/energy-systems/", "summary":"Energy, infrastructure, buildings, materials, engineering models, and architecture."},
    {"title":"Psychology and Decision-Making", "url":"/psychology/", "summary":"Cognition, behavior, grit, decision science, motivation, and group life."},
    {"title":"Governance, Ethics, and Meaning", "url":"/global-governance/", "summary":"Institutions, law, ethics, philosophy, symbolic interpretation, and public responsibility."},
    {"title":"Pattern, Geometry, Design, Music, and AI", "url":"/beauty-aesthetics-and-meaning/", "summary":"Music theory, color systems, vector geometry, mathematical pattern, embeddings, multimodal analysis, and design interpretation."},
]

def retrieve_context(question: str, topic: str = 'research-library') -> dict:
    tools = search_tools(' '.join([question or '', topic or '']), limit=6)
    q = (question or '').lower()
    pathways = [p for p in PATHWAYS if any(token in (p['title'] + ' ' + p['summary']).lower() for token in q.split())]
    if not pathways:
        pathways = PATHWAYS[:4]
    return {"tools": tools, "pathways": pathways, "notes": ["Retrieval is currently based on the Workbench model registry and curated pathway map.", "A vector index over published articles can be added as the next production step."]}

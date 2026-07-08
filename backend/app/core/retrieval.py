from __future__ import annotations
from .tool_registry import TOOLS

PATHWAYS = [
    {"id":"systems-thinking","title":"Systems Reasoning","description":"Feedback, resilience, interdependence, thresholds, adaptation, and complexity.","url":"/systems-thinking/"},
    {"id":"mathematical-thinking","title":"Scientific and Mathematical Reasoning","description":"Symbols, variables, models, uncertainty, computation, and interpretation.","url":"/mathematical-thinking/"},
    {"id":"algorithms-computational-reasoning","title":"Computational and Algorithmic Reasoning","description":"Formal procedure, data structures, complexity, search, optimization, simulation, automation, and AI governance.","url":"/algorithms-computational-reasoning/"},
    {"id":"sustainable-development","title":"Sustainable Human Futures","description":"Development, ecological limits, stewardship, resilience, energy systems, governance, and long-term wellbeing.","url":"/sustainable-development/"},
    {"id":"artificial-intelligence-systems","title":"Technology and Systems Intelligence","description":"AI, data systems, monitoring, infrastructure, automation, and public accountability.","url":"/artificial-intelligence-systems/"},
    {"id":"decision-science","title":"Decision and Strategy","description":"Decision quality, uncertainty, tradeoffs, risk, thresholds, and action.","url":"/decision-science/"},
    {"id":"meaning","title":"Meaning and Interpretation","description":"Symbol, story, beauty, myth, ritual, philosophy, religion, cultural memory, and human meaning-making.","url":"/beauty-aesthetics-and-meaning/"},
    {"id":"psychology","title":"Psychology and Behavior","description":"Cognition, social behavior, development, personality, organizations, behavior change, and moral psychology.","url":"/cognitive-psychology/"},
]


def retrieve(question: str, topic: str = ""):
    q = f"{question or ''} {topic or ''}".lower()
    scored_tools=[]
    for t in TOOLS:
        hay=(t["id"]+" "+t["title"]+" "+t["domain"]+" "+t.get("description","")).lower()
        score=sum(1 for token in q.split() if len(token)>3 and token in hay)
        if score or t.get("featured"):
            scored_tools.append((score + (1 if t.get("featured") else 0), t))
    scored_tools=sorted(scored_tools, key=lambda x:x[0], reverse=True)
    matched_paths=[]
    for p in PATHWAYS:
        hay=(p["id"]+" "+p["title"]+" "+p["description"]).lower()
        score=sum(1 for token in q.split() if len(token)>3 and token in hay)
        if score:
            matched_paths.append(p)
    if not matched_paths:
        matched_paths=PATHWAYS[:4]
    return {"tools":[t for _,t in scored_tools[:6]], "pathways":matched_paths[:5]}

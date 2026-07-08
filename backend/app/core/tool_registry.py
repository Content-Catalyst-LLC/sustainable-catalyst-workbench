from __future__ import annotations

TOOLS: list[dict] = [
    {
        "id": "linear-system-solver",
        "title": "Linear Algebra Systems Solver",
        "description": "Solve or diagnose Ax=b systems with rank, determinant, condition number, least-squares fallback, and residual checks.",
        "domain": "Mathematical Modeling",
        "topics": ["mathematical-modeling", "systems-modeling"],
        "type": "calculator",
        "engine": "python_numpy",
        "status": "active",
    },
    {
        "id": "decision-matrix",
        "title": "Decision Matrix",
        "description": "Compare options across weighted criteria with explicit assumptions and tradeoff warnings.",
        "domain": "Problem Solving",
        "topics": ["problem-solving", "decision-science", "thinking"],
        "type": "decision-support",
        "engine": "python",
        "status": "active",
    },
    {
        "id": "risk-resilience-scorecard",
        "title": "Risk & Resilience Scorecard",
        "description": "Assess exposure, sensitivity, adaptive capacity, redundancy, and recovery capacity.",
        "domain": "Sustainable Systems",
        "topics": ["risk-resilience", "sustainable-systems", "systems-modeling"],
        "type": "diagnostic",
        "engine": "python",
        "status": "active",
    },
    {
        "id": "ai-governance-audit",
        "title": "AI Governance Audit",
        "description": "Screen AI systems for transparency, oversight, data quality, contestability, and harm risk.",
        "domain": "Technology & Systems Intelligence",
        "topics": ["artificial-intelligence-systems", "technology-systems-intelligence", "decision-science"],
        "type": "audit",
        "engine": "python",
        "status": "active",
    },
    {
        "id": "sustainability-tradeoff-matrix",
        "title": "Sustainability Tradeoff Matrix",
        "description": "Compare sustainability options across environmental, social, economic, governance, and resilience criteria.",
        "domain": "Sustainable Systems",
        "topics": ["sustainable-systems", "risk-resilience", "economic-systems"],
        "type": "hybrid",
        "engine": "python",
        "status": "active",
    },
    {
        "id": "qualitative-interpretation-matrix",
        "title": "Qualitative Interpretation Matrix",
        "description": "Structure interpretive analysis across themes, symbols, institutions, narratives, tensions, and limitations.",
        "domain": "Meaning",
        "topics": ["meaning", "mythology", "literature-cultural-memory", "religious-studies", "philosophy", "cultural-anthropology"],
        "type": "interpretive",
        "engine": "structured_qualitative",
        "status": "active",
    },
    {
        "id": "research-library-assistant",
        "title": "Research Library Assistant",
        "description": "Guide users through Sustainable Catalyst topics, article maps, research paths, and related tools.",
        "domain": "Research Library",
        "topics": ["global-governance", "sustainable-systems", "technology-systems-intelligence", "natural-science", "thinking", "meaning", "problem-solving"],
        "type": "ai-guide",
        "engine": "site_scoped_ai_stub",
        "status": "active",
    },
    {
        "id": "workbench-tool-finder",
        "title": "Workbench Tool Finder",
        "description": "Route a user problem to the most relevant calculator, diagnostic, model, matrix, or interpretive framework.",
        "domain": "Research Library",
        "topics": ["thinking", "problem-solving", "mathematical-modeling", "systems-modeling"],
        "type": "router",
        "engine": "site_scoped_ai_stub",
        "status": "active",
    },
]


def list_tools(topic: str | None = None, domain: str | None = None) -> list[dict]:
    items = TOOLS
    if topic:
        topic = topic.strip().lower()
        items = [tool for tool in items if topic in tool.get("topics", [])]
    if domain:
        domain = domain.strip().lower()
        items = [tool for tool in items if domain in tool.get("domain", "").lower()]
    return items


def get_tool(tool_id: str) -> dict | None:
    return next((tool for tool in TOOLS if tool["id"] == tool_id), None)

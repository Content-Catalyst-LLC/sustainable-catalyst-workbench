from __future__ import annotations
import re

ALLOWED_TOPICS = {
    "research", "library", "sustainable", "sustainability", "systems systems thinking systems modeling limits growth world3 stocks flows feedback", "system", "governance", "law", "legal",
    "technology", "artificial intelligence", "ai", "data", "analytics", "science", "physics", "biology", "chemistry", "nuclear", "particle", "relativistic", "neurophysics", "biophysics", "rocket", "orbital", "aerospace", "electronics", "circuit", "rf", "antenna", "wireless", "lab", "laboratory", "assay", "qpcr", "clinical research", "diagnostic metrics",
    "materials", "earth", "astronomy astrophysics", "environmental", "psychology cognitive social developmental personality positive organizational institutional analytical behavioral moral", "cognitive", "social", "developmental",
    "personality", "positive", "grit", "behavior", "behaviour", "behavioral", "organization", "institutional",
    "moral", "philosophy", "ethics", "meaning beauty aesthetics art music pattern symbolism story myth creative form", "story", "myth", "religion", "anthropology", "literature",
    "culture", "decision", "strategy", "model", "modeling", "modelling", "calculus", "linear algebra", "probability",
    "statistics", "differential", "economics predictive analytics econometrics macroeconomic forecasting", "energy", "engineering FPGA RTL VHDL Verilog electrical power systems systems thinking systems modeling limits growth world3 stocks flows feedback structural civil infrastructure urban planning building science", "architecture", "building", "bim", "resilience",
    "risk", "climate", "carbon", "emissions", "optimization", "simulation", "network", "graph", "algorithm",
    "pattern", "geometry", "vector", "music", "chord", "scale", "frequency", "color", "palette", "contrast", "design", "aesthetics", "embedding", "multimodal", "fourier", "pca",
}

OUT_OF_SCOPE_HINTS = {
    "celebrity gossip", "sports betting", "dating advice", "recipe", "gaming cheats", "make money fast",
}

DOMAIN_TAGS = {
    "science": ["physics", "biology", "chemistry", "materials", "earth", "astronomy astrophysics", "environmental"],
    "psychology cognitive social developmental personality positive organizational institutional analytical behavioral moral": ["psychology cognitive social developmental personality positive organizational institutional analytical behavioral moral", "cognitive", "social", "developmental", "personality", "positive", "grit", "behavioral"],
    "engineering FPGA RTL VHDL Verilog electrical power systems systems thinking systems modeling limits growth world3 stocks flows feedback structural civil infrastructure urban planning building science_architecture": ["engineering FPGA RTL VHDL Verilog electrical power systems systems thinking systems modeling limits growth world3 stocks flows feedback structural civil infrastructure urban planning building science", "architecture", "building", "bim", "energy", "materials", "structural"],
    "economics predictive analytics econometrics macroeconomic forecasting_energy": ["economics predictive analytics econometrics macroeconomic forecasting", "elasticity", "npv", "energy", "emissions", "cost", "demand", "supply"],
    "governance_meaning beauty aesthetics art music pattern symbolism story myth creative form": ["governance", "law", "ethics", "meaning beauty aesthetics art music pattern symbolism story myth creative form", "myth", "religion", "culture", "philosophy"],
    "math_decision": ["calculus", "linear algebra", "probability", "statistics", "decision", "optimization", "modeling"],
    "pattern_design_ai": ["pattern", "geometry", "vector", "music", "color", "palette", "design", "embedding", "fourier", "pca", "multimodal"],
}

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())

def classify_scope(text: str, topic: str | None = None) -> dict:
    blob = normalize(" ".join([topic or "", text or ""]))
    if not blob:
        return {"in_scope": True, "score": 0.2, "matched": ["research-library"], "domains": ["research-library"]}
    blocked = [h for h in OUT_OF_SCOPE_HINTS if h in blob]
    matches = sorted({t for t in ALLOWED_TOPICS if t in blob})
    domains = [d for d, keys in DOMAIN_TAGS.items() if any(k in blob for k in keys)]
    score = min(1.0, 0.15 + 0.09 * len(matches) + 0.15 * len(domains))
    in_scope = bool(matches or domains) and not blocked
    # Research Library assistant should allow broad exploratory questions when a topic is provided.
    if topic and normalize(topic) in {"research-library", "sustainable-catalyst", "workbench"} and not blocked:
        in_scope = True
        score = max(score, 0.55)
    return {"in_scope": in_scope, "score": round(score, 3), "matched": matches[:15], "domains": domains or ["research-library"], "blocked": blocked}

def out_of_scope_message() -> str:
    return "That question is outside the Sustainable Catalyst knowledge map. I can help if you connect it to sustainability, systems systems thinking systems modeling limits growth world3 stocks flows feedback thinking, science, engineering FPGA RTL VHDL Verilog electrical power systems systems thinking systems modeling limits growth world3 stocks flows feedback structural civil infrastructure urban planning building science, architecture, psychology cognitive social developmental personality positive organizational institutional analytical behavioral moral, economics predictive analytics econometrics macroeconomic forecasting, governance, meaning beauty aesthetics art music pattern symbolism story myth creative form, music, color, geometry, design, AI representation, modeling, or decision-making."

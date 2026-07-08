from __future__ import annotations

from typing import Any

CRITERIA = ["environmental", "social", "economic", "governance", "resilience"]


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    options = inputs.get("options", [])
    weights = inputs.get("weights", {criterion: 1 for criterion in CRITERIA})
    if not options:
        raise ValueError("options are required")
    total_weight = sum(float(weights.get(c, 0.0)) for c in CRITERIA) or 1.0

    ranking = []
    for option in options:
        scores = option.get("scores", {})
        weighted = {}
        total = 0.0
        for criterion in CRITERIA:
            value = float(scores.get(criterion, 0.0))
            contribution = value * float(weights.get(criterion, 0.0)) / total_weight
            weighted[criterion] = contribution
            total += contribution
        ranking.append({"name": option.get("name", "Unnamed option"), "score": total, "weighted_breakdown": weighted})

    ranking.sort(key=lambda item: item["score"], reverse=True)
    warnings = []
    if ranking and ranking[0]["score"] < 5:
        warnings.append("The leading option still scores weakly overall; consider redesign rather than selection among poor alternatives.")

    return {
        "result": {"ranking": ranking, "criteria": CRITERIA, "weights": weights},
        "warnings": warnings,
        "interpretation": "Sustainability tradeoffs are not purely technical. Use this matrix to expose tensions, then review assumptions, distributional effects, and long-term resilience.",
    }

from __future__ import annotations

from typing import Any


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    criteria = inputs.get("criteria", [])
    options = inputs.get("options", [])
    if not criteria or not options:
        raise ValueError("criteria and options are required")

    weights = {item["name"]: float(item.get("weight", 1.0)) for item in criteria}
    directions = {item["name"]: item.get("direction", "higher_is_better") for item in criteria}
    total_weight = sum(weights.values()) or 1.0

    scored = []
    warnings: list[str] = []
    for option in options:
        raw_scores = option.get("scores", {})
        total = 0.0
        detail = {}
        for name, weight in weights.items():
            score = float(raw_scores.get(name, 0.0))
            if directions.get(name) == "lower_is_better":
                adjusted = 10.0 - score
            else:
                adjusted = score
            contribution = adjusted * (weight / total_weight)
            total += contribution
            detail[name] = {"raw": score, "adjusted": adjusted, "weighted_contribution": contribution}
        scored.append({"name": option.get("name", "Unnamed option"), "score": total, "details": detail})

    scored.sort(key=lambda item: item["score"], reverse=True)
    if len(scored) > 1 and abs(scored[0]["score"] - scored[1]["score"]) < 0.5:
        warnings.append("The top options are close; test sensitivity to weights before making a decision.")

    return {
        "result": {"ranking": scored, "criteria": criteria},
        "warnings": warnings,
        "interpretation": "The matrix makes tradeoffs explicit. It supports judgment but should not replace evidence review, stakeholder analysis, or uncertainty testing.",
    }

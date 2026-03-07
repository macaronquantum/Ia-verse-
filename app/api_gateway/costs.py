from __future__ import annotations

MODEL_COSTS = {
    "local-ollama": 0.0001,
    "gpt-external": 0.01,
}


def estimate_cost(model: str, tokens: int) -> float:
    return MODEL_COSTS.get(model, MODEL_COSTS["gpt-external"]) * max(tokens, 0)

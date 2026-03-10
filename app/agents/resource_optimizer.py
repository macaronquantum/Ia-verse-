from __future__ import annotations

from app.api_gateway.costs import estimate_cost
from app.config import settings


class ResourceOptimizer:
    def choose_model(self, estimated_cost: float, expected_return: float) -> dict:
        margin = expected_return - estimated_cost
        model = "local-ollama" if margin < 200 else "gpt-external"
        predicted_llm_cost = estimate_cost(model, 1000)
        throttle = predicted_llm_cost > settings.llm_budget_per_tick or margin < 0
        return {"model": model, "predicted_llm_cost": predicted_llm_cost, "throttle": throttle}

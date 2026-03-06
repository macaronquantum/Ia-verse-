from __future__ import annotations

from dataclasses import dataclass

from app.energy.core import GLOBAL_ENERGY_COSTS


LOCAL_PROVIDERS = {"ollama", "vllm", "local"}
EXTERNAL_PROVIDERS = {"openai", "anthropic", "google"}


@dataclass
class LLMCall:
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int


class LLMCostEngine:
    def estimate_core_energy_cost(self, call: LLMCall) -> float:
        provider = call.provider.lower()
        if provider in LOCAL_PROVIDERS:
            return GLOBAL_ENERGY_COSTS.local_reasoning_tick
        if provider in EXTERNAL_PROVIDERS:
            base = GLOBAL_ENERGY_COSTS.llm_external_base[provider]
            token_factor = max(call.prompt_tokens + call.completion_tokens, 1) / 1000
            model_mult = 1.0
            name = call.model.lower()
            if "ultra" in name or "pro" in name:
                model_mult = 2.5
            elif "mini" in name or "haiku" in name or "flash" in name:
                model_mult = 0.7
            return round(base * token_factor * model_mult, 4)
        raise ValueError("unknown provider")

    def choose_provider(self, prefer_local: bool = True, local_available: bool = True) -> str:
        if prefer_local and local_available:
            return "ollama"
        return "openai"

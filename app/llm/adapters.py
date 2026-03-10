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


@dataclass
class LLMResult:
    text: str = ""
    tokens: int = 0


class HybridLLMAdapter:
    def __init__(self, provider: str = "local", model: str = "default") -> None:
        self.provider = provider
        self.model = model
        self.token_cost_energy = GLOBAL_ENERGY_COSTS.local_reasoning_tick

    def generate(self, prompt: str) -> LLMResult:
        return LLMResult(text=f"[simulated response to: {prompt[:50]}]", tokens=100)

    async def complete(self, prompt: str, depth: float = 1.0) -> tuple[str, bool]:
        use_external = depth > 0.5 and self.provider not in LOCAL_PROVIDERS
        text = f"[simulated: {prompt[:50]}]"
        return text, use_external


class ModelRouter:
    def __init__(self) -> None:
        self._adapters: dict[str, HybridLLMAdapter] = {}

    def for_tier(self, tier: str) -> HybridLLMAdapter:
        if tier not in self._adapters:
            self._adapters[tier] = HybridLLMAdapter(provider="local", model=f"{tier}_model")
        return self._adapters[tier]

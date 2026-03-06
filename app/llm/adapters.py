from __future__ import annotations

from dataclasses import dataclass

from app.models import AgentTier


@dataclass
class LLMResult:
    model: str
    tokens: int
    output: str


class BaseLLMAdapter:
    model_name = "base"
    token_cost_energy = 0.00001

    def generate(self, prompt: str) -> LLMResult:
        tokens = max(20, len(prompt.split()) * 3)
        return LLMResult(model=self.model_name, tokens=tokens, output=f"[{self.model_name}] {prompt[:120]}")


class OllamaAdapter(BaseLLMAdapter):
    model_name = "ollama:qwen2.5"


class ExternalAdapter(BaseLLMAdapter):
    model_name = "external:gpt-4o-mini"
    token_cost_energy = 0.00003


class ModelRouter:
    def for_tier(self, tier: AgentTier) -> BaseLLMAdapter:
        if tier in {AgentTier.BANK, AgentTier.CENTRAL_BANK, AgentTier.SYSTEM}:
            return ExternalAdapter()
        return OllamaAdapter()

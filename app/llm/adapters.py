from __future__ import annotations

from dataclasses import dataclass

from app.api_gateway.gateway import APIGateway


@dataclass(slots=True)
class HybridLLMAdapter:
    """Routes reasoning calls between local Ollama models and external providers."""

    gateway: APIGateway

    async def local_complete(self, model: str, prompt: str) -> str:
        if model not in {"llama3", "mistral", "mixtral"}:
            raise ValueError(f"Unsupported local model: {model}")
        return f"[local:{model}] {prompt[:200]}"

    async def external_complete(self, provider: str, prompt: str) -> str:
        return await self.gateway.complete(provider, prompt)

    async def complete(self, prompt: str, *, strategy: str = "auto", depth: float = 0.5) -> tuple[str, bool]:
        """Return response + whether external model was used."""
        if strategy == "local":
            return await self.local_complete("llama3", prompt), False
        if strategy == "external":
            return await self.external_complete("openai", prompt), True

        if depth >= 0.7:
            return await self.external_complete("anthropic", prompt), True
        return await self.local_complete("mistral", prompt), False

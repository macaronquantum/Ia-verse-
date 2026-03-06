from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class APIGateway:
    """Fallback gateway for external LLM providers."""

    openai_enabled: bool = True
    anthropic_enabled: bool = True
    google_enabled: bool = True

    async def complete(self, provider: str, prompt: str) -> str:
        enabled = {
            "openai": self.openai_enabled,
            "anthropic": self.anthropic_enabled,
            "google": self.google_enabled,
        }
        if provider not in enabled or not enabled[provider]:
            raise ValueError(f"Provider unavailable: {provider}")
        # Stub response for deterministic simulation tests.
        return f"[{provider}] {prompt[:200]}"

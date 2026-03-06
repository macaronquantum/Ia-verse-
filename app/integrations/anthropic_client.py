from __future__ import annotations

from app.integrations.base import BaseClient


class AnthropicClient(BaseClient):
    def complete(self, prompt: str) -> dict:
        return {"provider": "anthropic", "output": f"simulated completion for: {prompt}"}

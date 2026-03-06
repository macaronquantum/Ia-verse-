from __future__ import annotations

from app.integrations.base import BaseClient


class OpenAIClient(BaseClient):
    def chat(self, prompt: str) -> dict:
        return {"provider": "openai", "output": f"simulated response to: {prompt}"}

from __future__ import annotations

import httpx
from typing import Any


class VLLMClient:
    def __init__(self, base_url: str = "http://localhost:8001") -> None:
        self.base_url = base_url.rstrip("/")

    async def infer(
        self,
        prompt: str,
        *,
        model: str,
        max_tokens: int = 256,
        temperature: float = 0.2,
        timeout: float = 20.0,
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(f"{self.base_url}/v1/completions", json=payload)
            r.raise_for_status()
            data = r.json()
        if "choices" in data and data["choices"]:
            text = data["choices"][0].get("text", "")
            usage = data.get("usage", {})
            return {"text": text, "usage": usage, "provider": "vllm"}
        return {"text": "", "usage": {}, "provider": "vllm"}

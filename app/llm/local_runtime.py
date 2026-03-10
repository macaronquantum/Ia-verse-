from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


@dataclass
class LocalRuntimeStatus:
    ollama_available: bool
    vllm_available: bool


class LocalLLMRuntime:
    def __init__(self, ollama_host: str | None = None, vllm_endpoint: str | None = None) -> None:
        self.ollama_host = (ollama_host or settings.OLLAMA_HOST).rstrip("/")
        self.vllm_endpoint = (vllm_endpoint or settings.VLLM_ENDPOINT).rstrip("/")

    async def detect(self) -> LocalRuntimeStatus:
        async with httpx.AsyncClient(timeout=2.0) as client:
            ollama = await self._is_up(client, f"{self.ollama_host}/api/tags")
            vllm = await self._is_up(client, f"{self.vllm_endpoint}/health")
        return LocalRuntimeStatus(ollama_available=ollama, vllm_available=vllm)

    async def _is_up(self, client: httpx.AsyncClient, url: str) -> bool:
        try:
            response = await client.get(url)
            return response.status_code < 500
        except Exception:
            return False

    async def infer(self, prompt: str, model: str = "mistral", **kwargs: Any) -> dict[str, Any]:
        status = await self.detect()
        if status.ollama_available:
            return await self._infer_ollama(prompt, model=model, **kwargs)
        if status.vllm_available:
            return await self._infer_vllm(prompt, model=model, **kwargs)
        raise RuntimeError("no local llm runtime available")

    async def _infer_ollama(self, prompt: str, model: str, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.2),
                "num_predict": kwargs.get("max_tokens", 256),
            },
        }
        async with httpx.AsyncClient(timeout=kwargs.get("timeout", settings.LOCAL_MODEL_TIMEOUT)) as client:
            response = await client.post(f"{self.ollama_host}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return {"text": data.get("response", ""), "usage": data.get("eval_count", 0), "backend": "ollama"}

    async def _infer_vllm(self, prompt: str, model: str, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 256),
            "temperature": kwargs.get("temperature", 0.2),
        }
        async with httpx.AsyncClient(timeout=kwargs.get("timeout", settings.LOCAL_MODEL_TIMEOUT)) as client:
            response = await client.post(f"{self.vllm_endpoint}/v1/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            text = ((data.get("choices") or [{}])[0]).get("text", "")
            return {"text": text, "usage": data.get("usage", {}), "backend": "vllm"}


def infer_sync(prompt: str, model: str = "mistral", **kwargs: Any) -> dict[str, Any]:
    return asyncio.run(LocalLLMRuntime().infer(prompt=prompt, model=model, **kwargs))

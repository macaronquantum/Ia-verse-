from __future__ import annotations

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.llm.provider_local_vllm import VLLMClient


@dataclass
class ModelSpec:
    name: str
    source: str
    repo: str
    quant: str = "4bit"
    device: str = "cuda:0"
    backend: str = "vllm"
    path: str | None = None
    memory_estimate_gb: float = 8.0


class OllamaClient:
    def __init__(self, host: str | None = None) -> None:
        self.host = host or settings.OLLAMA_HOST

    async def pull(self, model: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{self.host}/api/pull", json={"name": model, "stream": False})
            r.raise_for_status()
            return r.json()

    async def infer(self, prompt: str, model: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=kwargs.get("timeout", 30)) as client:
            r = await client.post(f"{self.host}/api/generate", json={"model": model, "prompt": prompt, "stream": False})
            r.raise_for_status()
            j = r.json()
            return {"text": j.get("response", ""), "usage": {"completion_tokens": j.get("eval_count", 0)}}


class LocalModelManager:
    """Manage local model lifecycle and bounded-concurrency inference."""

    def __init__(self, models: list[dict[str, Any]] | None = None, cache_dir: str | None = None) -> None:
        self.cache_dir = Path(cache_dir or settings.MODEL_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        raw_models = models or settings.LOCAL_MODELS
        self.registry: dict[str, ModelSpec] = {m["name"]: ModelSpec(**m) for m in raw_models}
        self.max_concurrency = settings.MODEL_MAX_CONCURRENCY
        self._semaphores = {name: asyncio.Semaphore(self.max_concurrency) for name in self.registry}
        self._clients: dict[str, Any] = {}

    async def download_model(self, model_name: str, quant: str | None = None) -> str:
        spec = self.registry[model_name]
        model_dir = self.cache_dir / model_name
        model_dir.mkdir(parents=True, exist_ok=True)

        if spec.backend == "ollama" or spec.source == "ollama":
            client = OllamaClient()
            await client.pull(spec.repo)

        meta = {
            "name": spec.name,
            "source": spec.source,
            "repo": spec.repo,
            "quant": quant or spec.quant,
            "downloaded_at": int(time.time()),
        }
        (model_dir / "model.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return str(model_dir)

    def install_model(self, name: str, source: str, repo: str, backend: str = "ollama") -> ModelSpec:
        spec = ModelSpec(name=name, source=source, repo=repo, backend=backend)
        self.registry[name] = spec
        self._semaphores[name] = asyncio.Semaphore(self.max_concurrency)
        return spec

    def _load_backend(self, spec: ModelSpec) -> Any:
        if spec.backend == "vllm":
            return VLLMClient()
        if spec.backend == "ollama":
            return OllamaClient()

        class _Fallback:
            async def infer(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
                return {"text": f"local-fallback:{prompt[:80]}", "usage": {"completion_tokens": 16}}

        return _Fallback()

    def ensure_loaded(self, model_name: str) -> None:
        if model_name in self._clients:
            return
        spec = self.registry[model_name]
        self._clients[model_name] = self._load_backend(spec)

    def switch_model(self, current: str, candidate: str) -> str:
        if candidate not in self.registry:
            raise ValueError(f"unknown model: {candidate}")
        if current in self._clients:
            self._clients.pop(current, None)
        self.ensure_loaded(candidate)
        return candidate

    async def infer(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.2,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        if model_name not in self.registry:
            raise ValueError(f"unknown model: {model_name}")
        self.ensure_loaded(model_name)
        timeout = timeout or settings.LOCAL_MODEL_TIMEOUT
        async with self._semaphores[model_name]:
            call = self._clients[model_name].infer(
                prompt,
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
            )
            return await asyncio.wait_for(call, timeout=timeout)

    def serve_model_locally(self, model_name: str) -> subprocess.Popen[str]:
        spec = self.registry[model_name]
        if spec.backend != "ollama":
            raise ValueError("serve_model_locally currently supports ollama backend")
        return subprocess.Popen(["ollama", "run", spec.repo], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

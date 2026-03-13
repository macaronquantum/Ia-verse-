from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx


class AIMarketplaceClient:
    def __init__(self, token: str | None = None, cache_dir: str = "models/external") -> None:
        self.token = token or os.getenv("HUGGINGFACE_TOKEN", "")
        self.base_url = "https://huggingface.co/api"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def search_models(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}/models", params={"search": query, "limit": limit})
            r.raise_for_status()
            return r.json()

    async def download_model(self, repo_id: str) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(f"{self.base_url}/models/{repo_id}")
            r.raise_for_status()
            model_dir = self.cache_dir / repo_id.replace("/", "__")
            model_dir.mkdir(parents=True, exist_ok=True)
            (model_dir / "manifest.json").write_text(r.text, encoding="utf-8")
            return str(model_dir)

    def install_model(self, repo_id: str, local_path: str) -> dict[str, str]:
        return {"repo_id": repo_id, "path": local_path, "installed": "true"}

    def register_tool(self, tool_registry: Any, tool_id: str, entrypoint: str, capabilities: list[str]) -> dict[str, Any]:
        record = tool_registry.register_tool(tool_id=tool_id, creator_agent="ai-marketplace", entrypoint=entrypoint, capabilities=capabilities)
        return {"tool_id": record.tool_id, "version": record.version}

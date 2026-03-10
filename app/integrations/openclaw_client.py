from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass
class OpenClawClient:
    endpoint: str

    @property
    def enabled(self) -> bool:
        return bool(self.endpoint)

    async def _call(self, path: str, payload: dict) -> dict:
        if not self.enabled:
            return {"status": "disabled", "reason": "OPENCLAW_ENDPOINT not set"}
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(f"{self.endpoint.rstrip('/')}/{path.lstrip('/')}", json=payload)
            res.raise_for_status()
            return res.json()

    async def browse(self, url: str) -> dict:
        return await self._call("browse", {"url": url})

    async def create_account(self, provider: str, payload: dict) -> dict:
        return await self._call("accounts/create", {"provider": provider, "payload": payload})

    async def automate(self, workflow: dict) -> dict:
        return await self._call("workflow/run", {"workflow": workflow})

    async def scrape(self, url: str, selectors: dict) -> dict:
        return await self._call("scrape", {"url": url, "selectors": selectors})

    async def run_tool(self, tool: str, args: dict) -> dict:
        return await self._call("tools/execute", {"tool": tool, "args": args})

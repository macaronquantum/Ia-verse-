from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BrowserAgent:
    headless: bool = True

    async def create_account(self, url: str, fields: dict[str, Any]) -> dict[str, Any]:
        return {"status": "queued", "action": "create_account", "url": url, "fields": fields}

    async def navigate(self, url: str) -> dict[str, Any]:
        return {"status": "ok", "action": "navigate", "url": url}

    async def fill_form(self, form_selector: str, fields: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "action": "fill_form", "form_selector": form_selector, "fields": fields}

    async def post_content(self, url: str, content: str) -> dict[str, Any]:
        return {"status": "ok", "action": "post_content", "url": url, "content": content}

    async def gather_data(self, url: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "action": "gather_data", "url": url, "schema": schema, "rows": []}

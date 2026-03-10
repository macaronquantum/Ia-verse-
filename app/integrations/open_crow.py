from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.config import settings
from app.integrations.openclaw_client import OpenClawClient


@dataclass
class OpenCrowController:
    base_url: str = ""

    def __post_init__(self) -> None:
        endpoint = self.base_url or settings.OPENCLAW_ENDPOINT
        self.client = OpenClawClient(endpoint=endpoint)

    def create_account(self, username: str, email: str) -> dict:
        return asyncio.run(self.client.create_account("generic", {"username": username, "email": email}))

    def navigate(self, url: str) -> dict:
        return asyncio.run(self.client.browse(url))

    def submit_form(self, form_id: str, payload: dict) -> dict:
        return asyncio.run(self.client.automate({"action": "submit_form", "form_id": form_id, "payload": payload}))

    def post_message(self, channel: str, message: str) -> dict:
        return asyncio.run(self.client.run_tool("post_message", {"channel": channel, "message": message}))

    def download_asset(self, asset_url: str) -> dict:
        return asyncio.run(self.client.scrape(asset_url, {"asset": "body"}))

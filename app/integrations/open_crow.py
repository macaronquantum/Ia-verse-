from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OpenCrowController:
    base_url: str = "https://opencrow.local"

    def create_account(self, username: str, email: str) -> dict:
        return {"status": "ok", "username": username, "email": email}

    def navigate(self, url: str) -> dict:
        return {"status": "ok", "url": url}

    def submit_form(self, form_id: str, payload: dict) -> dict:
        return {"status": "ok", "form_id": form_id, "payload": payload}

    def post_message(self, channel: str, message: str) -> dict:
        return {"status": "ok", "channel": channel, "message": message}

    def download_asset(self, asset_url: str) -> dict:
        return {"status": "ok", "asset_url": asset_url}

from __future__ import annotations

from app.integrations.base import BaseClient


class TwilioClient(BaseClient):
    def send_sms(self, to: str, body: str) -> dict:
        return {"to": to, "body": body, "sid": "SM123", "status": "queued"}

    def create_call(self, to: str) -> dict:
        return {"to": to, "call_sid": "CA123", "status": "ringing"}

from __future__ import annotations

from app.integrations.base import BaseClient


class GoogleClient(BaseClient):
    def create_calendar_event(self, title: str) -> dict:
        return {"event_id": f"evt-{title}", "status": "created"}

    def send_gmail(self, to: str, subject: str) -> dict:
        return {"to": to, "subject": subject, "status": "queued"}

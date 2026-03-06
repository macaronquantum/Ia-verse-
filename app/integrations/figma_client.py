from __future__ import annotations

from app.integrations.base import BaseClient


class FigmaClient(BaseClient):
    def create_file(self, name: str) -> dict:
        return {"file_id": f"fig-{name}", "status": "created"}

    def export(self, file_id: str, fmt: str = "png") -> dict:
        return {"file_id": file_id, "format": fmt, "url": f"https://figma.local/{file_id}.{fmt}"}

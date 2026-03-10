from __future__ import annotations

from app.integrations.base import BaseClient


class AWSClient(BaseClient):
    def create_instance(self, instance_type: str) -> dict:
        return {"instance_id": "i-simulated", "instance_type": instance_type, "status": "running"}

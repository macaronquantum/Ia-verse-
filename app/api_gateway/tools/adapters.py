from __future__ import annotations

from typing import Any


class ToolAdapter:
    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "ok", "payload": payload}

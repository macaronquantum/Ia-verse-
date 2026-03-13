from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class ToolRecord:
    tool_id: str
    creator_agent: str
    version: str
    entrypoint: str
    capabilities: list[str]
    created_at: float


class ToolRegistry:
    def __init__(self, registry_path: str = "data/tool_registry.json") -> None:
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, ToolRecord] = {}
        if self.registry_path.exists():
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
            self._records = {k: ToolRecord(**v) for k, v in data.items()}

    def register_tool(self, tool_id: str, creator_agent: str, entrypoint: str, capabilities: list[str], version: str = "1.0.0") -> ToolRecord:
        rec = ToolRecord(
            tool_id=tool_id,
            creator_agent=creator_agent,
            version=version,
            entrypoint=entrypoint,
            capabilities=capabilities,
            created_at=time.time(),
        )
        self._records[tool_id] = rec
        self._persist()
        return rec

    def discover(self, capability: str) -> list[ToolRecord]:
        return [r for r in self._records.values() if capability in r.capabilities]

    def share_with_agent(self, tool_id: str, target_agent: str) -> dict[str, Any]:
        if tool_id not in self._records:
            raise KeyError(tool_id)
        return {"tool_id": tool_id, "target_agent": target_agent, "granted": True}

    def _persist(self) -> None:
        self.registry_path.write_text(
            json.dumps({k: asdict(v) for k, v in self._records.items()}, indent=2),
            encoding="utf-8",
        )

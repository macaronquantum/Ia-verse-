from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PermissionManager:
    allowed_tools: set[str] = field(default_factory=set)
    audit_log: list[dict] = field(default_factory=list)

    def can_use_tool(self, tool: str) -> bool:
        return tool in self.allowed_tools

    def record_event(self, actor: str, action: str, allowed: bool) -> None:
        self.audit_log.append({"ts": datetime.utcnow().isoformat(), "actor": actor, "action": action, "allowed": allowed})

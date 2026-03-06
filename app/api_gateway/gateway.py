from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Permission:
    can_web_request: bool = False
    can_llm_call: bool = False
    can_blockchain_call: bool = False


@dataclass
class APIGateway:
    permissions: dict[str, Permission] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)

    def register_agent(self, agent_id: str, permission: Permission) -> None:
        self.permissions[agent_id] = permission

    def request(self, agent_id: str, capability: str, payload: dict) -> dict:
        perm = self.permissions.get(agent_id, Permission())
        allowed = {
            "web": perm.can_web_request,
            "llm": perm.can_llm_call,
            "blockchain": perm.can_blockchain_call,
        }.get(capability, False)
        event = f"agent={agent_id} capability={capability} allowed={allowed}"
        self.logs.append(event)
        if not allowed:
            return {"status": "denied", "event": event}
        return {"status": "ok", "event": event, "sandbox": True, "payload": payload}

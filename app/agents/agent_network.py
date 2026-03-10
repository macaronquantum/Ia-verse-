from __future__ import annotations

from uuid import uuid4

from app.models import AgentMessage, World


class AgentNetwork:
    def send_message(
        self,
        world: World,
        sender_agent_id: str,
        recipient_agent_id: str,
        message_type: str,
        content: str,
    ) -> str:
        msg = AgentMessage(
            id=str(uuid4()),
            sender_agent_id=sender_agent_id,
            recipient_agent_id=recipient_agent_id,
            message_type=message_type,
            content=content,
        )
        world.agent_network_messages.append(msg)
        return msg.id

    def fetch_inbox(self, world: World, agent_id: str) -> list[AgentMessage]:
        return [m for m in world.agent_network_messages if m.recipient_agent_id == agent_id]

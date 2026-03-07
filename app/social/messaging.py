from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from app.social.network import DependencyGraph, InfluenceGraph, TrustGraph


@dataclass
class Message:
    sender_id: str
    receiver_id: str
    type: str
    payload: Dict[str, object]


class CommunicationHub:
    def __init__(self, trust: TrustGraph, influence: InfluenceGraph, dependency: DependencyGraph) -> None:
        self.trust = trust
        self.influence = influence
        self.dependency = dependency
        self.history: list[Message] = []

    def negotiate(self, sender_id: str, receiver_id: str, topic: str, concession: float) -> Message:
        self.trust.adjust(sender_id, receiver_id, 0.02 + concession * 0.05)
        message = Message(sender_id, receiver_id, "negotiate", {"topic": topic, "concession": concession})
        self.history.append(message)
        return message

    def ally(self, sender_id: str, receiver_id: str, pact: str) -> Message:
        self.trust.adjust(sender_id, receiver_id, 0.08)
        self.influence.adjust(sender_id, receiver_id, 0.05)
        message = Message(sender_id, receiver_id, "ally", {"pact": pact})
        self.history.append(message)
        return message

    def threaten(self, sender_id: str, receiver_id: str, reason: Optional[str] = None) -> Message:
        self.trust.adjust(sender_id, receiver_id, -0.12)
        self.dependency.adjust(receiver_id, sender_id, 0.04)
        message = Message(sender_id, receiver_id, "threaten", {"reason": reason or "resource conflict"})
        self.history.append(message)
        return message

    def spread_beliefs(self, sender_id: str, receiver_id: str, belief: str, strength: float) -> Message:
        self.influence.adjust(sender_id, receiver_id, 0.03 * strength)
        message = Message(sender_id, receiver_id, "spread_beliefs", {"belief": belief, "strength": strength})
        self.history.append(message)
        return message

    def manipulate_reputation(self, sender_id: str, receiver_id: str, target_id: str, impact: float) -> Message:
        self.influence.adjust(sender_id, receiver_id, 0.02)
        message = Message(
            sender_id,
            receiver_id,
            "manipulate_reputation",
            {"target_id": target_id, "impact": impact},
        )
        self.history.append(message)
        return message

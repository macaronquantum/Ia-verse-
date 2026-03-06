from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.models import Action


@dataclass
class Ruling:
    agent_id: str
    penalty: str
    reason: str


class JudgeAI:
    """Transparent compliance engine with deterministic, auditable rulings."""

    def review(self, actions: Iterable[Action]) -> list[Ruling]:
        rulings: list[Ruling] = []
        for action in actions:
            if action.action_type == "mint_energy":
                rulings.append(
                    Ruling(
                        agent_id=action.actor_id,
                        penalty="freeze_accounts",
                        reason="Unauthorized minting attempt detected in immutable action log.",
                    )
                )
            if action.payload.get("value", 0) < 0:
                rulings.append(
                    Ruling(
                        agent_id=action.actor_id,
                        penalty="fine",
                        reason="Negative reported value indicates manipulative accounting.",
                    )
                )
        return rulings

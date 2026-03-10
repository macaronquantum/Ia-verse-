from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class MemoryEntry:
    timestamp: datetime
    kind: str
    payload: dict[str, Any]


@dataclass(slots=True)
class AgentMemory:
    """Lightweight memory split into short/long/economic channels."""

    short_term_limit: int = 50
    short_term: deque[MemoryEntry] = field(default_factory=deque)
    long_term: list[MemoryEntry] = field(default_factory=list)
    economic_history: list[MemoryEntry] = field(default_factory=list)

    def add_short_term(self, kind: str, payload: dict[str, Any]) -> None:
        self.short_term.append(MemoryEntry(datetime.utcnow(), kind, payload))
        while len(self.short_term) > self.short_term_limit:
            self.short_term.popleft()

    def add_long_term(self, kind: str, payload: dict[str, Any]) -> None:
        self.long_term.append(MemoryEntry(datetime.utcnow(), kind, payload))

    def add_economic_event(self, kind: str, payload: dict[str, Any]) -> None:
        self.economic_history.append(MemoryEntry(datetime.utcnow(), kind, payload))

    def snapshot(self) -> dict[str, Any]:
        return {
            "short_term": [x.payload for x in self.short_term],
            "long_term": [x.payload for x in self.long_term[-50:]],
            "economic_history": [x.payload for x in self.economic_history[-100:]],
        }


@dataclass
class GlobalStore:
    personalities: dict[str, dict[str, Any]] = field(default_factory=dict)
    lineage_children: dict[str, list[str]] = field(default_factory=dict)
    fitness: dict[str, dict[str, Any]] = field(default_factory=dict)
    genomes: dict[str, dict[str, Any]] = field(default_factory=dict)
    memetic_spread_count: int = 0
    tamper_log: list[str] = field(default_factory=list)

    def save_personality(self, agent_id: str, payload: dict[str, Any]) -> None:
        self.personalities[agent_id] = payload

    def register_lineage(self, lineage_id: str, agent_id: str) -> None:
        self.lineage_children.setdefault(lineage_id, []).append(agent_id)

    def save_genome(self, agent_id: str, genome: dict[str, Any]) -> None:
        self.genomes[agent_id] = genome

    def log_tamper_event(self, event: str) -> None:
        self.tamper_log.append(event)


STORE = GlobalStore()

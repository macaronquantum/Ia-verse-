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

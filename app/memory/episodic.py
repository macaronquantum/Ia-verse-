"""Episodic + long-term memory manager with lightweight condensation."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.memory.vector_store import InMemoryVectorStore


@dataclass
class MemoryManager:
    store: InMemoryVectorStore = field(default_factory=InMemoryVectorStore)
    episodes: list[str] = field(default_factory=list)

    def remember(self, event: str) -> None:
        self.episodes.append(event)

    def condense(self) -> str:
        summary = " | ".join(self.episodes[-5:])
        vec = self.store.embed(summary)
        self.store.upsert(str(uuid4()), vec, {"summary": summary})
        return summary

    def query(self, context: str, k: int = 3) -> list[dict]:
        return self.store.query(self.store.embed(context), k)

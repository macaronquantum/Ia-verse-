from __future__ import annotations

from dataclasses import asdict
from typing import List
from uuid import uuid4

from app.models import AgentMemoryRecord, World


class MemoryManager:
    def remember_short_term(self, world: World, agent_id: str, content: str) -> str:
        return self._store(world, agent_id, "short_term", content, score=0.2)

    def remember_long_term(self, world: World, agent_id: str, content: str, score: float = 0.6) -> str:
        # Vector DB integration point (pgvector / Qdrant)
        return self._store(world, agent_id, "long_term_vector", content, score=score)

    def remember_episode(self, world: World, agent_id: str, content: str, score: float = 0.4) -> str:
        return self._store(world, agent_id, "episodic", content, score=score)

    def recall(self, world: World, agent_id: str, memory_type: str | None = None, top_k: int = 10) -> List[dict]:
        memories = [m for m in world.agent_memory.values() if m.agent_id == agent_id]
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]
        memories.sort(key=lambda m: m.score, reverse=True)
        return [asdict(m) for m in memories[:top_k]]

    def _store(self, world: World, agent_id: str, memory_type: str, content: str, score: float) -> str:
        memory_id = str(uuid4())
        world.agent_memory[memory_id] = AgentMemoryRecord(
            id=memory_id,
            agent_id=agent_id,
            memory_type=memory_type,
            content=content,
            score=score,
        )
        return memory_id

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.llm.adapters import HybridLLMAdapter


@dataclass
class AgentJob:
    agent_id: str
    world_id: str
    agent_state: dict[str, Any]
    world_state: dict[str, Any]
    metadata: dict[str, Any]


class InMemoryQueue:
    def __init__(self) -> None:
        self.q: asyncio.Queue[str] = asyncio.Queue()

    async def push(self, item: dict[str, Any]) -> None:
        await self.q.put(json.dumps(item))

    async def pop(self, timeout: float = 1.0) -> dict[str, Any] | None:
        try:
            raw = await asyncio.wait_for(self.q.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        return json.loads(raw)


class AgentWorkerPool:
    def __init__(self, queue_backend: InMemoryQueue | None = None, worker_count: int | None = None, llm_adapter: HybridLLMAdapter | None = None) -> None:
        self.queue = queue_backend or InMemoryQueue()
        self.worker_count = worker_count or settings.WORKER_COUNT
        self.llm = llm_adapter or HybridLLMAdapter()
        self.running = False
        self._workers: list[asyncio.Task[Any]] = []
        self._agent_limits: dict[str, asyncio.Semaphore] = defaultdict(lambda: asyncio.Semaphore(1))
        self._token_budget: dict[str, int] = defaultdict(lambda: 1024)
        self.results: list[dict[str, Any]] = []

    async def enqueue(self, job: AgentJob) -> None:
        await self.queue.push(job.__dict__)

    async def start(self) -> None:
        self.running = True
        for idx in range(self.worker_count):
            self._workers.append(asyncio.create_task(self._worker_loop(idx)))

    async def stop(self) -> None:
        self.running = False
        for t in self._workers:
            t.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def _worker_loop(self, worker_index: int) -> None:
        while self.running:
            job_raw = await self.queue.pop(timeout=0.2)
            if not job_raw:
                continue
            job = AgentJob(**job_raw)
            sem = self._agent_limits[job.agent_id]
            async with sem:
                max_tokens = min(job.metadata.get("max_tokens", 128), self._token_budget[job.agent_id])
                decision = await self.llm.decide_action_async(job.agent_state, job.world_state, {**job.metadata, "max_tokens": max_tokens})
                self._token_budget[job.agent_id] = max(0, self._token_budget[job.agent_id] - max_tokens)
                self.results.append({"worker": worker_index, "agent_id": job.agent_id, "decision": decision})

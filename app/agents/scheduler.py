"""Priority task scheduler abstraction (Celery-compatible semantics)."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field


@dataclass(order=True)
class ScheduledTask:
    priority: int
    name: str = field(compare=False)


class PriorityScheduler:
    PRIORITIES = {"high": 0, "medium": 1, "low": 2}

    def __init__(self) -> None:
        self._queue: list[ScheduledTask] = []

    def enqueue(self, name: str, priority: str = "medium") -> None:
        heapq.heappush(self._queue, ScheduledTask(self.PRIORITIES[priority], name))

    def pop(self) -> str:
        return heapq.heappop(self._queue).name

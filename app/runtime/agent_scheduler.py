from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentScheduler:
    enabled: bool = False

    def schedule_tick(self, agents: list[dict[str, Any]], tick_fn) -> list[Any]:
        if not self.enabled:
            return [tick_fn(agent) for agent in agents]
        import ray

        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)

        @ray.remote
        def _exec(agent: dict[str, Any]) -> Any:
            return tick_fn(agent)

        futures = [_exec.remote(agent) for agent in agents]
        return ray.get(futures)

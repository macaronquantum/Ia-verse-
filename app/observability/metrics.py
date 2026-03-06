from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MetricsCollector:
    counters: dict[str, float] = field(default_factory=dict)
    gauges: dict[str, float] = field(default_factory=dict)

    def inc(self, name: str, value: float = 1.0) -> None:
        self.counters[name] = self.counters.get(name, 0.0) + value

    def set_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value

    def snapshot(self) -> dict[str, dict[str, float]]:
        return {"counters": dict(self.counters), "gauges": dict(self.gauges)}

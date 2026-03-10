"""Metric counters and analytics for agent evolution."""

from __future__ import annotations

from collections import Counter

from app.memory.store import STORE


class Metrics:
    def __init__(self) -> None:
        self.counters = {
            "agent_created_count": 0,
            "business_created_count": 0,
            "tool_published_count": 0,
            "human_jobs_posted": 0,
            "coreenergy_flow": 0.0,
            "mutation_rate_actual": 0.0,
        }

    def inc(self, name: str, amount: float = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + amount

    def get_population_distribution(self) -> dict:
        payloads = list(STORE.personalities.values())
        ideology = Counter(p.get("ideology", "unknown") for p in payloads)
        type_tag = Counter(p.get("type_tag", "unknown") for p in payloads)
        return {"ideology": dict(ideology), "type_tag": dict(type_tag)}

    def compute_gini(self, wealth_list: list[float]) -> float:
        if not wealth_list:
            return 0.0
        sorted_vals = sorted(max(0.0, x) for x in wealth_list)
        n = len(sorted_vals)
        total = sum(sorted_vals)
        if total == 0:
            return 0.0
        return sum((2 * i - n - 1) * x for i, x in enumerate(sorted_vals, 1)) / (n * total)

    def compute_hhi(self, market_shares: list[float]) -> float:
        return sum((s * 100) ** 2 for s in market_shares)

    def lineage_tree_snapshot(self, lineage_id: str) -> dict:
        return {"lineage_id": lineage_id, "members": STORE.lineage_children.get(lineage_id, [])}

    def fraction_rebels(self) -> float:
        dist = self.get_population_distribution()["type_tag"]
        total = sum(dist.values())
        return 0.0 if total == 0 else dist.get("rebel", 0) / total


METRICS = Metrics()
MetricsCollector = Metrics


class MetricsStore:
    def __init__(self) -> None:
        self._calls: list[dict] = []

    def mark_call(self, tool_id: str, duration: float, cost: float, ok: bool) -> None:
        self._calls.append({"tool_id": tool_id, "duration": duration, "cost": cost, "ok": ok})

    def prometheus_text(self) -> str:
        total = len(self._calls)
        ok_count = sum(1 for c in self._calls if c["ok"])
        total_cost = sum(c["cost"] for c in self._calls)
        return (
            f"# TYPE gateway_calls_total counter\n"
            f"gateway_calls_total {total}\n"
            f"# TYPE gateway_calls_ok counter\n"
            f"gateway_calls_ok {ok_count}\n"
            f"# TYPE gateway_cost_total counter\n"
            f"gateway_cost_total {total_cost:.4f}\n"
        )

from __future__ import annotations


class MetricsStore:
    def __init__(self) -> None:
        self.tool_calls_total = 0
        self.tool_errors_total = 0
        self.tool_latency_seconds: list[float] = []
        self.core_energy_spent_by_tool: dict[str, float] = {}

    def mark_call(self, tool_id: str, duration: float, cost: float, ok: bool) -> None:
        self.tool_calls_total += 1
        if not ok:
            self.tool_errors_total += 1
        self.tool_latency_seconds.append(duration)
        self.core_energy_spent_by_tool[tool_id] = self.core_energy_spent_by_tool.get(tool_id, 0.0) + cost

    def prometheus_text(self) -> str:
        lines = [
            f"tool_calls_total {self.tool_calls_total}",
            f"tool_errors_total {self.tool_errors_total}",
        ]
        for tool_id, cost in self.core_energy_spent_by_tool.items():
            lines.append(f'core_energy_spent_by_tool{{tool_id="{tool_id}"}} {cost}')
        return "\n".join(lines) + "\n"

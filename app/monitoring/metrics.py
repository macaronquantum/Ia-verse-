from __future__ import annotations

from prometheus_client import Counter, Gauge

AGENT_ACTIVITY = Counter("ia_agent_activity_total", "Agent actions", ["action"])
ENERGY_GAUGE = Gauge("ia_energy_supply", "Global energy")
LLM_CALLS = Counter("ia_llm_calls_total", "LLM calls", ["source"])
WEB_ACTIONS = Counter("ia_web_actions_total", "Web actions", ["action"])
ECON_METRICS = Gauge("ia_economic_metric", "Economic value", ["name"])


def record_agent_action(action: str) -> None:
    AGENT_ACTIVITY.labels(action=action).inc()

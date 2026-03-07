"""Central configuration for autonomous startup modules."""

from __future__ import annotations

from dataclasses import dataclass, field
import os


@dataclass
class CostConfig:
    create_agent_costs: dict[str, float] = field(
        default_factory=lambda: {
            "citizen": 0.2,
            "dev": 5.0,
            "marketer": 1.0,
            "bank": 200.0,
            "state": 2000.0,
        }
    )
    llm_costs: dict[str, float] = field(default_factory=lambda: {"local": 0.01, "openai": 1.0, "anthropic": 1.0})
    sandbox_per_second_cost: float = 0.02
    marketplace_platform_fee: float = 0.10
    high_risk_spend_threshold: float = 100.0


@dataclass
class RuntimeConfig:
    dev_mode: bool = os.getenv("DEV_MODE", "1") == "1"
    api_gateway_version: str = "v10"


COSTS = CostConfig()
RUNTIME = RuntimeConfig()

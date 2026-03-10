from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return float(raw) if raw is not None else default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw is not None else default


@dataclass
class Settings:
    TICK_SECONDS: int = field(default_factory=lambda: _env_int("TICK_SECONDS", 5))
    CORE_ENERGY_SUPPLY: int = field(default_factory=lambda: _env_int("CORE_ENERGY_SUPPLY", 10_000))
    CORE_EXCHANGE_RATE: int = field(default_factory=lambda: _env_int("CORE_EXCHANGE_RATE", 1_000_000))
    COST_LLMS: dict[str, float] = field(
        default_factory=lambda: {
            "local": _env_float("COST_LLM_LOCAL", 0.01),
            "openai": _env_float("COST_LLM_OPENAI", 1.0),
            "anthropic": _env_float("COST_LLM_ANTHROPIC", 1.0),
        }
    )
    COST_CREATE_CITIZEN: float = field(default_factory=lambda: _env_float("COST_CREATE_CITIZEN", 0.2))
    COST_CREATE_BANK: float = field(default_factory=lambda: _env_float("COST_CREATE_BANK", 200.0))
    COST_CREATE_STATE: float = field(default_factory=lambda: _env_float("COST_CREATE_STATE", 2000.0))
    SETTLEMENT_TIME: str = field(default_factory=lambda: os.getenv("SETTLEMENT_TIME", "00:00"))
    DEV_ALLOW_MINT: bool = field(default_factory=lambda: _env_bool("DEV_ALLOW_MINT", False))
    MINT_PRIVATE_KEY: str = field(default_factory=lambda: os.getenv("MINT_PRIVATE_KEY", ""))
    marketplace_fee_percent: float = field(default_factory=lambda: _env_float("MARKETPLACE_FEE", 0.10))


settings = Settings()


@dataclass
class EvolutionConfig:
    default_mutation_rate: float = field(default_factory=lambda: _env_float("EVO_MUTATION_RATE", 0.1))
    default_mutation_scale: float = field(default_factory=lambda: _env_float("EVO_MUTATION_SCALE", 0.05))
    spawn_energy_cost: float = field(default_factory=lambda: _env_float("EVO_SPAWN_COST", 50.0))
    child_inheritance: str = "average"
    max_rebel_fraction: float = field(default_factory=lambda: _env_float("EVO_MAX_REBEL", 0.3))
    imitate_check_interval_ticks: int = field(default_factory=lambda: _env_int("EVO_IMITATE_INTERVAL", 10))
    imitate_base_prob: float = field(default_factory=lambda: _env_float("EVO_IMITATE_PROB", 0.15))


EVOLUTION = EvolutionConfig()


@dataclass
class CostConfig:
    create_agent_costs: dict[str, float] = field(default_factory=lambda: {
        "worker": 1.0,
        "manager": 5.0,
        "trader": 3.0,
        "researcher": 4.0,
        "banker": 10.0,
    })


COSTS = CostConfig()

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


settings = Settings()

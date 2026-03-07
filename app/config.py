from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    dev_mode: bool = os.getenv("DEV_MODE", "1") == "1"
    judge_transfer_threshold: float = float(os.getenv("JUDGE_TRANSFER_THRESHOLD", "500"))
    judge_hire_threshold: float = float(os.getenv("JUDGE_HIRE_THRESHOLD", "300"))
    llm_budget_per_tick: float = float(os.getenv("LLM_BUDGET_PER_TICK", "25"))


settings = Settings()

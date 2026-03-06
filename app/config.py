from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    dev_mode: bool = os.getenv("DEV_MODE", "true").lower() == "true"
    marketplace_fee_percent: float = float(os.getenv("MARKETPLACE_FEE_PERCENT", "0.10"))
    quota_per_minute_default: int = int(os.getenv("QUOTA_PER_MINUTE_DEFAULT", "30"))
    encryption_key: str = os.getenv("GATEWAY_ENCRYPTION_KEY", "dev-secret-key")


settings = Settings()

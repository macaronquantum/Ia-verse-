from __future__ import annotations

from app.config import settings


class BaseClient:
    def __init__(self) -> None:
        self.dev_mode = bool(getattr(settings, "dev_mode", getattr(settings, "DEV_ALLOW_MINT", False)))

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ia-verse-backend"}


@router.get("/metrics")
def metrics() -> dict:
    return {
        "tick_target_seconds": 5,
        "scheduler_tiers": {"high": 1, "medium": 5, "low": 20},
        "daily_settlement": "enabled",
    }

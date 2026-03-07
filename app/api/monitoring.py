from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/world")
def world_metrics() -> dict:
    return {
        "agent_count": 0,
        "business_count": 0,
        "core_energy_flow": 0,
        "llm_calls_by_model": {"local-ollama": 0, "gpt-external": 0},
        "market_volume": 0,
        "num_active_jobs": 0,
    }


@router.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics() -> str:
    return "\n".join(
        [
            "agent_count 0",
            "business_count 0",
            "core_energy_flow 0",
            "market_volume 0",
            "num_active_jobs 0",
        ]
    )

"""Agent loop helpers including periodic imitation checks."""

from __future__ import annotations

from app.agents.evolution import imitation_event
from app.config import EVOLUTION
from app.memory.store import STORE


def imitation_check(tick: int, top_k: int = 3) -> int:
    if tick % EVOLUTION.imitate_check_interval_ticks != 0:
        return 0
    personalities = STORE.personalities
    if not personalities:
        return 0
    ranked = sorted(
        personalities.keys(),
        key=lambda aid: STORE.fitness.get(aid, {}).get("fitness", 0.0),
        reverse=True,
    )
    models = ranked[:top_k]
    updates = 0
    for observer_id, payload in list(personalities.items()):
        if float(payload.get("curiosity", 0.0)) <= 0.1:
            continue
        for model_id in models:
            if model_id == observer_id:
                continue
            if imitation_event(observer_id, model_id, ["obedience", "greed", "risk"], EVOLUTION.imitate_base_prob):
                updates += 1
    return updates

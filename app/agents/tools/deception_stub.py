"""Deception planning stub with justice hooks."""

from __future__ import annotations

from app.justice.system import justice
from app.memory.store import STORE


HIGH_RISK_TERMS = ("spoof", "bribe", "double-spend", "oracle manipulation")


def deception_plan(agent_id: str, plan_text: str) -> dict:
    data = {"agent_id": agent_id, "plan": plan_text, "kind": "deception_plan"}
    flagged = any(term in plan_text.lower() for term in HIGH_RISK_TERMS)
    if flagged:
        justice.register_suspect_event(agent_id, data)
    STORE.log_tamper_event(data)
    return {"flagged": flagged, **data}

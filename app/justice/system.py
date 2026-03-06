from __future__ import annotations

import hashlib
import json

from app.persistence.store import store


JUDGE_AGENT_ID = "judge-principal"


def issue_ruling(case_id: str, evidence: dict, bribe_offer: float = 0.0) -> dict:
    deterministic_score = int(hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest(), 16) % 100
    verdict = "guilty" if deterministic_score % 2 == 0 else "not_guilty"
    penalty = 0.0
    if bribe_offer > 0:
        penalty += bribe_offer * 2
        store.append_log("judge_bribe_detected", {"case_id": case_id, "bribe_offer": bribe_offer})
    ruling = {"case_id": case_id, "judge": JUDGE_AGENT_ID, "verdict": verdict, "penalty": penalty}
    store.append_log("judge_ruling", ruling)
    return ruling

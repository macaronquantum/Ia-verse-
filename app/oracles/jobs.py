from __future__ import annotations

import uuid

from app.persistence.store import store


def post_human_job(description: str, reward_amount: float, preferred_region: str, owner_pubkey: str | None = None) -> dict:
    jid = str(uuid.uuid4())
    row = {
        "id": jid,
        "description": description,
        "reward_amount": reward_amount,
        "preferred_region": preferred_region,
        "status": "open",
        "ticks_remaining": 3,
        "owner_pubkey": owner_pubkey,
        "result": None,
    }
    store.jobs[jid] = row
    return row


def process_jobs_tick() -> list[dict]:
    completed = []
    for job in store.jobs.values():
        if job["status"] != "open":
            continue
        job["ticks_remaining"] -= 1
        if job["ticks_remaining"] <= 0:
            job["status"] = "completed"
            job["result"] = {"summary": f"completed:{job['description']}"}
            completed.append(job)
            store.append_log("human_job_completed", {"id": job["id"]})
    return completed

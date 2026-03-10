"""Secure, auditable human labor marketplace flow (stubbed connectors)."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from uuid import uuid4

from app.agents.compliance import is_job_safe
from app.api_gateway.costs import BillingLedger
from app.justice.system import JudgeSystem


@dataclass
class HumanJob:
    id: str
    agent_id: str
    platform: str
    description: str
    reward: float
    status: str = "posted"
    worker_hash: str = ""
    hold_id: str = ""


class HumanMarketplaceClient:
    SUPPORTED = {"upwork", "fiverr", "mturk", "microworkers", "scaleai", "appen"}

    def __init__(self, ledger: BillingLedger, judge: JudgeSystem) -> None:
        self.ledger = ledger
        self.judge = judge
        self.jobs: dict[str, HumanJob] = {}

    def post_job(self, agent_id: str, platform: str, description: str, reward: float) -> HumanJob:
        if platform.lower() not in self.SUPPORTED:
            raise ValueError("unsupported platform")
        if not is_job_safe(description):
            raise ValueError("job violates policy")
        decision = self.judge.review_action(agent_id, f"post_job:{description}", reward)
        if not decision.allowed:
            raise ValueError(decision.reason)
        hold_id = self.ledger.preauthorize(agent_id, reward)
        job = HumanJob(id=str(uuid4()), agent_id=agent_id, platform=platform, description=description, reward=reward, hold_id=hold_id)
        self.jobs[job.id] = job
        return job

    def complete_job(self, job_id: str, worker_id: str, accepted: bool) -> None:
        job = self.jobs[job_id]
        job.worker_hash = sha256(worker_id.encode()).hexdigest()
        if accepted:
            self.ledger.capture(job.hold_id, job.reward)
            job.status = "paid"
        else:
            self.ledger.refund(job.hold_id, job.reward)
            job.status = "refunded"

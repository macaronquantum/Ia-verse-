"""Secure, auditable human labor marketplace flow with production connectors."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from uuid import uuid4

from app.agents.compliance import is_job_safe
from app.api_gateway.costs import BillingLedger
from app.justice.system import JudgeSystem
from app.web.browser_agent import BrowserAgent


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
    external_ref: str = ""


class HumanMarketplaceClient:
    SUPPORTED = {"upwork", "fiverr"}

    def __init__(self, ledger: BillingLedger, judge: JudgeSystem, browser_agent: BrowserAgent | None = None) -> None:
        self.ledger = ledger
        self.judge = judge
        self.jobs: dict[str, HumanJob] = {}
        self.browser = browser_agent or BrowserAgent(headless=True)

    def _platform_url(self, platform: str) -> str:
        return {
            "upwork": "https://www.upwork.com/nx/create-job/",
            "fiverr": "https://www.fiverr.com/",
        }[platform]

    def post_job(self, agent_id: str, platform: str, description: str, reward: float) -> HumanJob:
        platform = platform.lower()
        if platform not in self.SUPPORTED:
            raise ValueError("unsupported platform")
        if not is_job_safe(description):
            raise ValueError("job violates policy")
        decision = self.judge.review_action(agent_id, f"post_job:{description}", reward)
        if not decision.allowed:
            raise ValueError(decision.reason)

        hold_id = self.ledger.preauthorize(agent_id, reward)
        form_payload = {"textarea[name='description']": description, "input[name='budget']": str(reward)}
        external_ref = asyncio.run(self.browser.create_account(self._platform_url(platform), form_payload))["status"]
        job = HumanJob(
            id=str(uuid4()),
            agent_id=agent_id,
            platform=platform,
            description=description,
            reward=reward,
            hold_id=hold_id,
            external_ref=external_ref,
        )
        self.jobs[job.id] = job
        return job

    def hire_worker(self, job_id: str, worker_id: str) -> HumanJob:
        job = self.jobs[job_id]
        job.worker_hash = sha256(worker_id.encode()).hexdigest()
        job.status = "hired"
        return job

    def send_payment(self, job_id: str) -> None:
        job = self.jobs[job_id]
        self.ledger.capture(job.hold_id, job.reward)
        job.status = "paid"

    def receive_deliverable(self, job_id: str, accepted: bool, payload: dict[str, Any] | None = None) -> None:
        job = self.jobs[job_id]
        if accepted:
            self.send_payment(job_id)
            job.status = "paid"
        else:
            self.ledger.refund(job.hold_id, job.reward)
            job.status = "refunded"

    def complete_job(self, job_id: str, worker_id: str, accepted: bool) -> None:
        self.hire_worker(job_id, worker_id)
        self.receive_deliverable(job_id, accepted)

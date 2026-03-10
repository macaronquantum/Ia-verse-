from __future__ import annotations

from app.humans.job_market import JobPosting
from app.humans.payment_system import PaymentSystem
from app.justice.system import JudgeSystem


class TaskDispatcher:
    def __init__(self, payments: PaymentSystem, judge: JudgeSystem) -> None:
        self.payments = payments
        self.judge = judge

    def dispatch(self, job: JobPosting) -> str:
        decision = self.judge.review_hire(job.budget, job.risky)
        if not decision.approved:
            raise ValueError(decision.reason)
        self.payments.hold(f"escrow-{len(self.payments.escrows)+1}", job.budget)
        return "dispatched"

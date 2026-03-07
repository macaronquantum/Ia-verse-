"""Controlled external actions routed through gateway abstractions only."""

from __future__ import annotations

from dataclasses import dataclass

from app.api_gateway.costs import BillingLedger
from app.justice.system import JudgeSystem


@dataclass
class ActionResult:
    ok: bool
    message: str


class ExternalActionEngine:
    def __init__(self, ledger: BillingLedger, judge: JudgeSystem) -> None:
        self.ledger = ledger
        self.judge = judge

    def _execute_with_preauth(self, agent: str, action: str, amount: float) -> ActionResult:
        decision = self.judge.review_action(agent, action, amount)
        if not decision.allowed:
            return ActionResult(False, decision.reason)
        self.ledger.preauthorize(agent, amount)
        try:
            self.ledger.capture(agent, amount)
            return ActionResult(True, "executed")
        except Exception:
            self.ledger.refund(agent, amount)
            raise

    def post_job_to_freelance_platform(self, agent: str, job_spec: str, reward: float) -> ActionResult:
        return self._execute_with_preauth(agent, f"post_job:{job_spec}", reward)

    def hire_human(self, agent: str, platform: str, job_id: str, payout: float) -> ActionResult:
        return self._execute_with_preauth(agent, f"hire_human:{platform}:{job_id}", payout)

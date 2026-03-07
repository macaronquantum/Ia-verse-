from __future__ import annotations

from dataclasses import dataclass

from app.config import settings


@dataclass
class JudgeDecision:
    approved: bool
    reason: str


class JudgeSystem:
    def review_transfer(self, amount: float) -> JudgeDecision:
        if amount > settings.judge_transfer_threshold:
            return JudgeDecision(False, "transfer above threshold, manual review required")
        return JudgeDecision(True, "auto-approved")

    def review_hire(self, amount: float, risky: bool) -> JudgeDecision:
        if risky or amount > settings.judge_hire_threshold:
            return JudgeDecision(False, "hire escalated for safety/compliance")
        return JudgeDecision(True, "auto-approved")

    def detect_fraud_pattern(self, account_creations_last_hour: int, concentration_ratio: float) -> bool:
        return account_creations_last_hour > 100 or concentration_ratio > 0.8

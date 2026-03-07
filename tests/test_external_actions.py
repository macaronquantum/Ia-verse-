from app.api_gateway.costs import BillingLedger
from app.external.actions import ExternalActionEngine
from app.justice.system import JudgeSystem


def test_external_action_logs_and_spend_capture() -> None:
    ledger = BillingLedger()
    ledger.credit("agent", 200)
    engine = ExternalActionEngine(ledger, JudgeSystem())
    result = engine.post_job_to_freelance_platform("agent", "write blog", 20)
    assert result.ok
    assert ledger.entries[-1].kind == "capture"

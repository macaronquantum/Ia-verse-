from app.api_gateway.costs import BillingLedger
from app.integrations.human_marketplace_client import HumanMarketplaceClient
from app.justice.system import JudgeSystem


def test_human_job_lifecycle_paid() -> None:
    ledger = BillingLedger()
    ledger.credit("a1", 100)
    client = HumanMarketplaceClient(ledger, JudgeSystem())
    job = client.post_job("a1", "upwork", "create safe logo", 25)
    client.complete_job(job.id, "worker-123", accepted=True)
    assert client.jobs[job.id].status == "paid"

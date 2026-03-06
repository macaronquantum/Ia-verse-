from app.api_gateway.costs import BillingLedger


def test_preauth_capture_and_refund() -> None:
    ledger = BillingLedger()
    ledger.credit("owner", 50)
    ledger.preauthorize("owner", 20)
    ledger.refund("owner", 5)
    ledger.capture("owner", 15)
    assert ledger.balances["owner"] == 35
    assert ledger.reserved["owner"] == 0

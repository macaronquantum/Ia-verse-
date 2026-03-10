from scripts.settlement_daily import run_settlement


def test_settlement_reconciles_stub_entries() -> None:
    res = run_settlement([{"from": "bank", "to": "cb", "amount": 10.0}], dev_mode=True)
    assert res[0]["ok"] is True

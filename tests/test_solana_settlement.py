from scripts.settlement_daily import run_settlement


def test_settlement_reconciles_entries() -> None:
    res = run_settlement([{"from": "bank", "to": "cb", "amount": 10.0}])
    assert res["status"] == "ok"

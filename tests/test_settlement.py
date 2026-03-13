from app.integrations.solana_gateway import Transfer, batch_settlement


def test_settlement_batch_handles_missing_secrets() -> None:
    res = batch_settlement([Transfer(from_pubkey="a", to_pubkey="b", asset="SOL", amount=0.01)])
    assert res["status"] == "ok"
    assert res["applied"][0]["ok"] is False

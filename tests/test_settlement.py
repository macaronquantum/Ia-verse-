from app.integrations.solana_gateway import Transfer, batch_settlement, create_wallet, get_balance


def test_settlement_batch_updates_balances() -> None:
    wa = create_wallet("a")["pubkey"]
    wb = create_wallet("b")["pubkey"]
    from app.persistence.store import store

    store.core_energy_ledger[wa] = 10
    batch_settlement([Transfer(from_pubkey=wa, to_pubkey=wb, asset="CORE", amount=3)])
    assert get_balance(wa, "CORE") == 7
    assert get_balance(wb, "CORE") == 3

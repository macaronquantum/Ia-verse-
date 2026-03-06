from __future__ import annotations

from datetime import datetime, timezone

from app.integrations.solana_gateway import Transfer, batch_settlement
from app.persistence.store import store


def run_daily_settlement(receipt_dir: str = "receipts") -> dict:
    central_wallets = [cb["wallet_pubkey"] for cb in store.central_banks.values()]
    if len(central_wallets) < 2:
        return {"status": "noop", "reason": "not bootstrapped"}

    transfers = [Transfer(from_pubkey=central_wallets[0], to_pubkey=central_wallets[1], asset="CORE", amount=1.0)]
    result = batch_settlement(transfers)
    receipt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "result": result,
        "wallets": central_wallets,
    }
    path = store.persist_receipt(receipt_dir, "daily_settlement.json", receipt)
    receipt["receipt_path"] = path
    return receipt


if __name__ == "__main__":
    print(run_daily_settlement())

from __future__ import annotations

from app.config import settings
from app.persistence.store import store


def mint_core_energy(pubkey: str, amount: float, signer_secret_key: str | None = None) -> dict:
    if not settings.DEV_ALLOW_MINT:
        if not signer_secret_key or signer_secret_key != settings.MINT_PRIVATE_KEY:
            raise PermissionError("mint denied: invalid signer")
    store.core_energy_ledger[pubkey] = store.core_energy_ledger.get(pubkey, 0.0) + amount
    row = {"pubkey": pubkey, "amount": amount}
    store.transactions.append({**row, "kind": "mint"})
    store.append_log("mint", row)
    return {"status": "minted", **row}

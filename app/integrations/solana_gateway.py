from __future__ import annotations

import base64
import os
import uuid
from dataclasses import dataclass

from app.persistence.store import store


@dataclass
class Transfer:
    from_pubkey: str
    to_pubkey: str
    asset: str
    amount: float


def _encrypt(secret: str) -> str:
    return base64.b64encode(secret.encode()).decode()


def create_wallet(label: str) -> dict[str, str]:
    pubkey = f"So1{uuid.uuid4().hex[:20]}"
    secret = os.getenv("DEV_SOLANA_SECRET", uuid.uuid4().hex)
    enc = _encrypt(secret)
    store.wallets[pubkey] = {"label": label, "secret_key_encrypted": enc, "network": "solana"}
    if pubkey not in store.core_energy_ledger:
        store.core_energy_ledger[pubkey] = 0.0
    return {"pubkey": pubkey, "secret_key_encrypted": enc}


def get_balance(pubkey: str, token_mint: str = "CORE") -> float:
    _ = token_mint
    return float(store.core_energy_ledger.get(pubkey, 0.0))


def batch_settlement(transfers: list[Transfer]) -> dict:
    applied = []
    for t in transfers:
        if store.core_energy_ledger.get(t.from_pubkey, 0.0) < t.amount:
            continue
        store.core_energy_ledger[t.from_pubkey] -= t.amount
        store.core_energy_ledger[t.to_pubkey] = store.core_energy_ledger.get(t.to_pubkey, 0.0) + t.amount
        row = {"from": t.from_pubkey, "to": t.to_pubkey, "asset": t.asset, "amount": t.amount}
        applied.append(row)
        store.transactions.append({**row, "kind": "settlement"})
    store.append_log("batch_settlement", {"count": len(applied), "transfers": applied})
    return {"status": "ok", "applied": applied}

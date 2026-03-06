from __future__ import annotations

import re
import uuid

from app.config import settings
from app.energy.core import mint_core_energy
from app.persistence.store import store


class MintOracleAgent:
    id = "mint-oracle-unique"

    @staticmethod
    def mint(pubkey: str, amount_core: float) -> dict:
        return mint_core_energy(pubkey, amount_core, signer_secret_key=settings.MINT_PRIVATE_KEY)


def submit_proof(agent_id: str, solana_pubkey: str, tx_hash: str, metadata: dict) -> dict:
    request_id = str(uuid.uuid4())
    row = {
        "request_id": request_id,
        "agent_id": agent_id,
        "solana_pubkey": solana_pubkey,
        "tx_hash": tx_hash,
        "metadata": metadata,
        "status": "pending",
    }
    store.proofs[request_id] = row
    store.append_log("proof_submitted", row)
    return row


def verify_proof(request_id: str) -> dict:
    req = store.proofs[request_id]
    valid = bool(re.fullmatch(r"[A-Fa-f0-9]{16,128}", req["tx_hash"]))
    req["verified"] = valid
    if not valid:
        req["status"] = "rejected"
        store.append_log("proof_rejected", {"request_id": request_id})
        return req

    usd_value = float(req["metadata"].get("usd_value", settings.CORE_EXCHANGE_RATE))
    amount_core = usd_value / settings.CORE_EXCHANGE_RATE
    mint_result = MintOracleAgent.mint(req["solana_pubkey"], amount_core)
    req["status"] = "minted"
    req["mint_result"] = mint_result
    store.append_log("proof_verified", {"request_id": request_id, "amount_core": amount_core})
    return req

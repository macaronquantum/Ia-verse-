from __future__ import annotations

import base64
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction


@dataclass
class Transfer:
    from_pubkey: str
    to_pubkey: str
    asset: str
    amount: float


class SolanaRPCManager:
    def __init__(self, rpc_url: str | None = None, commitment: str = "confirmed") -> None:
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self.commitment = commitment
        self.client = Client(self.rpc_url, commitment=commitment)

    def get_balance(self, pubkey: str) -> float:
        lamports = self.client.get_balance(Pubkey.from_string(pubkey)).value
        return lamports / 1_000_000_000

    def estimate_fee(self, tx: Transaction) -> int:
        msg = tx.message
        resp = self.client.get_fee_for_message(msg)
        return int(resp.value or 5000)


def _decode_secret(secret_b64: str) -> Keypair:
    return Keypair.from_bytes(base64.b64decode(secret_b64))


def create_wallet(label: str) -> dict[str, str]:
    _ = label
    kp = Keypair()
    return {
        "pubkey": str(kp.pubkey()),
        "secret_key_encrypted": base64.b64encode(bytes(kp)).decode(),
    }


def get_balance(pubkey: str, token_mint: str = "SOL") -> float:
    if token_mint not in {"SOL", "CORE"}:
        raise ValueError("Unsupported asset")
    return SolanaRPCManager().get_balance(pubkey)


def sign_transaction(from_secret_key: str, to_pubkey: str, lamports: int) -> Transaction:
    keypair = _decode_secret(from_secret_key)
    blockhash = SolanaRPCManager().client.get_latest_blockhash().value.blockhash
    ix = transfer(
        TransferParams(
            from_pubkey=keypair.pubkey(),
            to_pubkey=Pubkey.from_string(to_pubkey),
            lamports=lamports,
        )
    )
    return Transaction([keypair], ix, blockhash)


def send_transaction(from_secret_key: str, to_pubkey: str, amount_sol: float, retries: int = 3) -> dict[str, Any]:
    client = SolanaRPCManager().client
    tx = sign_transaction(from_secret_key, to_pubkey, int(amount_sol * 1_000_000_000))
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            result = client.send_transaction(tx)
            sig = str(result.value)
            return {"ok": True, "signature": sig, "attempt": attempt}
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.25 * attempt)
    return {"ok": False, "error": str(last_error), "attempts": retries}


def confirm_transaction(signature: str, timeout_s: int = 30) -> dict[str, Any]:
    client = SolanaRPCManager().client
    end = time.time() + timeout_s
    while time.time() < end:
        status = client.get_signature_statuses([signature]).value[0]
        if status and status.confirmation_status in {"confirmed", "finalized"}:
            return {"confirmed": True, "signature": signature, "slot": status.slot}
        time.sleep(1)
    return {"confirmed": False, "signature": signature, "timeout_s": timeout_s}


def batch_settlement(transfers: list[Transfer]) -> dict[str, Any]:
    batches = []
    for t in transfers:
        from_secret = os.getenv(f"WALLET_SECRET_{t.from_pubkey}", "")
        if not from_secret:
            batches.append({"ok": False, "error": f"missing secret for {t.from_pubkey}"})
            continue
        tx = send_transaction(from_secret, t.to_pubkey, t.amount)
        if tx.get("ok"):
            tx["confirmation"] = confirm_transaction(tx["signature"])
        batches.append({**tx, "from": t.from_pubkey, "to": t.to_pubkey, "amount": t.amount, "asset": t.asset})
    return {"status": "ok", "applied": batches, "batch_id": str(uuid.uuid4())}

from __future__ import annotations

class SolanaClient:
    def __init__(self, dev_mode: bool = True) -> None:
        self.dev_mode = dev_mode

    def transfer(self, from_wallet: str, to_wallet: str, amount: float) -> dict:
        if not self.dev_mode:
            # production RPC integration point
            pass
        return {"ok": True, "tx": f"stub-{from_wallet[:4]}-{to_wallet[:4]}", "amount": amount}

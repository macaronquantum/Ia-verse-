from __future__ import annotations

from app.integrations.solana_client import SolanaClient


def run_settlement(entries: list[dict], dev_mode: bool = True) -> list[dict]:
    client = SolanaClient(dev_mode=dev_mode)
    return [client.transfer(e["from"], e["to"], e["amount"]) for e in entries]


if __name__ == "__main__":
    print(run_settlement([{"from": "bankA", "to": "cb", "amount": 1.0}]))

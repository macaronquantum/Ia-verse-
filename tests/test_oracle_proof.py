from app.config import settings
from app.oracles.api_oracle import submit_proof, verify_proof
from app.persistence.store import store


def test_valid_proof_triggers_mint() -> None:
    settings.DEV_ALLOW_MINT = True
    from app.integrations.solana_gateway import create_wallet

    wallet = create_wallet("oracle-test")["pubkey"]
    req = submit_proof("agent-x", wallet, "abcdef1234567890", {"usd_value": 2_000_000})
    out = verify_proof(req["request_id"])
    assert out["status"] == "minted"
    assert store.core_energy_ledger[wallet] >= 2.0

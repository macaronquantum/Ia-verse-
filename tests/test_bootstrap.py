from scripts.world_bootstrap import ALLOCATIONS, bootstrap_world
from app.persistence.store import store


def test_bootstrap_creates_banks_allocations_and_wallets() -> None:
    bootstrap_world()
    assert len(store.central_banks) == 5
    assert sum(ALLOCATIONS.values()) == 10000
    for cb in store.central_banks.values():
        assert cb["wallet_pubkey"] in store.wallets

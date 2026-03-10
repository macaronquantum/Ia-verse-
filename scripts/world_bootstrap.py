from __future__ import annotations

import time
import uuid

from app.bootstrap.regions import load_regions
from app.config import settings
from app.integrations.solana_gateway import create_wallet
from app.persistence.store import store

ALLOCATIONS = {
    "America": 3200,
    "Asia": 3000,
    "Europe": 2000,
    "LatinAmerica": 1000,
    "Africa": 800,
}
COORDS = {
    "America": [-100, 40],
    "Asia": [100, 35],
    "Europe": [10, 50],
    "LatinAmerica": [-60, -15],
    "Africa": [20, 0],
}


def bootstrap_world() -> dict:
    bootstrap_run_id = str(uuid.uuid4())
    regions = load_regions()
    store.regions.update(regions)

    for name, params in store.regions.items():
        params["coordinates"] = COORDS[name]
        wallet = create_wallet(f"central-bank-{name}")
        allocation = ALLOCATIONS[name]
        store.central_banks[name] = {
            "region": name,
            "wallet_pubkey": wallet["pubkey"],
            "reserve_ratio": 0.1,
            "policy_params": {"inflation_target": 0.02},
            "reputation": 0.8,
            "core_energy": allocation,
        }
        store.core_energy_ledger[wallet["pubkey"]] = float(allocation)
        params["core_energy"] = allocation

    for i in range(50):
        store.agents[f"bank-{i}"] = {"id": f"bank-{i}", "type": "bank", "reputation": 0.6}
    for i in range(300):
        store.agents[f"company-{i}"] = {"id": f"company-{i}", "type": "company", "reputation": 0.5}
    for i in range(2000):
        store.agents[f"citizen-{i}"] = {"id": f"citizen-{i}", "type": "citizen", "reputation": 0.4}
    for i in range(20):
        store.agents[f"judge-sub-{i}"] = {"id": f"judge-sub-{i}", "type": "judge_subordinate", "reputation": 0.9}
    store.agents["judge-principal"] = {"id": "judge-principal", "type": "judge", "reputation": 1.0}
    store.agents["mint-oracle-unique"] = {"id": "mint-oracle-unique", "type": "mint_oracle", "reputation": 1.0}

    assert sum(ALLOCATIONS.values()) == settings.CORE_ENERGY_SUPPLY
    result = {"bootstrap_run_id": bootstrap_run_id, "timestamp": time.time(), "allocations": ALLOCATIONS}
    store.append_log("bootstrap", result)
    return result


if __name__ == "__main__":
    out = bootstrap_world()
    print(out)

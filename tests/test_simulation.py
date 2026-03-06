import asyncio

from app.energy.core import CoreEnergyLedger, MintOracle
from app.simulation import build_default_engine


def test_bootstrap_supply_distribution():
    engine = build_default_engine()
    cb_balances = [k for k in engine.world.energy_ledger.balances if k.startswith("cb_")]
    assert len(cb_balances) == 5
    assert sum(engine.world.energy_ledger.balances[k] for k in cb_balances) == 10000.0


def test_mint_oracle_rules():
    ledger = CoreEnergyLedger()
    oracle = MintOracle(secret_salt="abc123")
    minted = oracle.mint(ledger, "cb_africa", external_usd_value=2_000_000, proof="proofabc")
    assert minted == 2
    assert ledger.balances["cb_africa"] == 2


def test_engine_runs_ticks():
    engine = build_default_engine()
    result = asyncio.run(engine.run(ticks=3, tick_seconds=0))
    assert len(result) == 3
    assert result[-1]["tick"] == 3

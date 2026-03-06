import pytest

from app.energy.core import CoreEnergyLedger
from app.institutions.entities import InstitutionBootstrap
from app.justice.system import JusticeSystem
from app.oracles.api_oracle import MintOracleAgent, OracleRegistry, RealValueProof


def test_initial_central_banks_default_to_five() -> None:
    bootstrap = InstitutionBootstrap()
    banks = bootstrap.create_initial_central_banks()
    assert len(banks) == 5


def test_unique_mint_oracle_registry_and_mint_stub_verification() -> None:
    ledger = CoreEnergyLedger()
    oracle = MintOracleAgent(ledger)
    registry = OracleRegistry()
    registry.register_mint_oracle("mint-1")
    with pytest.raises(ValueError):
        registry.register_mint_oracle("mint-2")

    proof = RealValueProof(
        agent_id="a1",
        external_reference="tx123",
        amount=10,
        signature="invalid",
    )
    with pytest.raises(ValueError):
        oracle.mint_on_verified_value(proof)


def test_unique_principal_judge() -> None:
    js = JusticeSystem(CoreEnergyLedger())
    js.bootstrap_main_judge("judge-1")
    with pytest.raises(ValueError):
        js.bootstrap_main_judge("judge-2")

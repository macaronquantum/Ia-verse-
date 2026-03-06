from app.energy.core import EnergyConfig, EnergyError, EnergyLedger


def test_energy_transfer_and_creation_cost():
    ledger = EnergyLedger(EnergyConfig(agent_creation_cost=4.0))
    ledger.mint("parent", 10)
    ledger.charge_creation("parent")
    assert ledger.balance_of("parent") == 6

    ledger.transfer("parent", "child", 2)
    assert ledger.balance_of("parent") == 4
    assert ledger.balance_of("child") == 2

    try:
        ledger.transfer("child", "parent", 999)
        assert False, "expected error"
    except EnergyError:
        pass

import pytest

from app.economy.markets import Order
from app.organizations.system import OrganizationSystem


def test_company_ipo_and_secondary_trade_updates_valuation() -> None:
    system = OrganizationSystem()
    c = system.create_company("Nova")
    system.ipo(c.id, shares=1000, listing_price=2.0, underwriter_bank_id="bank-1")
    trades = system.trade_equity(c.id, Order(agent_id="investor", side="buy", price=2.0, quantity=100, order_type="market"))
    assert trades
    assert system.organizations[c.id].valuation > 0


def test_state_creation_is_expensive() -> None:
    system = OrganizationSystem()
    with pytest.raises(ValueError):
        system.create_state("cheap-state", treasury=500)
    s = system.create_state("expensive-state", treasury=2500)
    assert s.kind == "state"

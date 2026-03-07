from app.economy.demand_simulator import DemandSimulator, SyntheticDemandConfig


def test_synthetic_demand_generates_revenue() -> None:
    sim = DemandSimulator(SyntheticDemandConfig(users=1000, intensity=1.5))
    rev = sim.generate_revenue(base_price=20, tick=2)
    assert rev > 0

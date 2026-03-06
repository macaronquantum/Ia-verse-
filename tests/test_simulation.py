from app.simulation import WorldEngine


def test_world_lifecycle_and_economy_ticks() -> None:
    engine = WorldEngine()
    world = engine.create_world("test-world")

    a1 = engine.create_agent(world.id, "Alpha")
    engine.create_agent(world.id, "Beta")

    engine.transfer_wallet_to_bank(world.id, a1.id, 20)
    engine.transfer_bank_to_wallet(world.id, a1.id, 10)

    company = engine.create_company(world.id, a1.id, "AlphaCorp")
    loan_id = engine.request_loan(world.id, company.id, 50)

    engine.tick(world.id, steps=5)
    snapshot = engine.snapshot(world.id)

    assert snapshot["tick_count"] == 5
    assert len(snapshot["agents"]) == 2
    assert len(snapshot["companies"]) >= 1
    assert any(l["id"] == loan_id for l in snapshot["bank"]["loans"])


def test_loan_repayment_reduces_or_closes_loan() -> None:
    engine = WorldEngine()
    world = engine.create_world("repay-world")
    agent = engine.create_agent(world.id, "Gamma")
    company = engine.create_company(world.id, agent.id, "GammaWorks")

    loan_id = engine.request_loan(world.id, company.id, 100)
    engine.repay_loan(world.id, company.id, loan_id, 40)

    snapshot = engine.snapshot(world.id)
    loans = {loan["id"]: loan for loan in snapshot["bank"]["loans"]}
    assert loan_id in loans
    assert loans[loan_id]["remaining"] < 100


def test_autonomous_agent_system_generates_tasks_memory_and_metrics() -> None:
    engine = WorldEngine()
    world = engine.create_world("autonomous-world")
    agent = engine.create_agent(world.id, "Delta")
    engine.initialize_autonomous_system(world.id)

    results = engine.scheduler.run_background_cycle(world, cycles_per_agent=2)
    snapshot = engine.snapshot(world.id)

    assert agent.id in results
    assert snapshot["api_gateway_version"] == "v10"
    assert len(snapshot["agent_goals"]) > 0
    assert len(snapshot["agent_tasks"]) > 0
    assert len(snapshot["agent_memory"]) > 0
    assert "agent_revenue" in snapshot["metrics"]
    assert "agent_success_rate" in snapshot["metrics"]

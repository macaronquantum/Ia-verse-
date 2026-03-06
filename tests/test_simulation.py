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

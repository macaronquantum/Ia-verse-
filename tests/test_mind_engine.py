from app.simulation import WorldEngine


def test_agent_mind_cycle_runs_and_records_actions() -> None:
    engine = WorldEngine()
    world = engine.create_world("mind-world")
    alpha = engine.create_agent(world.id, "Alpha")
    engine.create_agent(world.id, "Beta")

    engine.tick(world.id, steps=2)

    mind = engine.minds[world.id][alpha.id]
    assert mind.state.goals
    assert mind.state.plan
    assert mind.state.chosen_actions
    assert "learning_signal" in mind.state.beliefs

    snapshot = engine.snapshot(world.id)
    assert any("cognition cycle actions" in event for event in snapshot["event_log"])


def test_crisis_and_social_system_components_are_active() -> None:
    engine = WorldEngine()
    world = engine.create_world("crisis-world")
    alpha = engine.create_agent(world.id, "Alpha")
    beta = engine.create_agent(world.id, "Beta")

    world.global_resources[next(r for r in world.global_resources if r.value == "energy")] = 1000

    mind = engine.minds[world.id][alpha.id]
    mind.messaging.negotiate(alpha.id, beta.id, "energy deal", 0.2)
    mind.messaging.threaten(alpha.id, beta.id, "territory")

    engine.tick(world.id, steps=1)
    snapshot = engine.snapshot(world.id)

    assert engine.crisis_engines[world.id].active_crises
    assert any("Crisis engine" in event for event in snapshot["event_log"])
    assert len(mind.messaging.history) >= 2

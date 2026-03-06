from app.agents.subagent_manifest import SubAgentSpec, generate_subagent_manifest


def test_subagent_manifest_includes_tests_and_activation_gate() -> None:
    manifest = generate_subagent_manifest(
        parent_agent_id="parent-1",
        specs=[
            SubAgentSpec(
                name="worker-1",
                role="citizen_worker",
                skills=["labor", "data-entry"],
                energy_cost=0.2,
                api_hooks=["/gateway/run_job"],
            )
        ],
    )
    assert len(manifest.subagents) == 1
    entry = manifest.subagents[0]
    assert entry["activation_allowed"] is True
    assert all(t["passed"] for t in entry["simulated_tests"])

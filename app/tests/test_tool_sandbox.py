from app.api_gateway.sandbox.docker_runner import DockerRunner
from app.models.tool_manifest import ToolManifest


def test_docker_runner_echo_and_timeout():
    manifest = ToolManifest.model_validate(
        {
            "name": "echo",
            "description": "echo tool",
            "version": "1.0.0",
            "creator_agent_id": "agent-alpha",
            "entrypoint": "echo",
            "type": "agent_created",
            "tags": [],
            "inputs_schema": {"type": "object"},
            "outputs_schema": {"type": "object"},
            "resources": {"cpu_cores": 0.5, "memory_mb": 128, "disk_mb": 128, "timeout_seconds": 1},
            "cost_core_energy": 0.1,
            "pricing_model": "per_call",
            "visibility": "private",
        }
    )
    runner = DockerRunner()
    ok = runner.run(manifest, {"a": 1})
    assert ok["status"] == "success"
    assert ok["output"]["echo"]["a"] == 1

    timeout = runner.run(manifest, {"simulate_duration": 5})
    assert timeout["status"] == "timeout"

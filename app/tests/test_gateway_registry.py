from app.api_gateway.gateway import PublishToolRequest, RegisterToolRequest, get_tool, list_tools, publish_tool, register_tool


def _manifest():
    return {
        "name": "registry-tool",
        "description": "registry tool test",
        "version": "1.0.0",
        "entrypoint": "echo",
        "type": "agent_created",
        "tags": ["registry"],
        "inputs_schema": {"type": "object"},
        "outputs_schema": {"type": "object"},
        "resources": {"cpu_cores": 0.5, "memory_mb": 128, "disk_mb": 128, "timeout_seconds": 5},
        "cost_core_energy": 0.1,
        "pricing_model": "per_call",
        "visibility": "private",
    }


def test_register_publish_list_get_manifest():
    reg = register_tool(RegisterToolRequest(manifest=_manifest()), x_agent_id="agent-alpha", x_role="citizen")
    tool_id = reg["tool_id"]
    out = publish_tool(tool_id=tool_id, payload=PublishToolRequest(signature="signed"), x_agent_id="agent-alpha", x_role="citizen")
    assert out["status"] == "published"
    listed = list_tools()
    assert any(t["id"] == tool_id for t in listed)
    assert get_tool(tool_id)["name"] == "registry-tool"

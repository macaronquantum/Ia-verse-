from fastapi import HTTPException

from app.api_gateway.gateway import RegisterToolRequest, ToolCallRequest, call_tool, ledger, register_tool


def test_billing_success_and_failure_refund():
    start = ledger.balance_of("agent-beta")
    manifest = {
        "name": "billing-tool",
        "description": "billing tool test",
        "version": "1.0.0",
        "entrypoint": "echo",
        "type": "agent_created",
        "tags": ["billing"],
        "inputs_schema": {"type": "object"},
        "outputs_schema": {"type": "object"},
        "resources": {"cpu_cores": 0.5, "memory_mb": 128, "disk_mb": 128, "timeout_seconds": 1},
        "cost_core_energy": 0.1,
        "pricing_model": "per_call",
        "visibility": "private",
    }
    tool_id = register_tool(RegisterToolRequest(manifest=manifest), x_agent_id="agent-alpha", x_role="citizen")["tool_id"]
    ok = call_tool(tool_id, ToolCallRequest(payload={"x": 1}), x_agent_id="agent-beta", x_role="citizen")
    assert ok["status"] == "success"
    assert ledger.balance_of("agent-beta") < start

    before_fail = ledger.balance_of("agent-beta")
    try:
        call_tool(tool_id, ToolCallRequest(payload={"simulate_duration": 5}), x_agent_id="agent-beta", x_role="citizen")
    except HTTPException as exc:
        assert exc.status_code == 500
    assert ledger.balance_of("agent-beta") == before_fail

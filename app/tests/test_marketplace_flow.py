from app.api_gateway.gateway import (
    PublishToolRequest,
    PurchaseRequest,
    RegisterToolRequest,
    ToolCallRequest,
    call_tool,
    ledger,
    marketplace_purchase,
    publish_tool,
    register_tool,
)


def test_marketplace_publish_purchase_call_and_revenue_split():
    manifest = {
        "name": "market-tool",
        "description": "marketplace tool",
        "version": "1.0.0",
        "entrypoint": "echo",
        "type": "agent_created",
        "tags": ["market"],
        "inputs_schema": {"type": "object"},
        "outputs_schema": {"type": "object"},
        "resources": {"cpu_cores": 0.5, "memory_mb": 128, "disk_mb": 128, "timeout_seconds": 2},
        "cost_core_energy": 0.1,
        "pricing_model": "per_call",
        "visibility": "private",
    }
    tool_id = register_tool(RegisterToolRequest(manifest=manifest), x_agent_id="agent-alpha", x_role="citizen")["tool_id"]
    publish_tool(tool_id=tool_id, payload=PublishToolRequest(signature="ok"), x_agent_id="agent-alpha", x_role="citizen")
    purchase = marketplace_purchase(PurchaseRequest(tool_id=tool_id, model="per_call", amount=1), x_agent_id="agent-beta")
    assert purchase["status"] == "purchased"

    before = ledger.balance_of("agent-alpha")
    res = call_tool(tool_id, ToolCallRequest(payload={}), x_agent_id="agent-beta", x_role="citizen")
    assert res["status"] == "success"
    assert ledger.balance_of("agent-alpha") > before

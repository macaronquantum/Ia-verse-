from app.api_gateway.gateway import call_third_party, create_wallet


def test_gateway_quota_and_charging() -> None:
    agent_id = "agent-test"
    create_wallet(agent_id)
    res = call_third_party(agent_id, "alchemy", {"symbol": "SOL"})
    assert res["provider"] == "alchemy_stub"

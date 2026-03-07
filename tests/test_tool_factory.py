from app.agents.tool_factory import ToolFactory
from app.api_gateway.registry import ToolRegistry


def test_generate_tool_and_publish_to_registry() -> None:
    registry = ToolRegistry()
    factory = ToolFactory(registry)
    result = factory.build_and_publish("a1", "mini-api", 9.0)
    assert result.published
    assert registry.get(result.tool_id).name == "mini-api"

import asyncio

from app.agents.tool_registry import ToolRegistry
from app.integrations.ai_marketplace_client import AIMarketplaceClient


def test_tool_registration_roundtrip(tmp_path):
    reg = ToolRegistry(registry_path=str(tmp_path / "registry.json"))
    client = AIMarketplaceClient(cache_dir=str(tmp_path / "models"))
    out = client.register_tool(reg, "t1", "app.tools.t1:run", ["vision"])
    assert out["tool_id"] == "t1"
    assert reg.discover("vision")


def test_install_model_metadata(tmp_path):
    client = AIMarketplaceClient(cache_dir=str(tmp_path / "models"))
    res = client.install_model("org/repo", str(tmp_path / "models"))
    assert res["installed"] == "true"

import asyncio

from app.llm.adapters import HybridLLMAdapter


class FailingLocal:
    async def infer(self, *args, **kwargs):
        raise TimeoutError("timeout")


class LM:
    def __init__(self):
        self.registry = {"mistral-7b": object()}

    async def infer(self, *args, **kwargs):
        return await FailingLocal().infer()


def test_hybrid_fallback_external():
    adapter = HybridLLMAdapter(local_manager=LM())

    async def run():
        result = await adapter.decide_action_async({"id": "a1"}, {"tick": 1}, {"intent": "x", "local_model": "mistral-7b", "complexity": "low"})
        assert result["source"] == "external_fallback"

    asyncio.run(run())

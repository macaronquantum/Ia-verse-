import asyncio

from app.llm.local_manager import LocalModelManager


def test_local_model_manager_semaphore_enforced():
    mgr = LocalModelManager(models=[{"name": "mistral-7b", "source": "hf", "repo": "x"}], cache_dir="/tmp/models-test")
    mgr.max_concurrency = 1
    mgr._semaphores = {"mistral-7b": asyncio.Semaphore(1)}

    class Slow:
        async def infer(self, *args, **kwargs):
            await asyncio.sleep(0.05)
            return {"text": "ok"}

    mgr._clients["mistral-7b"] = Slow()

    async def run():
        await asyncio.gather(
            mgr.infer("mistral-7b", "a"),
            mgr.infer("mistral-7b", "b"),
        )

    asyncio.run(run())

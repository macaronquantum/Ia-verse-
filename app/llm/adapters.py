from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.llm.local_manager import LocalModelManager
from app.llm.local_runtime import LocalLLMRuntime

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    text: str = ""
    tokens: int = 0


class HybridLLMAdapter:
    """Hybrid local-first adapter with deterministic external routing/fallback."""

    def __init__(self, provider: Any = "anthropic", model: str = "claude-haiku-4-5", local_manager: LocalModelManager | None = None) -> None:
        self.provider = provider if isinstance(provider, str) else "anthropic"
        self.model = model
        self.local_manager = local_manager or LocalModelManager()
        self.token_cost_energy = 0.2
        self.local_runtime = LocalLLMRuntime()

    def _should_use_external(self, agent_state: dict[str, Any], world_state: dict[str, Any], prompt_metadata: dict[str, Any]) -> bool:
        if prompt_metadata.get("complexity") == "high":
            return True
        seed = f"{agent_state.get('id','anon')}|{world_state.get('tick',0)}|{prompt_metadata.get('intent','default')}"
        digest = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        external_ratio = max(0.0, min(1.0, 1.0 - settings.LOCAL_LLM_RATIO))
        return digest < external_ratio

    async def _call_external(self, prompt: str, request_id: str) -> dict[str, Any]:
        return {"text": f"external:{prompt[:120]}", "provider": self.provider, "request_id": request_id}

    async def decide_action_async(
        self,
        agent_state: dict[str, Any],
        world_state: dict[str, Any],
        prompt_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt_metadata = prompt_metadata or {}
        request_id = prompt_metadata.get("request_id") or str(uuid.uuid4())
        prompt = json.dumps({"agent": agent_state, "world": world_state, "meta": prompt_metadata})
        model_name = prompt_metadata.get("local_model", settings.LOCAL_MODELS[0]["name"])
        use_external = self._should_use_external(agent_state, world_state, prompt_metadata)
        try:
            if not use_external:
                try:
                    local = await self.local_runtime.infer(
                        prompt,
                        model=model_name,
                        max_tokens=prompt_metadata.get("max_tokens", 256),
                        temperature=prompt_metadata.get("temperature", 0.2),
                        timeout=settings.LOCAL_MODEL_TIMEOUT,
                    )
                except Exception:
                    local = await self.local_manager.infer(
                        model_name,
                        prompt,
                        max_tokens=prompt_metadata.get("max_tokens", 256),
                        temperature=prompt_metadata.get("temperature", 0.2),
                        timeout=settings.LOCAL_MODEL_TIMEOUT,
                    )
                text = local.get("text", "")
                if text:
                    return {"action": "generate_revenue", "reasoning": text[:160], "request_id": request_id, "source": "local"}
                raise ValueError("invalid local response")
            ext = await self._call_external(prompt, request_id)
            return {"action": "generate_revenue", "reasoning": ext["text"][:160], "request_id": request_id, "source": "external"}
        except Exception as exc:
            logger.warning("local inference failed, fallback to external", extra={"request_id": request_id, "error": str(exc)})
            ext = await self._call_external(prompt, request_id)
            return {"action": "generate_revenue", "reasoning": ext["text"][:160], "request_id": request_id, "source": "external_fallback"}

    def decide_action(self, agent_state: dict[str, Any], world_context: dict[str, Any], prompt_metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        import asyncio

        return asyncio.run(self.decide_action_async(agent_state, world_context, prompt_metadata))

    def generate(self, prompt: str, system: str = "") -> LLMResult:
        return LLMResult(text=f"hybrid:{prompt[:120]}", tokens=max(1, len(prompt) // 8))


class ModelRouter:
    def __init__(self) -> None:
        self._adapter = HybridLLMAdapter()

    def for_tier(self, tier: str) -> HybridLLMAdapter:
        return self._adapter

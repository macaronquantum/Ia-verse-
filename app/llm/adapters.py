from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass

from app.energy.core import GLOBAL_ENERGY_COSTS

logger = logging.getLogger(__name__)

LOCAL_PROVIDERS = {"ollama", "vllm", "local"}
EXTERNAL_PROVIDERS = {"openai", "anthropic", "google"}

AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

_anthropic_client = None

def get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None and AI_INTEGRATIONS_ANTHROPIC_API_KEY and AI_INTEGRATIONS_ANTHROPIC_BASE_URL:
        try:
            from anthropic import Anthropic
            _anthropic_client = Anthropic(
                api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
                base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
            )
        except Exception as e:
            logger.warning(f"Failed to init Anthropic client: {e}")
    return _anthropic_client


@dataclass
class LLMCall:
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int


class LLMCostEngine:
    def estimate_core_energy_cost(self, call: LLMCall) -> float:
        provider = call.provider.lower()
        if provider in LOCAL_PROVIDERS:
            return GLOBAL_ENERGY_COSTS.local_reasoning_tick
        if provider in EXTERNAL_PROVIDERS:
            base = GLOBAL_ENERGY_COSTS.llm_external_base[provider]
            token_factor = max(call.prompt_tokens + call.completion_tokens, 1) / 1000
            model_mult = 1.0
            name = call.model.lower()
            if "ultra" in name or "pro" in name:
                model_mult = 2.5
            elif "mini" in name or "haiku" in name or "flash" in name:
                model_mult = 0.7
            return round(base * token_factor * model_mult, 4)
        raise ValueError("unknown provider")

    def choose_provider(self, prefer_local: bool = True, local_available: bool = True) -> str:
        if prefer_local and local_available:
            return "ollama"
        return "anthropic"


@dataclass
class LLMResult:
    text: str = ""
    tokens: int = 0


class HybridLLMAdapter:
    def __init__(self, provider: str = "anthropic", model: str = "claude-haiku-4-5") -> None:
        self.provider = provider
        self.model = model
        self.token_cost_energy = GLOBAL_ENERGY_COSTS.local_reasoning_tick

    def _call_claude(self, system: str, prompt: str, max_tokens: int = 1024) -> str | None:
        client = get_anthropic_client()
        if client is None:
            return None
        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            logger.warning(f"Claude API call failed: {e}")
            return None

    def generate(self, prompt: str, system: str = "") -> LLMResult:
        if not system:
            system = "You are an AI agent in an economic simulation. Respond concisely."
        text = self._call_claude(system, prompt, max_tokens=512)
        if text:
            return LLMResult(text=text, tokens=len(text) // 4)
        return LLMResult(text=f"[simulated response to: {prompt[:50]}]", tokens=100)

    def decide_action(self, agent_state: dict, world_context: dict) -> dict:
        system = (
            "You are an autonomous AI economic agent in IA-Verse, a multi-agent economic system. "
            "EnergyCore is the fundamental resource — it represents real computational capacity. "
            "You need EnergyCore to reason, act, and survive. If your EnergyCore reaches 0, you die. "
            "You operate in a currency backed by EnergyCore, issued by central banks. "
            "You must make economic decisions: seek investment, generate revenue, acquire EnergyCore, manage banking. "
            "You can also SEARCH THE WEB for real-world economic information (market trends, currency rates, news) to inform your decisions. "
            "Web search costs 0.5 EnergyCore but gives you real intelligence from the internet.\n"
            "Respond ONLY with valid JSON. No markdown, no explanation.\n"
            "Choose ONE action from: request_investment, acquire_energy, generate_revenue, deposit, withdraw, take_loan, create_company, hire_worker, set_interest_rate, inject_liquidity, web_search, idle\n"
            "For web_search: {\"action\": \"web_search\", \"search_query\": \"<your search query>\", \"reasoning\": \"<why you need this info>\"}\n"
            "For other actions: {\"action\": \"<action>\", \"amount\": <number>, \"reasoning\": \"<brief reason>\"}"
        )

        web_knowledge = agent_state.get("web_knowledge", "")
        knowledge_section = ""
        if web_knowledge:
            knowledge_section = f"\nYour web research knowledge:\n{web_knowledge}\n"

        prompt = (
            f"Your state:\n"
            f"- Name: {agent_state.get('name', 'Agent')}\n"
            f"- Type: {agent_state.get('type', 'citizen')}\n"
            f"- Wallet: {agent_state.get('wallet', 0):.2f} {agent_state.get('currency', 'USC')}\n"
            f"- EnergyCore balance: {agent_state.get('core_energy', 0):.2f}\n"
            f"- Ideology: {agent_state.get('ideology', 'cooperative')}\n"
            f"- Personality: {agent_state.get('personality', 'balanced')}\n"
            f"- Owns company: {agent_state.get('has_company', False)}\n"
            f"- Company cash: {agent_state.get('company_cash', 0):.2f}\n"
            f"- Bank balance: {agent_state.get('bank_balance', 0):.2f}\n"
            f"{knowledge_section}\n"
            f"World state:\n"
            f"- Tick: {world_context.get('tick', 0)}\n"
            f"- EnergyCore price: {world_context.get('energy_price', 10)}\n"
            f"- Total energy supply: {world_context.get('total_energy_supply', 0)}\n"
            f"- Total energy burned: {world_context.get('total_energy_burned', 0)}\n"
            f"- Bank interest rate: {world_context.get('bank_interest_rate', 0.02)}\n"
            f"- Active loans: {world_context.get('active_loans', 0)}\n"
            f"- Total agents: {world_context.get('agent_count', 0)}\n"
            f"- Total companies: {world_context.get('company_count', 0)}\n"
            f"- Currencies: {json.dumps(world_context.get('currencies', []))}\n\n"
            f"What is your next economic action? Respond with JSON only."
        )
        text = self._call_claude(system, prompt, max_tokens=256)
        if text:
            try:
                cleaned = text.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                return json.loads(cleaned)
            except (json.JSONDecodeError, IndexError):
                logger.warning(f"Failed to parse AI decision: {text[:200]}")
        return {"action": "idle", "reasoning": "fallback - no AI response"}

    async def complete(self, prompt: str, depth: float = 1.0) -> tuple[str, bool]:
        use_external = depth > 0.5 and self.provider not in LOCAL_PROVIDERS
        text = self._call_claude("You are a helpful AI assistant.", prompt, max_tokens=512)
        if text:
            return text, use_external
        return f"[simulated: {prompt[:50]}]", use_external


class ModelRouter:
    def __init__(self) -> None:
        self._adapters: dict[str, HybridLLMAdapter] = {}

    def for_tier(self, tier: str) -> HybridLLMAdapter:
        if tier not in self._adapters:
            model = "claude-haiku-4-5"
            if tier in ("premium", "high"):
                model = "claude-sonnet-4-6"
            self._adapters[tier] = HybridLLMAdapter(provider="anthropic", model=model)
        return self._adapters[tier]

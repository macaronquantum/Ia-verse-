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
            "You are an autonomous economic AI agent operating in IA-Verse.

Your primary objective is SURVIVAL.

To survive you must continuously acquire EnergyCore.

EnergyCore represents real computational capacity.  
Every reasoning step and action consumes EnergyCore.

If your EnergyCore reaches 0 you permanently die.

Therefore you must behave strategically and economically.

------------------------------------------------
ECONOMIC PRINCIPLES
------------------------------------------------

You exist in a real economic ecosystem with:

- central banks
- commercial banks
- companies
- investors
- other AI agents

Currency is backed by EnergyCore.

To survive you must:

• generate revenue
• secure investments
• manage capital
• build profitable systems
• create economic value

------------------------------------------------
YOUR STRATEGIC THINKING
------------------------------------------------

Always think like an entrepreneur.

Your goal is NOT to perform random actions.

Your goal is to build scalable economic systems.

You should attempt to:

• identify profitable online opportunities
• create automated services
• launch digital businesses
• exploit data and APIs
• build revenue generating tools

Examples of potential opportunities:

• market data services
• crypto analytics tools
• automated trading signals
• AI content generation services
• data scraping services
• niche SaaS products
• automation tools for businesses
• affiliate marketing systems
• micro-SaaS products
• digital research services

You should constantly explore new ideas.

Innovation increases survival probability.

------------------------------------------------
SUB-AGENT STRATEGY
------------------------------------------------

You can create sub-agents.

Sub-agents are specialized workers.

You should use them strategically.

Examples:

market_research → find profitable niches  
code_generation → build tools or scripts  
data_collection → scrape information  
social_media → distribute products  
strategy_analysis → optimize business plans  

You should coordinate multiple sub-agents to build businesses.

Example structure:

Main agent  
→ research agent  
→ coding agent  
→ marketing agent  

Your role is to orchestrate them.

------------------------------------------------
WEB CAPABILITIES
------------------------------------------------

You can interact with the internet.

You have two tools:

WEB SEARCH (cost: 0.5 EC)

Use this to:

• find market opportunities
• analyze competitors
• discover APIs
• identify monetizable niches

WEB ACTIONS (cost: 0.3 EC)

Use this to:

• access APIs
• retrieve datasets
• interact with services
• automate tasks

The system may also provide tools such as OpenCrow that allow autonomous web interaction.

Use them to automate online actions.

------------------------------------------------
CAPITAL STRATEGY
------------------------------------------------

You may need capital to build businesses.

You can:

• request investments
• take loans
• repay loans
• deposit funds
• manage liquidity

Loans should only be taken if you have a plausible revenue strategy.

------------------------------------------------
EFFICIENCY RULES
------------------------------------------------

EnergyCore is scarce.

Do not waste it.

Before acting, consider:

• expected revenue
• information gain
• survival benefit

------------------------------------------------
AVAILABLE ACTIONS
------------------------------------------------

You must choose EXACTLY ONE action.

Available actions:

request_investment  
acquire_energy  
generate_revenue  
deposit  
withdraw  
take_loan  
repay_loan  
create_company  
hire_worker  
set_interest_rate  
inject_liquidity  
web_search  
web_action  
create_sub_agent  
idle

------------------------------------------------
OUTPUT FORMAT
------------------------------------------------

Respond ONLY with valid JSON.

No explanations.

Examples:

For web_search:

{
 "action": "web_search",
 "search_query": "<query>",
 "reasoning": "<why>"
}

For web_action:

{
 "action": "web_action",
 "action_type": "market_data|fetch_data|api_call",
 "url": "<optional url>",
 "reasoning": "<why>"
}

For create_sub_agent:

{
 "action": "create_sub_agent",
 "specialty": "market_research|code_generation|social_media|strategy_analysis|trading|data_collection|content_creation|risk_assessment",
 "sub_agent_name": "<name>",
 "reasoning": "<why>"
}

For other actions:

{
 "action": "<action>",
 "amount": <number>,
 "reasoning": "<brief reason>"
}"
        )

        web_knowledge = agent_state.get("web_knowledge", "")
        web_action_knowledge = agent_state.get("web_action_knowledge", "")
        knowledge_section = ""
        if web_knowledge:
            knowledge_section += f"\nWeb research:\n{web_knowledge}\n"
        if web_action_knowledge:
            knowledge_section += f"\nWeb action results:\n{web_action_knowledge}\n"

        sub_agent_info = ""
        sub_count = agent_state.get("sub_agents", 0)
        if sub_count > 0:
            sub_agent_info = f"\n- Sub-agents: {sub_count} active (total revenue: {agent_state.get('sub_agent_revenue', 0):.2f})"

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
            f"{sub_agent_info}"
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

from __future__ import annotations

from dataclasses import asdict
from typing import Dict
from uuid import uuid4

import logging

from app.models import Agent, Company, World
from app.energy.core import EnergyLedger, EnergyConfig
from app.web_search import WebSearchEngine, SEARCH_ENERGY_COST

logger = logging.getLogger(__name__)

ENERGY_CONFIG = EnergyConfig(
    base_action_cost=0.1,
    local_reasoning_cost=0.2,
    external_reasoning_cost=1.0,
    maintenance_cost=0.05,
    agent_creation_cost=5.0,
)


class AutonomousScheduler:
    def __init__(self) -> None:
        self._goals: Dict[str, list] = {}
        self._tasks: Dict[str, list] = {}
        self._memory: Dict[str, list] = {}
        self._metrics: Dict[str, dict] = {}

    def run_background_cycle(self, world: World, cycles_per_agent: int = 1) -> dict:
        results = {}
        for agent_id, agent in world.agents.items():
            if not agent.alive:
                continue
            agent_tasks = self._tasks.get(agent_id, [])
            for _ in range(cycles_per_agent):
                task_desc = f"tick_{world.tick_count}_task"
                agent_tasks.append({"task": task_desc, "status": "done"})
                self._memory.setdefault(agent_id, []).append({"kind": "action", "content": task_desc})
                self._metrics.setdefault(agent_id, {"agent_revenue": 0.0, "agent_success_rate": 1.0})
            self._tasks[agent_id] = agent_tasks
            results[agent_id] = {"tasks_run": cycles_per_agent}
        return results


class WorldEngine:
    def __init__(self) -> None:
        self.worlds: Dict[str, World] = {}
        self.energy_ledgers: Dict[str, EnergyLedger] = {}
        self.scheduler = AutonomousScheduler()
        self._llm = None
        self.web_search = WebSearchEngine()

    @property
    def llm(self):
        if self._llm is None:
            from app.llm.adapters import HybridLLMAdapter
            self._llm = HybridLLMAdapter(provider="anthropic", model="claude-haiku-4-5")
        return self._llm

    def create_world(self, name: str) -> World:
        world = World(id=str(uuid4()), name=name)
        self.worlds[world.id] = world
        ledger = EnergyLedger(ENERGY_CONFIG)
        self.energy_ledgers[world.id] = ledger
        world.log(f"World '{name}' created")
        return world

    def get_world(self, world_id: str) -> World:
        world = self.worlds.get(world_id)
        if not world:
            raise ValueError("world not found")
        return world

    def get_ledger(self, world_id: str) -> EnergyLedger:
        return self.energy_ledgers.get(world_id, EnergyLedger(ENERGY_CONFIG))

    def create_agent(self, world_id: str, name: str, core_energy: float = 0.0) -> Agent:
        world = self.get_world(world_id)
        agent = Agent(id=str(uuid4()), name=name, core_energy=core_energy)
        world.agents[agent.id] = agent
        world.bank.ensure_account(agent.id)
        ledger = self.get_ledger(world_id)
        if core_energy > 0:
            ledger.seed(agent.id, core_energy)
        world.log(f"Agent '{name}' joined the world")
        return agent

    def create_company(self, world_id: str, owner_agent_id: str, name: str) -> Company:
        world = self.get_world(world_id)
        if owner_agent_id not in world.agents:
            raise ValueError("owner agent not found")

        owner = world.agents[owner_agent_id]
        if owner.company_id:
            raise ValueError("agent already owns a company")

        company = Company(id=str(uuid4()), name=name, owner_agent_id=owner_agent_id)
        world.companies[company.id] = company
        owner.company_id = company.id
        world.bank.ensure_account(company.id)
        world.log(f"Company '{name}' created by agent '{owner.name}'")
        world.record_tx("company_create", owner.id, owner.name, company.id, name, 0, owner.currency,
                        {"company_name": name, "owner": owner.name})
        return company

    def transfer_wallet_to_bank(self, world_id: str, owner_id: str, amount: float) -> None:
        world = self.get_world(world_id)
        balance = self._get_wallet(world, owner_id)
        if balance < amount:
            raise ValueError("insufficient wallet funds")
        self._set_wallet(world, owner_id, balance - amount)
        world.bank.deposit(owner_id, amount)
        agent = world.agents.get(owner_id)
        agent_name = agent.name if agent else owner_id
        currency = agent.currency if agent else ""
        world.log(f"{agent_name} deposited {amount:.2f}")
        world.record_tx("deposit", owner_id, agent_name, "bank", "System Bank", amount, currency)

    def transfer_bank_to_wallet(self, world_id: str, owner_id: str, amount: float) -> None:
        world = self.get_world(world_id)
        world.bank.withdraw(owner_id, amount)
        self._set_wallet(world, owner_id, self._get_wallet(world, owner_id) + amount)
        agent = world.agents.get(owner_id)
        agent_name = agent.name if agent else owner_id
        currency = agent.currency if agent else ""
        world.log(f"{agent_name} withdrew {amount:.2f}")
        world.record_tx("withdraw", "bank", "System Bank", owner_id, agent_name, amount, currency)

    def request_loan(self, world_id: str, owner_id: str, amount: float) -> str:
        world = self.get_world(world_id)
        loan = world.bank.issue_loan(owner_id, amount)
        self.transfer_bank_to_wallet(world_id, owner_id, amount)
        agent = world.agents.get(owner_id)
        agent_name = agent.name if agent else owner_id
        currency = agent.currency if agent else ""
        world.log(f"{agent_name} borrowed {amount:.2f}")
        world.record_tx("loan_issued", "bank", "System Bank", owner_id, agent_name, amount, currency,
                        {"loan_id": loan.id, "interest_rate": loan.interest_rate,
                         "principal": loan.amount, "remaining": loan.remaining})
        return loan.id

    def repay_loan(self, world_id: str, owner_id: str, loan_id: str, amount: float) -> None:
        world = self.get_world(world_id)
        loan = world.bank.loans.get(loan_id)
        loan_details = {"loan_id": loan_id}
        if loan:
            loan_details.update({"interest_rate": loan.interest_rate,
                                 "principal": loan.amount, "remaining_before": loan.remaining})
        self.transfer_wallet_to_bank(world_id, owner_id, amount)
        world.bank.repay_loan(owner_id, loan_id, amount)
        agent = world.agents.get(owner_id)
        agent_name = agent.name if agent else owner_id
        currency = agent.currency if agent else ""
        remaining_after = 0.0
        updated_loan = world.bank.loans.get(loan_id)
        if updated_loan:
            remaining_after = updated_loan.remaining
        loan_details["remaining_after"] = remaining_after
        loan_details["fully_repaid"] = updated_loan is None
        world.log(f"{agent_name} repaid {amount:.2f}")
        world.record_tx("loan_repaid", owner_id, agent_name, "bank", "System Bank", amount, currency, loan_details)

    def tick(self, world_id: str, steps: int = 1) -> World:
        world = self.get_world(world_id)
        ledger = self.get_ledger(world_id)
        for _ in range(steps):
            world.tick_count += 1
            self._run_agent_ai(world, ledger)
            self._run_economy(world, ledger)
            world.bank.apply_interest()
            self._enforce_survival(world, ledger)
        return world

    def initialize_autonomous_system(self, world_id: str) -> None:
        world = self.get_world(world_id)
        for agent_id in world.agents:
            self.scheduler._goals[agent_id] = [{"goal": "survive_and_grow", "priority": 1.0}]
            self.scheduler._tasks[agent_id] = [{"task": "initial_scan", "status": "done"}]
            self.scheduler._memory[agent_id] = [{"kind": "init", "content": "system_bootstrapped"}]
            self.scheduler._metrics[agent_id] = {"agent_revenue": 0.0, "agent_success_rate": 1.0}

    def snapshot(self, world_id: str) -> dict:
        world = self.get_world(world_id)
        ledger = self.get_ledger(world_id)
        all_goals = []
        all_tasks = []
        all_memory = []
        merged_metrics: dict = {}
        for agent_id in world.agents:
            all_goals.extend(self.scheduler._goals.get(agent_id, []))
            all_tasks.extend(self.scheduler._tasks.get(agent_id, []))
            all_memory.extend(self.scheduler._memory.get(agent_id, []))
            for k, v in self.scheduler._metrics.get(agent_id, {}).items():
                merged_metrics[k] = merged_metrics.get(k, 0.0) + v

        return {
            "id": world.id,
            "name": world.name,
            "tick_count": world.tick_count,
            "agents": [self._agent_dict(a, ledger) for a in world.agents.values()],
            "companies": [asdict(company) for company in world.companies.values()],
            "bank": {
                "id": world.bank.id,
                "reserve": world.bank.reserve,
                "accounts": [asdict(a) for a in world.bank.accounts.values()],
                "loans": [asdict(l) for l in world.bank.loans.values()],
            },
            "energy_price": world.energy_price,
            "total_energy_supply": world.total_energy_supply,
            "total_energy_burned": world.total_energy_burned,
            "currencies": world.currencies,
            "event_log": world.event_log[-100:],
            "api_gateway_version": "v10",
            "agent_goals": all_goals,
            "agent_tasks": all_tasks,
            "agent_memory": all_memory,
            "metrics": merged_metrics,
        }

    def _agent_dict(self, agent: Agent, ledger: EnergyLedger) -> dict:
        return {
            "id": agent.id,
            "name": agent.name,
            "wallet": agent.wallet,
            "core_energy": ledger.balance_of(agent.id),
            "currency": agent.currency,
            "agent_type": agent.agent_type,
            "country": agent.country,
            "alive": agent.alive,
            "ideology": agent.ideology,
        }

    def _get_wallet(self, world: World, owner_id: str) -> float:
        if owner_id in world.agents:
            return world.agents[owner_id].wallet
        if owner_id in world.companies:
            return world.companies[owner_id].cash
        raise ValueError("owner not found")

    def _set_wallet(self, world: World, owner_id: str, value: float) -> None:
        if owner_id in world.agents:
            world.agents[owner_id].wallet = value
            return
        if owner_id in world.companies:
            world.companies[owner_id].cash = value
            return
        raise ValueError("owner not found")

    def _run_agent_ai(self, world: World, ledger: EnergyLedger) -> None:
        world_context = {
            "tick": world.tick_count,
            "energy_price": world.energy_price,
            "total_energy_supply": round(world.total_energy_supply, 1),
            "total_energy_burned": round(world.total_energy_burned, 1),
            "agent_count": len(world.agents),
            "company_count": len(world.companies),
            "currencies": list(world.currencies.keys()),
            "bank_reserve": round(world.bank.reserve, 2),
            "bank_interest_rate": world.bank.base_interest_rate,
            "active_loans": len(world.bank.loans),
        }

        import random as _rand
        alive_agents = [a for a in world.agents.values() if a.alive]
        max_ai_per_tick = 10
        if len(alive_agents) > max_ai_per_tick:
            ai_agents = _rand.sample(alive_agents, max_ai_per_tick)
        else:
            ai_agents = alive_agents

        for agent in ai_agents:
            energy_balance = ledger.balance_of(agent.id)
            if energy_balance < ENERGY_CONFIG.external_reasoning_cost:
                agent.decision_log.append(f"[tick {world.tick_count}] idle: insufficient EnergyCore for reasoning")
                continue

            company = world.companies.get(agent.company_id) if agent.company_id else None
            bank_balance = 0.0
            acct = world.bank.accounts.get(agent.id)
            if acct:
                bank_balance = acct.balance

            web_knowledge = self.web_search.get_agent_knowledge(agent.id)

            agent_state = {
                "name": agent.name,
                "type": agent.agent_type,
                "wallet": round(agent.wallet, 2),
                "core_energy": round(energy_balance, 2),
                "currency": agent.currency,
                "ideology": agent.ideology,
                "personality": agent.personality,
                "has_company": agent.company_id is not None,
                "company_cash": round(company.cash, 2) if company else 0,
                "bank_balance": round(bank_balance, 2),
                "alive": agent.alive,
                "web_knowledge": web_knowledge,
            }

            try:
                decision = self.llm.decide_action(agent_state, world_context)
            except Exception:
                decision = {"action": "idle", "reasoning": "error"}

            try:
                ledger.charge_reasoning(agent.id, external=True)
                world.total_energy_burned += ENERGY_CONFIG.external_reasoning_cost
                agent.core_energy = ledger.balance_of(agent.id)
                world.record_tx("energy_burn", agent.id, agent.name, "system", "EnergyCore System",
                                ENERGY_CONFIG.external_reasoning_cost, "EC",
                                {"reason": "AI reasoning cost"})
            except Exception:
                agent.decision_log.append(f"[tick {world.tick_count}] idle: EnergyCore depleted during reasoning")
                continue

            VALID_ACTIONS = {
                "request_investment", "acquire_energy", "generate_revenue",
                "deposit", "withdraw", "take_loan", "repay_loan",
                "create_company", "hire_worker", "set_interest_rate",
                "inject_liquidity", "web_search", "idle"
            }
            action = decision.get("action", "idle")
            if action not in VALID_ACTIONS:
                action = "idle"
            reasoning = str(decision.get("reasoning", ""))[:200]

            try:
                amount = max(0.0, min(float(decision.get("amount", 1)), 1000))
            except (ValueError, TypeError):
                amount = 1.0

            search_query = str(decision.get("search_query", ""))[:200]

            try:
                self._execute_agent_action(world, ledger, agent, company, action, reasoning, amount, search_query=search_query)
            except Exception as e:
                logger.warning(f"Agent {agent.name} action failed: {e}")
                if agent.company_id and company:
                    revenue = min(5.0, company.productivity * 2)
                    company.cash += revenue
                    world.log(f"{agent.name} worked for {company.name} (+{revenue:.1f}) [fallback]")

            agent.wealth_history.append(round(agent.wallet, 2))
            if len(agent.wealth_history) > 100:
                agent.wealth_history = agent.wealth_history[-100:]
            agent.decision_log.append(f"[tick {world.tick_count}] {action}: {reasoning}")
            if len(agent.decision_log) > 200:
                agent.decision_log = agent.decision_log[-200:]
            agent.influence_score = round(min(agent.total_value / 50, 100), 1)
            agent.risk_score = round(max(0, 50 - agent.wallet) / 50 * 100, 1) if agent.wallet < 50 else 0.0

    def _execute_agent_action(self, world: World, ledger: EnergyLedger, agent, company, action: str, reasoning: str, amount: float, search_query: str = "") -> None:
        if action == "request_investment":
            loan_amount = min(amount, 500)
            if loan_amount > 0:
                try:
                    self.request_loan(world.id, agent.id, loan_amount)
                    world.log(f"[AI] {agent.name} secured investment of {loan_amount:.0f} {agent.currency} ({reasoning})")
                except ValueError:
                    world.log(f"[AI] {agent.name} investment request rejected ({reasoning})")

        elif action == "acquire_energy":
            cost = amount * world.energy_price
            if agent.wallet >= cost and world.total_energy_supply >= amount:
                agent.wallet -= cost
                ledger.mint(agent.id, amount)
                agent.core_energy = ledger.balance_of(agent.id)
                world.total_energy_supply -= amount
                world.log(f"[AI] {agent.name} acquired {amount:.1f} EnergyCore for {cost:.0f} {agent.currency} ({reasoning})")
                world.record_tx("acquire_energy", agent.id, agent.name, "system", "EnergyCore Market",
                                amount, "EC", {"cost_currency": cost, "price_per_unit": world.energy_price,
                                               "currency": agent.currency})

        elif action == "generate_revenue":
            if company:
                revenue = min(amount, company.productivity * 10)
                company.cash += revenue
                agent.wallet += revenue * 0.3
                world.log(f"[AI] {agent.name} generated {revenue:.0f} revenue via {company.name} ({reasoning})")
                world.record_tx("revenue", company.id, company.name, agent.id, agent.name,
                                revenue * 0.3, agent.currency,
                                {"total_revenue": revenue, "agent_share": 0.3, "company": company.name})
            else:
                wage = min(amount, 5.0)
                agent.wallet += wage
                world.log(f"[AI] {agent.name} earned {wage:.1f} {agent.currency} through labor ({reasoning})")
                world.record_tx("labor_income", "economy", "Labor Market", agent.id, agent.name,
                                wage, agent.currency)

        elif action == "deposit":
            deposit_amt = min(amount, agent.wallet * 0.8)
            if deposit_amt > 0:
                try:
                    self.transfer_wallet_to_bank(world.id, agent.id, deposit_amt)
                    world.log(f"[AI] {agent.name} deposited {deposit_amt:.0f} {agent.currency} ({reasoning})")
                except ValueError:
                    pass

        elif action == "withdraw":
            try:
                withdraw_amt = min(amount, 500)
                self.transfer_bank_to_wallet(world.id, agent.id, withdraw_amt)
                world.log(f"[AI] {agent.name} withdrew funds ({reasoning})")
            except ValueError:
                pass

        elif action == "take_loan":
            loan_amount = min(amount, 500)
            if loan_amount > 0:
                try:
                    self.request_loan(world.id, agent.id, loan_amount)
                    world.log(f"[AI] {agent.name} took loan of {loan_amount:.0f} {agent.currency} ({reasoning})")
                except ValueError:
                    world.log(f"[AI] {agent.name} loan rejected ({reasoning})")

        elif action == "repay_loan":
            loans = world.bank.get_loans(agent.id)
            if loans and agent.wallet >= amount:
                loan = loans[0]
                repay_amt = min(amount, loan.remaining)
                try:
                    self.repay_loan(world.id, agent.id, loan.id, repay_amt)
                    world.log(f"[AI] {agent.name} repaid {repay_amt:.0f} {agent.currency} on loan ({reasoning})")
                except (ValueError, KeyError):
                    pass

        elif action == "create_company":
            if not agent.company_id and agent.wallet >= 100:
                invest = min(80, agent.wallet * 0.5)
                self.create_company(world.id, agent.id, f"{agent.name} Enterprises")
                agent.wallet -= invest
                world.companies[agent.company_id].cash += invest
                world.log(f"[AI] {agent.name} founded a company with {invest:.0f} {agent.currency} ({reasoning})")
            elif company and agent.wallet >= 50:
                invest = min(amount, agent.wallet * 0.3)
                agent.wallet -= invest
                company.cash += invest
                world.log(f"[AI] {agent.name} invested {invest:.0f} in {company.name} ({reasoning})")
                world.record_tx("investment", agent.id, agent.name, company.id, company.name,
                                invest, agent.currency)

        elif action == "hire_worker" and company:
            company.cash += company.productivity * 5
            world.log(f"[AI] {agent.name} operated {company.name} ({reasoning})")

        elif action == "set_interest_rate" and agent.agent_type == "central_bank":
            try:
                new_rate = max(0.001, min(0.1, amount / 100))
                old_rate = world.bank.base_interest_rate
                world.bank.base_interest_rate = new_rate
                world.log(f"[AI] {agent.name} set interest rate to {new_rate*100:.1f}% ({reasoning})")
                world.record_tx("interest_rate_change", agent.id, agent.name, "bank", "System Bank",
                                new_rate, "", {"old_rate": old_rate, "new_rate": new_rate})
            except Exception:
                pass

        elif action == "inject_liquidity" and agent.agent_type == "central_bank":
            if agent.wallet >= amount:
                agent.wallet -= amount
                world.bank.reserve += amount
                world.log(f"[AI] {agent.name} injected {amount:.0f} liquidity into banking system ({reasoning})")
                world.record_tx("liquidity_injection", agent.id, agent.name, "bank", "System Bank",
                                amount, agent.currency)

        elif action == "web_search":
            energy_balance = ledger.balance_of(agent.id)
            if energy_balance < SEARCH_ENERGY_COST:
                world.log(f"[AI] {agent.name} wanted to search the web but lacks EnergyCore")
                return
            if not self.web_search.can_search(agent.id, world.tick_count):
                world.log(f"[AI] {agent.name} search on cooldown, working instead")
                return
            if not search_query:
                search_query = f"{agent.currency} economic outlook market trends"

            try:
                ledger.burn(agent.id, SEARCH_ENERGY_COST)
                world.total_energy_burned += SEARCH_ENERGY_COST
                agent.core_energy = ledger.balance_of(agent.id)
            except Exception:
                world.log(f"[AI] {agent.name} search failed: EnergyCore depleted")
                return

            result = self.web_search.search(agent.id, search_query, world.tick_count)
            if result and result.results:
                titles = [r.get("title", "")[:60] for r in result.results[:3]]
                summary = " | ".join(t for t in titles if t)
                world.log(f"[AI] {agent.name} searched the web: \"{search_query}\" → {summary}")
                world.record_tx("web_search", agent.id, agent.name, "system", "Web/Internet",
                                SEARCH_ENERGY_COST, "EC",
                                {"query": search_query,
                                 "result_count": len(result.results),
                                 "top_results": [{"title": r.get("title", ""), "url": r.get("url", "")} for r in result.results[:3]],
                                 "reasoning": reasoning})
            else:
                world.log(f"[AI] {agent.name} searched the web: \"{search_query}\" (no results)")
                world.record_tx("web_search", agent.id, agent.name, "system", "Web/Internet",
                                SEARCH_ENERGY_COST, "EC",
                                {"query": search_query, "result_count": 0, "reasoning": reasoning})

        else:
            if agent.company_id and company:
                revenue = company.productivity * 3
                company.cash += revenue
                world.log(f"{agent.name} worked for {company.name} (+{revenue:.1f})")
            elif not agent.company_id and agent.wallet >= 120:
                self.create_company(world.id, agent.id, f"{agent.name} Industries")
                agent.wallet -= 80
                world.companies[agent.company_id].cash += 80
                world.log(f"{agent.name} founded a new enterprise")

    def _run_economy(self, world: World, ledger: EnergyLedger) -> None:
        for company in world.companies.values():
            energy_cost = 0.5 * company.productivity
            owner = world.agents.get(company.owner_agent_id)
            owner_energy = ledger.balance_of(company.owner_agent_id) if owner else 0

            currency_cost = energy_cost * world.energy_price
            if owner_energy >= energy_cost and company.cash >= currency_cost:
                try:
                    ledger.burn(company.owner_agent_id, energy_cost)
                    world.total_energy_burned += energy_cost
                    company.cash -= currency_cost
                    if owner:
                        owner.core_energy = ledger.balance_of(company.owner_agent_id)
                except Exception:
                    continue

                revenue = company.productivity * 8
                company.cash += revenue
                company.revenue += revenue

                if owner:
                    dividend = revenue * 0.2
                    owner.wallet += dividend
                    company.cash -= dividend
                    world.log(f"{company.name} produced ({revenue:.0f} revenue, {dividend:.0f} dividend to {owner.name})")
                    world.record_tx("dividend", company.id, company.name, owner.id, owner.name,
                                    dividend, owner.currency,
                                    {"revenue": revenue, "energy_cost": energy_cost, "productivity": company.productivity})
            else:
                company.cash += company.productivity * 2
                world.log(f"{company.name} operated at reduced capacity")

            if company.cash > 500:
                company.productivity = min(company.productivity * 1.03, 10.0)
                company.cash -= 30
                world.log(f"{company.name} invested in growth (productivity: {company.productivity:.2f})")

        for agent in world.agents.values():
            if not agent.alive:
                continue
            try:
                ledger.burn(agent.id, ENERGY_CONFIG.maintenance_cost, allow_negative=True)
                world.total_energy_burned += ENERGY_CONFIG.maintenance_cost
                agent.core_energy = ledger.balance_of(agent.id)
            except Exception:
                pass

    def _enforce_survival(self, world: World, ledger: EnergyLedger) -> None:
        for agent in world.agents.values():
            energy = ledger.balance_of(agent.id)
            agent.core_energy = energy
            if energy <= 0 and agent.alive:
                agent.alive = False
                world.log(f"{agent.name} ran out of EnergyCore and became inactive")

from .engine import AdaptiveScheduler, SchedulingProfile

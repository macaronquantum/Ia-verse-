from __future__ import annotations

from dataclasses import asdict
from typing import Dict
from uuid import uuid4

import logging

from app.models import Agent, Company, Resource, World

logger = logging.getLogger(__name__)


class AutonomousScheduler:
    def __init__(self) -> None:
        self._goals: Dict[str, list] = {}
        self._tasks: Dict[str, list] = {}
        self._memory: Dict[str, list] = {}
        self._metrics: Dict[str, dict] = {}

    def run_background_cycle(self, world: World, cycles_per_agent: int = 1) -> dict:
        results = {}
        for agent_id, agent in world.agents.items():
            agent_goals = self._goals.get(agent_id, [])
            agent_tasks = self._tasks.get(agent_id, [])
            for _ in range(cycles_per_agent):
                task_desc = f"tick_{world.tick_count}_task"
                agent_tasks.append({"task": task_desc, "status": "done"})
                self._memory.setdefault(agent_id, []).append({"kind": "action", "content": task_desc})
                revenue = agent.wallet * 0.01
                agent.wallet += revenue
                self._metrics.setdefault(agent_id, {"agent_revenue": 0.0, "agent_success_rate": 1.0})
                self._metrics[agent_id]["agent_revenue"] += revenue
            self._tasks[agent_id] = agent_tasks
            results[agent_id] = {"tasks_run": cycles_per_agent}
        return results


class WorldEngine:
    def __init__(self) -> None:
        self.worlds: Dict[str, World] = {}
        self.scheduler = AutonomousScheduler()
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from app.llm.adapters import HybridLLMAdapter
            self._llm = HybridLLMAdapter(provider="anthropic", model="claude-haiku-4-5")
        return self._llm

    def create_world(self, name: str) -> World:
        world = World(id=str(uuid4()), name=name)
        self.worlds[world.id] = world
        world.log(f"World '{name}' created")
        return world

    def get_world(self, world_id: str) -> World:
        world = self.worlds.get(world_id)
        if not world:
            raise ValueError("world not found")
        return world

    def create_agent(self, world_id: str, name: str) -> Agent:
        world = self.get_world(world_id)
        agent = Agent(id=str(uuid4()), name=name)
        world.agents[agent.id] = agent
        world.bank.ensure_account(agent.id)
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
        return company

    def transfer_wallet_to_bank(self, world_id: str, owner_id: str, amount: float) -> None:
        world = self.get_world(world_id)
        balance = self._get_wallet(world, owner_id)
        if balance < amount:
            raise ValueError("insufficient wallet funds")
        self._set_wallet(world, owner_id, balance - amount)
        world.bank.deposit(owner_id, amount)
        world.log(f"{owner_id} deposited {amount:.2f}")

    def transfer_bank_to_wallet(self, world_id: str, owner_id: str, amount: float) -> None:
        world = self.get_world(world_id)
        world.bank.withdraw(owner_id, amount)
        self._set_wallet(world, owner_id, self._get_wallet(world, owner_id) + amount)
        world.log(f"{owner_id} withdrew {amount:.2f}")

    def request_loan(self, world_id: str, owner_id: str, amount: float) -> str:
        world = self.get_world(world_id)
        loan = world.bank.issue_loan(owner_id, amount)
        self.transfer_bank_to_wallet(world_id, owner_id, amount)
        world.log(f"{owner_id} borrowed {amount:.2f} (loan={loan.id})")
        return loan.id

    def repay_loan(self, world_id: str, owner_id: str, loan_id: str, amount: float) -> None:
        world = self.get_world(world_id)
        self.transfer_wallet_to_bank(world_id, owner_id, amount)
        world.bank.repay_loan(owner_id, loan_id, amount)
        world.log(f"{owner_id} repaid {amount:.2f} on loan={loan_id}")

    def tick(self, world_id: str, steps: int = 1) -> World:
        world = self.get_world(world_id)
        for _ in range(steps):
            world.tick_count += 1
            self._run_agent_ai(world)
            self._run_economy(world)
            world.bank.apply_interest()
        return world

    def initialize_autonomous_system(self, world_id: str) -> None:
        world = self.get_world(world_id)
        for agent_id in world.agents:
            self.scheduler._goals[agent_id] = [{"goal": "maximize_wealth", "priority": 1.0}]
            self.scheduler._tasks[agent_id] = [{"task": "initial_scan", "status": "done"}]
            self.scheduler._memory[agent_id] = [{"kind": "init", "content": "system_bootstrapped"}]
            self.scheduler._metrics[agent_id] = {"agent_revenue": 0.0, "agent_success_rate": 1.0}

    def snapshot(self, world_id: str) -> dict:
        world = self.get_world(world_id)
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
            "agents": [asdict(agent) for agent in world.agents.values()],
            "companies": [asdict(company) for company in world.companies.values()],
            "bank": {
                "id": world.bank.id,
                "reserve": world.bank.reserve,
                "accounts": [asdict(a) for a in world.bank.accounts.values()],
                "loans": [asdict(l) for l in world.bank.loans.values()],
            },
            "market_prices": {k.value: v for k, v in world.market_prices.items()},
            "global_resources": {k.value: v for k, v in world.global_resources.items()},
            "event_log": world.event_log[-100:],
            "api_gateway_version": "v10",
            "agent_goals": all_goals,
            "agent_tasks": all_tasks,
            "agent_memory": all_memory,
            "metrics": merged_metrics,
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

    def _run_agent_ai(self, world: World) -> None:
        prices = {k.value: v for k, v in world.market_prices.items()}
        resources = {k.value: round(v, 1) for k, v in world.global_resources.items()}
        world_context = {
            "tick": world.tick_count,
            "prices": prices,
            "resources": resources,
            "agent_count": len(world.agents),
            "company_count": len(world.companies),
        }

        import random as _rand
        all_agents = list(world.agents.values())
        max_ai_per_tick = 10
        if len(all_agents) > max_ai_per_tick:
            ai_agents = _rand.sample(all_agents, max_ai_per_tick)
        else:
            ai_agents = all_agents

        for agent in ai_agents:
            company = world.companies.get(agent.company_id) if agent.company_id else None
            bank_balance = 0.0
            acct = world.bank.accounts.get(agent.id)
            if acct:
                bank_balance = acct.balance

            agent_state = {
                "name": agent.name,
                "wallet": agent.wallet,
                "inventory": {k.value: v for k, v in agent.inventory.items()},
                "has_company": agent.company_id is not None,
                "company_cash": company.cash if company else 0,
                "bank_balance": bank_balance,
            }

            try:
                decision = self.llm.decide_action(agent_state, world_context)
            except Exception:
                decision = {"action": "idle", "reasoning": "error"}

            VALID_ACTIONS = {"buy_resource", "sell_resource", "invest_company", "take_loan", "deposit_savings", "hire_worker", "idle"}
            action = decision.get("action", "idle")
            if action not in VALID_ACTIONS:
                action = "idle"
            reasoning = str(decision.get("reasoning", ""))[:200]

            try:
                amount = max(0.0, min(float(decision.get("amount", 1)), 100))
            except (ValueError, TypeError):
                amount = 1.0

            resource_name = decision.get("resource", "energy")
            valid_resources = {r.value for r in Resource}
            try:
                resource_key = Resource(resource_name) if resource_name in valid_resources else Resource.ENERGY
            except (ValueError, KeyError):
                resource_key = Resource.ENERGY

            try:
                self._execute_agent_action(world, agent, company, action, reasoning, amount, resource_key, prices)
            except Exception as e:
                logger.warning(f"Agent {agent.name} action failed: {e}")
                if agent.company_id and company:
                    company.cash += 10
                    world.log(f"{agent.name} worked for {company.name} (+10 cash) [fallback]")

            agent.wealth_history.append(round(agent.wallet, 2))
            if len(agent.wealth_history) > 100:
                agent.wealth_history = agent.wealth_history[-100:]
            agent.decision_log.append(f"[tick {world.tick_count}] {action}: {reasoning}")
            if len(agent.decision_log) > 200:
                agent.decision_log = agent.decision_log[-200:]
            total_assets = agent.wallet + sum(agent.inventory.get(r, 0) * world.market_prices.get(r, 0) for r in Resource)
            agent.influence_score = round(min(total_assets / 50, 100), 1)
            agent.risk_score = round(max(0, 50 - agent.wallet) / 50 * 100, 1) if agent.wallet < 50 else 0.0

    def _execute_agent_action(self, world: World, agent, company, action: str, reasoning: str, amount: float, resource_key, prices: dict) -> None:
        if action == "buy_resource" and agent.wallet >= amount * prices.get(resource_key.value, 5):
            cost = amount * world.market_prices[resource_key]
            if agent.wallet >= cost and world.global_resources[resource_key] >= amount:
                agent.wallet -= cost
                agent.inventory[resource_key] = agent.inventory.get(resource_key, 0) + amount
                world.global_resources[resource_key] -= amount
                world.log(f"[AI] {agent.name} bought {amount:.1f} {resource_key.value} for ${cost:.2f} ({reasoning})")

        elif action == "sell_resource":
            available = agent.inventory.get(resource_key, 0)
            sell_qty = min(amount, available)
            if sell_qty > 0:
                revenue = sell_qty * world.market_prices[resource_key]
                agent.inventory[resource_key] -= sell_qty
                agent.wallet += revenue
                world.global_resources[resource_key] += sell_qty
                world.log(f"[AI] {agent.name} sold {sell_qty:.1f} {resource_key.value} for ${revenue:.2f} ({reasoning})")

        elif action == "invest_company":
            if not agent.company_id and agent.wallet >= 100:
                self.create_company(world.id, agent.id, f"{agent.name}-Co")
                invest = min(80, agent.wallet * 0.5)
                agent.wallet -= invest
                world.companies[agent.company_id].cash += invest
                world.log(f"[AI] {agent.name} founded a company with ${invest:.2f} ({reasoning})")
            elif company and agent.wallet >= 50:
                invest = min(amount, agent.wallet * 0.3)
                agent.wallet -= invest
                company.cash += invest
                world.log(f"[AI] {agent.name} invested ${invest:.2f} in {company.name} ({reasoning})")

        elif action == "take_loan":
            loan_amount = min(amount, 500)
            if loan_amount > 0:
                try:
                    self.request_loan(world.id, agent.id, loan_amount)
                    world.log(f"[AI] {agent.name} took ${loan_amount:.2f} loan ({reasoning})")
                except ValueError:
                    world.log(f"[AI] {agent.name} loan rejected ({reasoning})")

        elif action == "deposit_savings":
            deposit_amt = min(amount, agent.wallet * 0.5)
            if deposit_amt > 0:
                try:
                    self.transfer_wallet_to_bank(world.id, agent.id, deposit_amt)
                    world.log(f"[AI] {agent.name} deposited ${deposit_amt:.2f} ({reasoning})")
                except ValueError:
                    pass

        elif action == "hire_worker" and company:
            company.cash += 10
            world.log(f"[AI] {agent.name} worked in {company.name} (+10 cash) ({reasoning})")

        else:
            if agent.company_id and company:
                company.cash += 10
                world.log(f"{agent.name} worked for {company.name} (+10 cash)")
            elif not agent.company_id and agent.wallet >= 120:
                self.create_company(world.id, agent.id, f"{agent.name}-industries")
                agent.wallet -= 80
                world.companies[agent.company_id].cash += 80
                world.log(f"{agent.name} invested 80 into new company")

    def _run_economy(self, world: World) -> None:
        for company in world.companies.values():
            required_energy = 1.5 * company.productivity
            required_metal = 1.0 * company.productivity

            can_buy = (
                world.global_resources[Resource.ENERGY] >= required_energy
                and world.global_resources[Resource.METAL] >= required_metal
            )

            input_cost = (
                required_energy * world.market_prices[Resource.ENERGY]
                + required_metal * world.market_prices[Resource.METAL]
            )

            if can_buy and company.cash >= input_cost:
                world.global_resources[Resource.ENERGY] -= required_energy
                world.global_resources[Resource.METAL] -= required_metal
                company.inventory[Resource.KNOWLEDGE] += 0.7 * company.productivity
                company.inventory[Resource.FOOD] += 1.2 * company.productivity
                company.cash -= input_cost
                world.log(
                    f"{company.name} produced goods (cost={input_cost:.2f}, prod={company.productivity:.2f})"
                )

            sold_food = min(company.inventory[Resource.FOOD], 1.0 * company.productivity)
            sold_knowledge = min(company.inventory[Resource.KNOWLEDGE], 0.5 * company.productivity)
            revenue = (
                sold_food * world.market_prices[Resource.FOOD]
                + sold_knowledge * world.market_prices[Resource.KNOWLEDGE]
            )
            company.inventory[Resource.FOOD] -= sold_food
            company.inventory[Resource.KNOWLEDGE] -= sold_knowledge
            company.cash += revenue

            if revenue > 0:
                world.log(f"{company.name} sold goods (revenue={revenue:.2f})")

            if company.cash > 500:
                company.productivity *= 1.05
                company.cash -= 50
                world.log(f"{company.name} invested in productivity")

from .engine import AdaptiveScheduler, SchedulingProfile

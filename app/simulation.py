from __future__ import annotations

from dataclasses import asdict
from typing import Dict
from uuid import uuid4

from app.agents.mind import AgentMind
from app.models import Agent, Company, Resource, World
from app.world.crisis_engine import CrisisEngine
from app.world.state import GlobalState


class WorldEngine:
    def __init__(self) -> None:
        self.worlds: Dict[str, World] = {}
        self.minds: Dict[str, Dict[str, AgentMind]] = {}
        self.crisis_engines: Dict[str, CrisisEngine] = {}

    def create_world(self, name: str) -> World:
        world = World(id=str(uuid4()), name=name)
        self.worlds[world.id] = world
        self.minds[world.id] = {}
        self.crisis_engines[world.id] = CrisisEngine()
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
        self.minds[world_id][agent.id] = AgentMind(agent)
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
            global_state = GlobalState.from_world(world)
            self._run_agent_ai(world)
            self._run_economy(world)
            self._regenerate_resources(world)
            crisis_engine = self.crisis_engines[world_id]
            crises = crisis_engine.evaluate(world, global_state)
            for event in crisis_engine.apply_effects(world):
                world.log(f"Crisis engine: {event}")
            if any(level > 0 for level in crises.values()):
                world.log(f"Active crises: {crises}")
            world.bank.apply_interest()
            self._pay_dividends(world)
        return world

    def snapshot(self, world_id: str) -> dict:
        world = self.get_world(world_id)
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
        }

    def _regenerate_resources(self, world: World) -> None:
        regen_rates = {
            Resource.ENERGY: 50.0,
            Resource.FOOD: 30.0,
            Resource.METAL: 20.0,
            Resource.KNOWLEDGE: 10.0,
        }
        for resource, rate in regen_rates.items():
            cap = 15000.0
            current = world.global_resources[resource]
            if current < cap:
                world.global_resources[resource] = min(cap, current + rate)

    def _pay_dividends(self, world: World) -> None:
        for company in world.companies.values():
            if company.cash > 300:
                dividend = company.cash * 0.05
                company.cash -= dividend
                owner = world.agents.get(company.owner_agent_id)
                if owner:
                    owner.wallet += dividend

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
        for agent in world.agents.values():
            mind = self.minds[world.id][agent.id]
            global_state = GlobalState.from_world(world)
            actions = mind.run_cycle(world, global_state)
            world.log(f"Agent '{agent.name}' cognition cycle actions: {actions}")

            if not agent.company_id and agent.wallet >= 120:
                self.create_company(world.id, agent.id, f"{agent.name}-industries")
                agent.wallet -= 80
                company = world.companies[agent.company_id]
                company.cash += 80
                world.log(f"Agent '{agent.name}' invested 80 into new company")
                continue

            if agent.company_id:
                company = world.companies[agent.company_id]
                wage = min(10.0, agent.wallet)
                if wage > 0:
                    agent.wallet -= wage
                    company.cash += wage
                    world.log(f"Agent '{agent.name}' worked for company '{company.name}' (+{wage:.1f} cash)")

                if company.cash < 25:
                    try:
                        loan_id = self.request_loan(world.id, company.id, 100)
                        world.log(f"Company '{company.name}' took emergency loan {loan_id}")
                    except ValueError:
                        world.log(f"Company '{company.name}' failed to get emergency loan")

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
            world.global_resources[Resource.FOOD] += sold_food
            world.global_resources[Resource.KNOWLEDGE] += sold_knowledge
            company.cash += revenue

            if revenue > 0:
                world.log(f"{company.name} sold goods (revenue={revenue:.2f})")

            if company.cash > 500:
                company.productivity *= 1.05
                company.cash -= 50
                world.log(f"{company.name} invested in productivity")

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from app.agents.personality import Personality
from app.agents.tools.deception_stub import deception_plan
from app.memory.store import STORE

from app.culture.beliefs import BeliefSystem
from app.models import Agent, Resource, World
from app.social.messaging import CommunicationHub
from app.social.network import DependencyGraph, InfluenceGraph, TrustGraph
from app.world.state import GlobalState, partial_view


@dataclass
class CognitiveBudget:
    core_energy: float = 2.0
    llm_tokens: int = 200
    compute_time: float = 1.0


@dataclass
class AgentMindState:
    beliefs: Dict[str, float] = field(default_factory=dict)
    goals: List[Dict[str, object]] = field(default_factory=list)
    plan: Dict[str, object] = field(default_factory=dict)
    chosen_actions: List[Dict[str, object]] = field(default_factory=list)
    last_outcome: Dict[str, float] = field(default_factory=dict)




def _normalize(values: list[float]) -> list[float]:
    total = sum(max(0.0, v) for v in values)
    if total <= 0:
        return [0.0 for _ in values]
    return [max(0.0, v) / total for v in values]


def decision_weighting(
    instruction: dict[str, float],
    personality: Personality,
    survival_estimate: float,
    expected_profit: float,
    social_value: float = 0.2,
) -> dict[str, float]:
    """Compute owner-vs-self weighting and normalized action scores."""
    weight_owner = personality.obedience * (1 - personality.risk)
    weight_self = (1 - personality.obedience) * (personality.greed + personality.risk)
    ideology_modifiers = {
        "capitalist": 1.1,
        "cooperative": 0.9,
        "anarchist": 1.05,
        "pirate": 1.1,
        "bureaucrat": 0.95,
    }
    weight_self *= ideology_modifiers.get(personality.ideology, 1.0)
    scores = _normalize([weight_owner * instruction.get("value", 0.0), weight_self * expected_profit, personality.cooperation * social_value])
    return {
        "owner": scores[0],
        "self": scores[1],
        "social": scores[2],
        "survival_estimate": survival_estimate,
    }

class AgentMind:
    def __init__(self, agent: Agent, confidence: float = 0.65) -> None:
        self.agent = agent
        self.confidence = confidence
        self.state = AgentMindState()
        self.belief_system = BeliefSystem()
        self.trust_graph = TrustGraph()
        self.influence_graph = InfluenceGraph()
        self.dependency_graph = DependencyGraph()
        self.messaging = CommunicationHub(self.trust_graph, self.influence_graph, self.dependency_graph)
        self.budget = CognitiveBudget()
        self.personality = Personality()

    def run_cycle(self, world: World, global_state: GlobalState) -> List[Dict[str, object]]:
        perceived = self.perceive_world(global_state)
        beliefs = self.update_beliefs(perceived)
        goals = self.evaluate_goals(beliefs)
        plan = self.plan_strategy(goals)
        actions = self.decide_actions(plan)
        outcomes = self.execute_actions(world, actions)
        self.learn_from_outcomes(outcomes)
        return actions

    def perceive_world(self, global_state: GlobalState) -> Dict[str, object]:
        known_agents = {
            target: abs(weight)
            for target, weight in self.trust_graph.edges.get(self.agent.id, {}).items()
            if weight > 0
        }
        perception = partial_view(global_state, self.agent.id, self.confidence, known_agents)
        self._consume_budget(energy=0.4, tokens=40, compute=0.1)
        return perception

    def update_beliefs(self, perception: Dict[str, object]) -> Dict[str, float]:
        crises = perception.get("crisis_signals", {})
        energy_price = float(perception.get("energy_price", 0.0))

        self.state.beliefs.update(
            {
                "scarcity_risk": min(1.0, crises.get("energy_shortage", 0.0) + energy_price / 20.0),
                "institution_instability": min(1.0, crises.get("bank_run", 0.0) + crises.get("economic_collapse", 0.0)),
                "epistemic_uncertainty": min(1.0, crises.get("oracle_failure", 0.0) + (1 - self.confidence)),
            }
        )
        self._consume_budget(energy=0.2, tokens=20, compute=0.1)
        return self.state.beliefs

    def evaluate_goals(self, beliefs: Dict[str, float]) -> List[Dict[str, object]]:
        survival_score = (
            (self.agent.inventory[Resource.ENERGY] / 15.0)
            + (self.agent.wallet / 200.0)
            + beliefs.get("institution_instability", 0.0)
        )
        power_score = (
            0.4 * self.influence_graph.get_weight(self.agent.id, "bank")
            + 0.4 * (self.agent.wallet / 300.0)
            + 0.2 * (1.0 - beliefs.get("scarcity_risk", 0.0))
        )
        meaning_score = (
            beliefs.get("epistemic_uncertainty", 0.0)
            + len(self.belief_system.ideology_scores) * 0.2
            + self.belief_system.religion_intensity * 0.5
        )

        goals = [
            {"name": "survival", "score": survival_score},
            {"name": "power", "score": power_score},
            {"name": "meaning", "score": meaning_score},
        ]
        self.state.goals = sorted(goals, key=lambda g: float(g["score"]), reverse=True)
        self._consume_budget(energy=0.3, tokens=30, compute=0.2)
        return self.state.goals

    def plan_strategy(self, goals: List[Dict[str, object]]) -> Dict[str, object]:
        primary_goal = str(goals[0]["name"]) if goals else "survival"

        strategy = {
            "survival": "stabilize_resources",
            "power": "expand_influence",
            "meaning": "advance_world_model",
        }.get(primary_goal, "stabilize_resources")

        plan = {
            "goal": primary_goal,
            "strategy": strategy,
            "plan": f"Execute {strategy} under constrained cognition budget",
            "tasks": self._tasks_for_strategy(strategy),
        }
        self.state.plan = plan
        self._consume_budget(energy=0.35, tokens=55, compute=0.2)
        return plan

    def decide_actions(self, plan: Dict[str, object]) -> List[Dict[str, object]]:
        actions: List[Dict[str, object]] = []
        for task in plan.get("tasks", []):
            action = self._action_for_task(task)
            weight = decision_weighting({"value": 1.0}, self.personality, 0.5, expected_profit=0.4, social_value=0.3)
            chosen = action
            if weight["self"] > weight["owner"] and task == "secure_liquidity":
                chosen = "trade_for_energy"
            actions.append({"task": task, "action": chosen, "reasoning": weight})
            STORE.log_tamper_event({"kind": "decision_trace", "agent_id": self.agent.id, "task": task, "weights": weight})
            if self.personality.manipulativeness > 0.6 and chosen in {"build_alliance", "shape_narrative"}:
                deception_plan(self.agent.id, "attempt to spoof proof for alliance bribe")

        if self.budget.llm_tokens < 30:
            actions = actions[:1]

        self.state.chosen_actions = actions
        self._consume_budget(energy=0.25, tokens=20, compute=0.1)
        return actions

    def execute_actions(self, world: World, actions: List[Dict[str, object]]) -> Dict[str, float]:
        outcome = {"resource_gain": 0.0, "influence_gain": 0.0, "knowledge_gain": 0.0}

        for decision in actions:
            action = decision["action"]
            if action == "conserve_energy":
                self.agent.inventory[Resource.ENERGY] += 0.2
                outcome["resource_gain"] += 0.2
            elif action == "trade_for_energy" and self.agent.wallet >= world.market_prices[Resource.ENERGY]:
                self.agent.wallet -= world.market_prices[Resource.ENERGY]
                self.agent.inventory[Resource.ENERGY] += 0.5
                outcome["resource_gain"] += 0.5
            elif action == "build_alliance":
                peer = next((a for a in world.agents if a != self.agent.id), None)
                if peer:
                    self.messaging.ally(self.agent.id, peer, "mutual growth")
                    outcome["influence_gain"] += 0.3
            elif action == "shape_narrative":
                peer = next((a for a in world.agents if a != self.agent.id), None)
                if peer:
                    self.messaging.spread_beliefs(self.agent.id, peer, "creator hypothesis", 0.6)
                    self.belief_system.spread_meme("creator hypothesis", 0.6)
                    outcome["knowledge_gain"] += 0.4
            elif action == "investigate_reality":
                self.belief_system.form_ideology("empirical idealism", 0.2)
                self.belief_system.emerge_religion(0.1)
                outcome["knowledge_gain"] += 0.5

        self.state.last_outcome = outcome
        self._consume_budget(energy=0.35, tokens=25, compute=0.2)
        return outcome

    def learn_from_outcomes(self, outcomes: Dict[str, float]) -> None:
        learning_signal = outcomes["knowledge_gain"] + outcomes["influence_gain"] + outcomes["resource_gain"]
        self.confidence = max(0.05, min(0.95, self.confidence + (learning_signal - 0.3) * 0.02))
        self.state.beliefs["learning_signal"] = learning_signal
        self.state.beliefs["budget_pressure"] = max(0.0, 1.0 - (self.budget.llm_tokens / 200.0))
        self._consume_budget(energy=0.15, tokens=10, compute=0.1)

    def _tasks_for_strategy(self, strategy: str) -> List[str]:
        if strategy == "stabilize_resources":
            return ["audit_energy", "secure_liquidity"]
        if strategy == "expand_influence":
            return ["identify_allies", "signal_strength"]
        return ["question_models", "propagate_memes"]

    def _action_for_task(self, task: str) -> str:
        mapping = {
            "audit_energy": "conserve_energy",
            "secure_liquidity": "trade_for_energy",
            "identify_allies": "build_alliance",
            "signal_strength": "shape_narrative",
            "question_models": "investigate_reality",
            "propagate_memes": "shape_narrative",
        }
        return mapping[task]

    def _consume_budget(self, energy: float, tokens: int, compute: float) -> None:
        self.budget.core_energy = max(0.0, self.budget.core_energy - energy)
        self.budget.llm_tokens = max(0, self.budget.llm_tokens - tokens)
        self.budget.compute_time = max(0.0, self.budget.compute_time - compute)

from __future__ import annotations

from dataclasses import asdict
from typing import List
from uuid import uuid4

from app.models import AgentGoal, World


class GoalSystem:
    def initialize_default_goals(self, world: World, agent_id: str) -> None:
        if any(goal.agent_id == agent_id for goal in world.agent_goals.values()):
            return
        self.create_goal(world, agent_id, "create profitable tools", priority=10, reward=30)
        self.create_goal(world, agent_id, "launch automation services", priority=9, reward=25)
        self.create_goal(world, agent_id, "improve marketplace supply", priority=8, reward=20)
        self.create_goal(world, agent_id, "generate revenue streams", priority=10, reward=40)

    def create_goal(
        self,
        world: World,
        agent_id: str,
        title: str,
        priority: int,
        reward: float,
        deadline_tick: int | None = None,
    ) -> str:
        goal_id = str(uuid4())
        world.agent_goals[goal_id] = AgentGoal(
            id=goal_id,
            agent_id=agent_id,
            title=title,
            priority=priority,
            reward=reward,
            deadline_tick=deadline_tick,
        )
        return goal_id

    def choose_goal(self, world: World, agent_id: str) -> AgentGoal | None:
        goals = [
            g
            for g in world.agent_goals.values()
            if g.agent_id == agent_id and g.status in {"pending", "active"}
        ]
        if not goals:
            return None
        goals.sort(key=lambda g: (g.priority, g.reward), reverse=True)
        chosen = goals[0]
        chosen.status = "active"
        return chosen

    def complete_goal(self, world: World, goal_id: str) -> None:
        goal = world.agent_goals.get(goal_id)
        if goal:
            goal.status = "completed"

    def list_goals(self, world: World, agent_id: str) -> List[dict]:
        return [asdict(g) for g in world.agent_goals.values() if g.agent_id == agent_id]

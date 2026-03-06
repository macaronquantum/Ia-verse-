from __future__ import annotations

from dataclasses import asdict
from typing import List
from uuid import uuid4

from app.models import AgentGoal, AgentTask, World


class Planner:
    def plan_tasks(self, world: World, goal: AgentGoal) -> List[AgentTask]:
        # LLM reasoning integration point: replace with external planning model call.
        plan_templates = [
            f"research strategy for: {goal.title}",
            f"execute primary action for: {goal.title}",
            f"evaluate monetization for: {goal.title}",
        ]
        tasks: List[AgentTask] = []
        for title in plan_templates:
            task_id = str(uuid4())
            task = AgentTask(id=task_id, goal_id=goal.id, agent_id=goal.agent_id, title=title)
            world.agent_tasks[task_id] = task
            tasks.append(task)
        return tasks

    def list_tasks(self, world: World, agent_id: str) -> List[dict]:
        return [asdict(t) for t in world.agent_tasks.values() if t.agent_id == agent_id]

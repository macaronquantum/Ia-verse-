from __future__ import annotations

from app.agents.business_builder import BusinessBuilder
from app.agents.executor import TaskExecutor
from app.agents.goal_system import GoalSystem
from app.agents.memory_manager import MemoryManager
from app.agents.planner import Planner
from app.agents.tool_factory import ToolFactory
from app.agents.tool_selector import ToolSelector
from app.models import World


class AgentBrain:
    def __init__(self) -> None:
        self.goals = GoalSystem()
        self.planner = Planner()
        self.selector = ToolSelector()
        self.executor = TaskExecutor()
        self.memory = MemoryManager()
        self.factory = ToolFactory()
        self.business_builder = BusinessBuilder()

    def run_cycle(self, world: World, agent_id: str) -> dict:
        self.goals.initialize_default_goals(world, agent_id)
        goal = self.goals.choose_goal(world, agent_id)
        if not goal:
            return {"status": "idle", "agent_id": agent_id}

        tasks = self.planner.plan_tasks(world, goal)
        last_result = ""
        for task in tasks:
            tool = self.selector.select_optimal_tool(world, task.title)
            tool_id = tool.id if tool else None
            last_result = self.executor.execute_task(world, task, tool_id)
            self.memory.remember_short_term(world, agent_id, f"tool usage results: {last_result}")
            self.memory.remember_episode(world, agent_id, f"action history and outcomes: {task.result_summary}")

        if not world.tool_registry:
            new_tool = self.factory.create_tool(world, agent_id, "autonomous productivity tool")
            self.memory.remember_long_term(world, agent_id, f"learned strategies: created tool {new_tool.id}", 0.9)

        if not world.agents_table[agent_id]["businesses"]:
            business = self.business_builder.create_business(world, agent_id)
            self.memory.remember_long_term(world, agent_id, f"business outcomes: launched {business.name}", 0.8)

        # Monetization + economy accounting
        reward = goal.reward
        world.agents_table[agent_id]["agent_wallet"] += reward
        world.agent_revenue[agent_id] = world.agent_revenue.get(agent_id, 0.0) + reward
        self.memory.remember_long_term(world, agent_id, f"revenue history: +{reward}", 0.75)
        self.goals.complete_goal(world, goal.id)

        return {
            "status": "ok",
            "agent_id": agent_id,
            "goal": goal.title,
            "tasks_executed": len(tasks),
            "last_result": last_result,
        }

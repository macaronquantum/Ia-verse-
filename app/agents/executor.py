from __future__ import annotations

from uuid import uuid4

from app.models import AgentTask, AgentTransaction, World


class TaskExecutor:
    def execute_task(self, world: World, task: AgentTask, tool_id: str | None = None) -> str:
        task.selected_tool_id = tool_id
        task.status = "running"

        energy_spent = 1.0
        if tool_id and tool_id in world.tool_registry:
            tool = world.tool_registry[tool_id]
            energy_spent = tool.energy_cost

        identity = world.agents_table[task.agent_id]
        identity["energy_balance"] = max(0.0, float(identity["energy_balance"]) - energy_spent)

        result = f"task={task.title} executed via api_gateway={world.api_gateway_version} tool={tool_id}"
        task.result_summary = result
        task.status = "done"

        tx_id = str(uuid4())
        world.agent_transactions[tx_id] = AgentTransaction(
            id=tx_id,
            agent_id=task.agent_id,
            category="energy_expense",
            amount=energy_spent,
            metadata=task.title,
        )
        world.agent_expenses[task.agent_id] = world.agent_expenses.get(task.agent_id, 0.0) + energy_spent
        return result

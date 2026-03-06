from __future__ import annotations

from dataclasses import asdict

from app.models import ToolManifest, World


class ToolSelector:
    def discover_tools(self, world: World) -> list[dict]:
        return [asdict(tool) for tool in world.tool_registry.values()]

    def select_optimal_tool(self, world: World, task_title: str) -> ToolManifest | None:
        if not world.tool_registry:
            return None

        def score(tool: ToolManifest) -> float:
            # Higher success/reputation good; lower cost/time good.
            return (
                (tool.success_rate * 45)
                + (tool.reputation * 25)
                - (tool.energy_cost * 10)
                - (tool.execution_time * 4)
            )

        ranked = sorted(world.tool_registry.values(), key=score, reverse=True)
        return ranked[0]

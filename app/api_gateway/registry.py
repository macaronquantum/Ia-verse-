"""In-memory tool registry with simple monetization support."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ToolManifest:
    tool_id: str
    owner_id: str
    name: str
    price: float
    pricing_model: str


class ToolRegistry:
    def __init__(self) -> None:
        self.tools: dict[str, ToolManifest] = {}

    def publish(self, manifest: ToolManifest) -> None:
        self.tools[manifest.tool_id] = manifest

    def get(self, tool_id: str) -> ToolManifest:
        return self.tools[tool_id]

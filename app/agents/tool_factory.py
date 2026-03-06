"""Tool generation pipeline stubbed for safe dev execution."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.api_gateway.registry import ToolManifest, ToolRegistry


@dataclass
class ToolBuildResult:
    tool_id: str
    published: bool
    retries: int


class ToolFactory:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def build_and_publish(self, owner_id: str, name: str, price: float, pricing_model: str = "subscription") -> ToolBuildResult:
        # Stub workflow: generation/lint/security/sandbox assumed successful in DEV mode.
        tool_id = str(uuid4())
        manifest = ToolManifest(tool_id=tool_id, owner_id=owner_id, name=name, price=price, pricing_model=pricing_model)
        self.registry.publish(manifest)
        return ToolBuildResult(tool_id=tool_id, published=True, retries=0)

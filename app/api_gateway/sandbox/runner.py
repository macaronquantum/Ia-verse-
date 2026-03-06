from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models.tool_manifest import ToolManifest


class SandboxRunner(ABC):
    @abstractmethod
    def run(
        self,
        manifest: ToolManifest,
        input_payload: dict[str, Any],
        exec_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

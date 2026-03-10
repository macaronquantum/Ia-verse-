from __future__ import annotations

from typing import Any

from app.api_gateway.sandbox.runner import SandboxRunner
from app.models.tool_manifest import ToolManifest


class WasmRunner(SandboxRunner):
    def run(
        self,
        manifest: ToolManifest,
        input_payload: dict[str, Any],
        exec_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "status": "not_implemented",
            "output": None,
            "logs": ["WASM runner is a v10 skeleton"],
            "duration": 0.0,
            "resource_usage": {},
        }

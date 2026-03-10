from __future__ import annotations

import time
from typing import Any

from app.api_gateway.sandbox.runner import SandboxRunner
from app.models.tool_manifest import ToolManifest


class DockerRunner(SandboxRunner):
    """Dev-friendly docker runner emulator.

    In production this class should shell out to docker with strict options.
    """

    def run(
        self,
        manifest: ToolManifest,
        input_payload: dict[str, Any],
        exec_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start = time.time()
        timeout = manifest.resources.timeout_seconds
        simulated_duration = float(input_payload.get("simulate_duration", 0.01))
        if simulated_duration > timeout:
            return {
                "status": "timeout",
                "output": None,
                "logs": ["execution timed out"],
                "duration": timeout,
                "resource_usage": {"cpu_seconds": timeout, "memory_mb": manifest.resources.memory_mb},
            }
        if manifest.entrypoint == "echo":
            output = {"echo": input_payload}
        else:
            output = {"result": "ok", "entrypoint": manifest.entrypoint, "input": input_payload}
        duration = max(time.time() - start, simulated_duration)
        return {
            "status": "success",
            "output": output,
            "logs": ["sandbox execution completed"],
            "duration": duration,
            "resource_usage": {"cpu_seconds": duration, "memory_mb": min(64, manifest.resources.memory_mb)},
        }

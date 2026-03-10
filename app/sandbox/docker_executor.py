from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass


@dataclass
class DockerExecutionResult:
    stdout: str
    stderr: str
    code: int


class DockerExecutor:
    def __init__(self, image: str = "python:3.11-slim", cpu_quota: int = 50000, memory: str = "256m") -> None:
        self.image = image
        self.cpu_quota = cpu_quota
        self.memory = memory

    def run_python(self, code: str, timeout: int = 20) -> DockerExecutionResult:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
            path = f.name
        cmd = [
            "docker", "run", "--rm", "--network", "none", "--cpus", "0.5", "--memory", self.memory,
            "-v", f"{path}:/app/main.py:ro", self.image, "python", "/app/main.py",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return DockerExecutionResult(stdout=proc.stdout, stderr=proc.stderr, code=proc.returncode)

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class CloudDeployer:
    def deploy_docker(self, image: str, target: str) -> dict:
        cmd = ["docker", "run", "-d", image]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return {"target": target, "stdout": proc.stdout, "stderr": proc.stderr, "code": proc.returncode}

    def deploy_vercel(self, project_dir: str) -> dict:
        proc = subprocess.run(["vercel", "deploy", "--prod"], cwd=project_dir, capture_output=True, text=True)
        return {"stdout": proc.stdout, "stderr": proc.stderr, "code": proc.returncode}

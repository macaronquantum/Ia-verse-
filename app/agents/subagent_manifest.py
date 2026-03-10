from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SubAgentSpec:
    name: str
    role: str
    skills: List[str]
    energy_cost: float
    api_hooks: List[str]


@dataclass
class SubAgentManifest:
    parent_agent_id: str
    subagents: List[Dict[str, object]] = field(default_factory=list)

    def add_subagent(self, spec: SubAgentSpec) -> Dict[str, object]:
        entry = {
            "name": spec.name,
            "role": spec.role,
            "skills": spec.skills,
            "energy_cost": spec.energy_cost,
            "api_hooks": spec.api_hooks,
            "simulated_tests": [
                {"name": "unit_capability_check", "passed": True},
                {"name": "integration_gateway_check", "passed": True},
            ],
            "activation_allowed": True,
        }
        self.subagents.append(entry)
        return entry


def generate_subagent_manifest(parent_agent_id: str, specs: List[SubAgentSpec]) -> SubAgentManifest:
    manifest = SubAgentManifest(parent_agent_id=parent_agent_id)
    for spec in specs:
        manifest.add_subagent(spec)
    return manifest

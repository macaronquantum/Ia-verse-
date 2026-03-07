"""In-memory store for genomes, personalities, lineages and tamper-evident events."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any


@dataclass
class EvolutionMemoryStore:
    genomes: dict[str, dict[str, Any]] = field(default_factory=dict)
    personalities: dict[str, dict[str, Any]] = field(default_factory=dict)
    lineage_children: dict[str, list[str]] = field(default_factory=dict)
    fitness: dict[str, dict[str, float]] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    memetic_spread_count: int = 0

    def save_genome(self, genome_id: str, payload: dict[str, Any]) -> None:
        self.genomes[genome_id] = payload

    def save_personality(self, agent_id: str, payload: dict[str, Any]) -> None:
        self.personalities[agent_id] = payload

    def register_lineage(self, lineage_id: str, child_agent_id: str) -> None:
        self.lineage_children.setdefault(lineage_id, []).append(child_agent_id)

    def log_tamper_event(self, event_data: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(event_data, sort_keys=True)
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        entry = {"digest": digest, "event": event_data}
        self.events.append(entry)
        return entry


STORE = EvolutionMemoryStore()

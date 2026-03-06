from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, Dict


@dataclass
class WeightedGraph:
    edges: DefaultDict[str, Dict[str, float]] = field(default_factory=lambda: defaultdict(dict))

    def set_weight(self, source: str, target: str, weight: float) -> None:
        self.edges[source][target] = max(-1.0, min(1.0, weight))

    def adjust(self, source: str, target: str, delta: float) -> None:
        current = self.edges[source].get(target, 0.0)
        self.set_weight(source, target, current + delta)

    def get_weight(self, source: str, target: str) -> float:
        return self.edges[source].get(target, 0.0)


@dataclass
class TrustGraph(WeightedGraph):
    pass


@dataclass
class InfluenceGraph(WeightedGraph):
    pass


@dataclass
class DependencyGraph(WeightedGraph):
    pass

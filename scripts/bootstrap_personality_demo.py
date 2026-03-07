"""Seed a population and print personality metrics after 1,000 ticks."""

from __future__ import annotations

from app.observability.metrics import METRICS
from app.simulation import WorldEngine


def main() -> None:
    engine = WorldEngine()
    world = engine.create_world("personality-demo")
    for i in range(50):
        engine.create_agent(world.id, f"agent-{i}")
    engine.tick(world.id, 1000)
    print(METRICS.get_population_distribution())
    print({"fraction_rebels": METRICS.fraction_rebels()})


if __name__ == "__main__":
    main()

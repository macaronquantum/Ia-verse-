from app.simulation.engine import SimulationEngine, World


def build_default_engine() -> SimulationEngine:
    world = World()
    world.bootstrap()
    return SimulationEngine(world)

from app.agents.evolution import imitation_event
from app.memory.store import STORE


def test_imitation_updates_traits() -> None:
    STORE.personalities.clear()
    STORE.personalities["observer"] = {
        "obedience": 0.9,
        "greed": 0.1,
        "risk": 0.1,
        "curiosity": 1.0,
        "type_tag": "loyal",
    }
    STORE.personalities["model"] = {
        "obedience": 0.2,
        "greed": 0.8,
        "risk": 0.7,
        "curiosity": 0.2,
        "type_tag": "opportunist",
    }
    STORE.fitness["model"] = {"fitness": 1.0}
    changed = imitation_event("observer", "model", ["obedience", "greed", "risk"], prob=1.0)
    assert changed
    assert STORE.personalities["observer"]["greed"] > 0.1

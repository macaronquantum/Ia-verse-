from app.agents.mind import decision_weighting
from app.agents.personality import Personality


def test_decision_weighting_changes_with_obedience() -> None:
    obedient = Personality(obedience=0.95, risk=0.1, greed=0.1)
    rebel = Personality(obedience=0.1, risk=0.7, greed=0.9)
    a = decision_weighting({"value": 1.0}, obedient, survival_estimate=0.5, expected_profit=0.8)
    b = decision_weighting({"value": 1.0}, rebel, survival_estimate=0.5, expected_profit=0.8)
    assert a["owner"] > a["self"]
    assert b["self"] > b["owner"]

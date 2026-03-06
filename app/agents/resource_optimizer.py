"""Energy spend decision policies."""


def should_spend(task_cost: float, expected_return: float, risk: float, survival_prob: float) -> bool:
    if survival_prob < 0.3:
        return False
    score = (expected_return - task_cost) * max(1 - risk, 0)
    return score > 0

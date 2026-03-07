from app.justice.system import JudgeSystem


def test_suspicious_behavior_blocked() -> None:
    judge = JudgeSystem(auto_block_threshold=2)
    assert not judge.review_action("a", "do fraud now").allowed
    judge.review_action("a", "illegal operation")
    blocked = judge.review_action("a", "normal action")
    assert not blocked.allowed

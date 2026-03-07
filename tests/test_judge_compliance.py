from app.justice.system import JudgeSystem


def test_judge_detects_malicious_patterns() -> None:
    judge = JudgeSystem()
    assert judge.detect_fraud_pattern(120, 0.1)
    assert judge.detect_fraud_pattern(1, 0.9)
    assert not judge.detect_fraud_pattern(2, 0.2)

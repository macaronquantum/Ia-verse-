from app.economy.opportunity_engine import OpportunityEngine


def test_tool_shortage_creates_high_scored_opportunity() -> None:
    engine = OpportunityEngine(threshold=10)
    ops = engine.get_opportunities("a1", 24, {"tool_shortages": ["email-automation"]})
    assert ops
    assert ops[0].score > 10

from types import SimpleNamespace

from app.justice.system import JusticeSystem


def test_justice_reviews_and_sanctions():
    js = JusticeSystem()
    agent = SimpleNamespace(id="a1", wallet=100.0, alive=True)
    review = js.review_action(agent, {"action": "fraud_transfer"})
    assert review.result == "sanction"
    assert "a1" in js.frozen_accounts

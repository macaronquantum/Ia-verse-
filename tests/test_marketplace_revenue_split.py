from app.marketplace.engine import compute_revenue_split


def test_revenue_split() -> None:
    split = compute_revenue_split(100, platform_fee=0.1, affiliate_fee=0.05)
    assert split.creator == 85
    assert split.platform == 10

from app.agents.business_builder import BusinessBuilder


def test_virtual_sale_distribution() -> None:
    builder = BusinessBuilder()
    listing = builder.create_listing("tool1", "subscription")
    sale = builder.settle_sale(100)
    assert listing["status"] == "listed"
    assert sale.creator_share == 90

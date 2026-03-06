from app.integrations.alchemy_client import AlchemyClient


def test_alchemy_stub_response():
    response = AlchemyClient().get_token_price("SOL")
    assert response["symbol"] == "SOL"
    assert "price_usd" in response

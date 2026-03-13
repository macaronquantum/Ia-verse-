from app.humans.payment_system import CryptoPaymentSystem


def test_verify_payment_interprets_confirmed(monkeypatch):
    cps = CryptoPaymentSystem(api_key="k", api_url="https://x")

    def fake_request(method, path, payload=None):
        return {"data": {"timeline": [{"status": "NEW"}, {"status": "CONFIRMED"}]}}

    monkeypatch.setattr(cps, "_request", fake_request)
    assert cps.verify_payment("charge") is True

from app.integrations.robokassa_client import build_payment_url, get_robokassa_client


def test_build_payment_url_contains_merchant():
    url = build_payment_url(inv_id=42, amount_rub=165, description="Test")
    assert "MerchantLogin=demo" in url
    assert "InvId=42" in url
    assert "OutSum=165" in url
    assert "SignatureValue=" in url


def test_robokassa_client_singleton():
    assert get_robokassa_client() is get_robokassa_client()

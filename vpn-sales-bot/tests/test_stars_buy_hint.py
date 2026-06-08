from app.formatters import format_stars_buy_hint
from app.config import settings


def test_format_stars_buy_hint_uses_stars_buy_bot_url(monkeypatch):
    monkeypatch.setattr(settings, "stars_buy_bot_url", "https://t.me/StarsFreeRuBot")
    text = format_stars_buy_hint()
    assert "@StarsFreeRuBot" in text
    assert "nexussstarsbot" not in text.lower()

from types import SimpleNamespace

from app.bot.keyboards import daily_review_keyboard
from app.services.daily_review import DailyReviewContent, _item_title


def test_item_title_truncates_long_text() -> None:
    item = SimpleNamespace(
        title=None,
        url=None,
        transcription="x" * 100,
    )
    assert len(_item_title(item)) == 80
    assert _item_title(item).endswith("…")


def test_item_title_prefers_title() -> None:
    item = SimpleNamespace(
        title="How Stripe Built Its API",
        url="https://example.com",
        transcription=None,
    )
    assert _item_title(item) == "How Stripe Built Its API"


def test_daily_review_keyboard_spotlight_and_backlog() -> None:
    spotlight = SimpleNamespace(id=1)
    backlog = SimpleNamespace(id=2)
    content = DailyReviewContent(
        text="☀️ Утренний обзор",
        spotlight_item=spotlight,
        spotlight_label="Год назад",
        backlog_item=backlog,
        unread_count=47,
    )
    markup = daily_review_keyboard(content)
    assert markup is not None
    texts = [btn.text for row in markup.inline_keyboard for btn in row]
    assert "📚 Посмотреть из архива" in texts
    assert "📥 Открыть из очереди" in texts
    assert "Инбокс" in texts


def test_daily_review_keyboard_spotlight_only() -> None:
    spotlight = SimpleNamespace(id=5)
    content = DailyReviewContent(
        text="☀️",
        spotlight_item=spotlight,
        spotlight_label="Месяц назад",
        backlog_item=None,
        unread_count=0,
    )
    markup = daily_review_keyboard(content)
    assert markup is not None
    callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    assert "daily:show:5" in callbacks

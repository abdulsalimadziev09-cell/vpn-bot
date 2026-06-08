from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.services.reminders import (
    ReminderParseError,
    format_remind_at,
    has_reminder_keyword,
    parse_remind_at,
    parse_reminder_intent,
)

MOSCOW = ZoneInfo("Europe/Moscow")


def test_parse_remind_at_hours() -> None:
    base = datetime(2026, 6, 5, 12, 0, tzinfo=MOSCOW)
    result = parse_remind_at("2h", now=base)
    assert result == datetime(2026, 6, 5, 14, 0, tzinfo=MOSCOW)


def test_parse_remind_at_days_ru() -> None:
    base = datetime(2026, 6, 5, 12, 0, tzinfo=MOSCOW)
    result = parse_remind_at("3д", now=base)
    assert result == datetime(2026, 6, 8, 12, 0, tzinfo=MOSCOW)


def test_parse_remind_at_weeks() -> None:
    base = datetime(2026, 6, 5, 12, 0, tzinfo=MOSCOW)
    result = parse_remind_at("1w", now=base)
    assert result == datetime(2026, 6, 12, 12, 0, tzinfo=MOSCOW)


def test_parse_remind_at_tomorrow_default_time() -> None:
    base = datetime(2026, 6, 5, 22, 0, tzinfo=MOSCOW)
    result = parse_remind_at("завтра", now=base)
    assert result == datetime(2026, 6, 6, 10, 0, tzinfo=MOSCOW)


def test_parse_remind_at_tomorrow_with_time() -> None:
    base = datetime(2026, 6, 5, 8, 0, tzinfo=MOSCOW)
    result = parse_remind_at("tomorrow 15:30", now=base)
    assert result == datetime(2026, 6, 6, 15, 30, tzinfo=MOSCOW)


def test_parse_remind_at_empty_raises() -> None:
    with pytest.raises(ReminderParseError):
        parse_remind_at("   ")


def test_parse_remind_at_unknown_raises() -> None:
    with pytest.raises(ReminderParseError):
        parse_remind_at("soon")


def test_format_remind_at_moscow() -> None:
    dt = datetime(2026, 6, 5, 9, 5, tzinfo=MOSCOW)
    assert format_remind_at(dt) == "05.06.2026 09:05"


def test_has_reminder_keyword_ru() -> None:
    assert has_reminder_keyword("напомни через 2 дня")
    assert has_reminder_keyword("Remind me tomorrow")
    assert not has_reminder_keyword("просто заметка")


def test_parse_reminder_intent_text_with_link() -> None:
    base = datetime(2026, 6, 5, 12, 0, tzinfo=MOSCOW)
    intent = parse_reminder_intent(
        "https://example.com напомни через 2 дня",
        now=base,
    )
    assert intent is not None
    assert intent.cleaned_text == "https://example.com"
    assert intent.remind_at == datetime(2026, 6, 7, 12, 0, tzinfo=MOSCOW)


def test_parse_reminder_intent_voice_style() -> None:
    base = datetime(2026, 6, 5, 8, 0, tzinfo=MOSCOW)
    intent = parse_reminder_intent(
        "напомни завтра посмотреть это видео",
        now=base,
    )
    assert intent is not None
    assert intent.cleaned_text == "посмотреть это видео"
    assert intent.remind_at == datetime(2026, 6, 6, 10, 0, tzinfo=MOSCOW)


def test_parse_reminder_intent_tomorrow() -> None:
    base = datetime(2026, 6, 5, 12, 0, tzinfo=MOSCOW)
    intent = parse_reminder_intent("напомни завтра", now=base)
    assert intent is not None
    assert intent.remind_at == datetime(2026, 6, 6, 10, 0, tzinfo=MOSCOW)


def test_parse_reminder_intent_keyword_only_returns_none() -> None:
    assert parse_reminder_intent("напомни про это") is None


def test_parse_reminder_intent_no_keyword() -> None:
    assert parse_reminder_intent("через 2 дня купить молоко") is None


def test_parse_remind_at_next_week() -> None:
    base = datetime(2026, 6, 5, 12, 0, tzinfo=MOSCOW)
    result = parse_remind_at("next week", now=base)
    assert result == datetime(2026, 6, 12, 12, 0, tzinfo=MOSCOW)


def test_parse_remind_at_in_3_days() -> None:
    base = datetime(2026, 6, 5, 12, 0, tzinfo=MOSCOW)
    result = parse_remind_at("in 3 days", now=base)
    assert result == datetime(2026, 6, 8, 12, 0, tzinfo=MOSCOW)

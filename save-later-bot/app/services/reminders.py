import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from zoneinfo import ZoneInfo

DURATION_RE = re.compile(
    r"^(\d+)\s*(h|ч|d|д|w|н)$",
    re.IGNORECASE,
)
TOMORROW_RE = re.compile(
    r"^tomorrow(?:\s+(\d{1,2})(?::(\d{2}))?)?$|^завтра(?:\s+в\s+(\d{1,2})(?::(\d{2}))?)?$",
    re.IGNORECASE,
)
REMINDER_KEYWORD_RE = re.compile(
    r"\b(?:напомни(?:те)?|remind(?:\s+me)?)\b",
    re.IGNORECASE | re.UNICODE,
)
NATURAL_TIME_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"через\s+(\d+)\s*(?:час|часа|часов|h)\b",
            re.IGNORECASE | re.UNICODE,
        ),
        "hours",
    ),
    (
        re.compile(
            r"через\s+(\d+)\s*(?:день|дня|дней|д)\b",
            re.IGNORECASE | re.UNICODE,
        ),
        "days",
    ),
    (
        re.compile(
            r"через\s+(\d+)\s*(?:неделю|недели|недель|н)\b",
            re.IGNORECASE | re.UNICODE,
        ),
        "weeks",
    ),
    (re.compile(r"\bчерез\s+час\b", re.IGNORECASE | re.UNICODE), "1hour"),
    (re.compile(r"\bчерез\s+день\b", re.IGNORECASE | re.UNICODE), "1day"),
    (re.compile(r"\bпослезавтра\b", re.IGNORECASE | re.UNICODE), "2days"),
    (
        re.compile(
            r"\bзавтра(?:\s+в\s+(\d{1,2})(?::(\d{2}))?)?\b",
            re.IGNORECASE | re.UNICODE,
        ),
        "tomorrow",
    ),
    (
        re.compile(r"\b(\d+)\s*(h|ч|d|д|w|н)\b", re.IGNORECASE | re.UNICODE),
        "compact",
    ),
    (re.compile(r"\bnext\s+week\b", re.IGNORECASE), "1week"),
    (re.compile(r"\bследующ(?:ую|ей)\s+недел", re.IGNORECASE | re.UNICODE), "1week"),
    (re.compile(r"\bin\s+(\d+)\s+days?\b", re.IGNORECASE), "days_en"),
]

DEFAULT_TZ = ZoneInfo("Europe/Moscow")


class ReminderParseError(ValueError):
    pass


@dataclass
class ReminderIntent:
    remind_at: datetime
    cleaned_text: str
    time_phrase: str


def parse_remind_at(expression: str, now: datetime | None = None) -> datetime:
    expr = expression.strip().lower()
    if not expr:
        raise ReminderParseError("Пустое выражение")

    base = now or datetime.now(DEFAULT_TZ)
    if base.tzinfo is None:
        base = base.replace(tzinfo=DEFAULT_TZ)

    duration_match = DURATION_RE.match(expr)
    if expr in ("next week", "следующую неделю", "на следующей неделе"):
        return base + timedelta(weeks=1)
    if expr in ("in 3 days", "через 3 дня", "через три дня"):
        return base + timedelta(days=3)

    duration_match = DURATION_RE.match(expr)
    if duration_match:
        amount = int(duration_match.group(1))
        unit = duration_match.group(2).lower()
        if unit in ("h", "ч"):
            return base + timedelta(hours=amount)
        if unit in ("d", "д"):
            return base + timedelta(days=amount)
        if unit in ("w", "н"):
            return base + timedelta(weeks=amount)

    tomorrow_match = TOMORROW_RE.match(expr)
    if tomorrow_match:
        hour = int(tomorrow_match.group(1) or tomorrow_match.group(3) or 10)
        minute = int(tomorrow_match.group(2) or tomorrow_match.group(4) or 0)
        target = (base + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= base:
            target += timedelta(days=1)
        return target

    raise ReminderParseError(
        f"Не понял «{expression}». Примеры: 1h, 2d, 1w, завтра, tomorrow 10:00"
    )


def format_remind_at(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(DEFAULT_TZ)
    return local.strftime("%d.%m.%Y %H:%M")


def has_reminder_keyword(text: str | None) -> bool:
    if not text:
        return False
    return REMINDER_KEYWORD_RE.search(text) is not None


def _apply_natural_time_match(
    match: re.Match[str],
    kind: str,
    base: datetime,
) -> datetime | None:
    if kind == "hours":
        return base + timedelta(hours=int(match.group(1)))
    if kind == "days":
        return base + timedelta(days=int(match.group(1)))
    if kind == "weeks":
        return base + timedelta(weeks=int(match.group(1)))
    if kind == "1hour":
        return base + timedelta(hours=1)
    if kind == "1day":
        return base + timedelta(days=1)
    if kind == "2days":
        return base + timedelta(days=2)
    if kind == "tomorrow":
        hour = int(match.group(1) or 10)
        minute = int(match.group(2) or 0)
        target = (base + timedelta(days=1)).replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
        )
        if target <= base:
            target += timedelta(days=1)
        return target
    if kind == "compact":
        amount = int(match.group(1))
        unit = match.group(2).lower()
        if unit in ("h", "ч"):
            return base + timedelta(hours=amount)
        if unit in ("d", "д"):
            return base + timedelta(days=amount)
        if unit in ("w", "н"):
            return base + timedelta(weeks=amount)
    if kind == "1week":
        return base + timedelta(weeks=1)
    if kind == "days_en":
        return base + timedelta(days=int(match.group(1)))
    return None


def _match_time_in_text(text: str, base: datetime) -> tuple[datetime, re.Match[str]] | None:
    for pattern, kind in NATURAL_TIME_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        remind_at = _apply_natural_time_match(match, kind, base)
        if remind_at is not None:
            return remind_at, match
    return None


def _find_time_in_text(
    text: str,
    keyword_match: re.Match[str],
    base: datetime,
) -> tuple[datetime, int, int, str] | None:
    segments = (
        (keyword_match.end(), text[keyword_match.end() :]),
        (0, text[: keyword_match.start()]),
        (0, text),
    )
    for offset, segment in segments:
        result = _match_time_in_text(segment, base)
        if not result:
            continue
        remind_at, match = result
        start = offset + match.start()
        end = offset + match.end()
        return remind_at, start, end, match.group(0)
    return None


def _clean_reminder_text(
    text: str,
    keyword_span: tuple[int, int],
    time_span: tuple[int, int],
) -> str:
    spans = sorted([keyword_span, time_span])
    parts: list[str] = []
    cursor = 0
    for start, end in spans:
        parts.append(text[cursor:start])
        cursor = max(cursor, end)
    parts.append(text[cursor:])
    cleaned = " ".join(" ".join(parts).split())
    cleaned = re.sub(r"^[,\-—:]+|[,\-—:]+$", "", cleaned).strip()
    return cleaned


def parse_reminder_intent(text: str | None, now: datetime | None = None) -> ReminderIntent | None:
    if not text or not has_reminder_keyword(text):
        return None

    keyword_match = REMINDER_KEYWORD_RE.search(text)
    if not keyword_match:
        return None

    base = now or datetime.now(DEFAULT_TZ)
    if base.tzinfo is None:
        base = base.replace(tzinfo=DEFAULT_TZ)

    time_result = _find_time_in_text(text, keyword_match, base)
    if not time_result:
        return None

    remind_at, time_start, time_end, time_phrase = time_result
    cleaned = _clean_reminder_text(text, keyword_match.span(), (time_start, time_end))

    return ReminderIntent(
        remind_at=remind_at,
        cleaned_text=cleaned,
        time_phrase=time_phrase,
    )

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from aiogram.types import Message

from app.db.models import ItemType

URL_RE = re.compile(r"https?://[^\s<>\"']+")
HASHTAG_RE = re.compile(r"#([\w\u0400-\u04FF]+)", re.UNICODE)


@dataclass
class SavePayload:
    item_type: str
    title: str | None = None
    body: str | None = None
    url: str | None = None
    source_chat: str | None = None
    telegram_message_id: int | None = None
    transcription: str | None = None
    hashtags: list[str] = field(default_factory=list)


def extract_hashtags(text: str | None) -> list[str]:
    if not text:
        return []
    return [m.group(1).lower() for m in HASHTAG_RE.finditer(text)]


def _first_url(text: str | None) -> str | None:
    if not text:
        return None
    match = URL_RE.search(text)
    return match.group(0).rstrip(".,)") if match else None


def _title_from_text(text: str | None, url: str | None = None) -> str | None:
    if text:
        line = text.strip().splitlines()[0].strip()
        if line:
            return line[:512]
    if url:
        parsed = urlparse(url)
        return parsed.netloc or url[:512]
    return None


def _forward_source(message: Message) -> str | None:
    if message.forward_from_chat:
        title = message.forward_from_chat.title or message.forward_from_chat.username
        return title
    if message.forward_from:
        parts = [message.forward_from.first_name or "", message.forward_from.last_name or ""]
        name = " ".join(p for p in parts if p).strip()
        return name or message.forward_from.username
    return None


def extract_from_message(message: Message) -> SavePayload | None:
    if message.voice or message.audio:
        return None

    text = message.text or message.caption
    url = _first_url(text)

    if message.forward_date or message.forward_origin:
        hashtags = extract_hashtags(text)
        return SavePayload(
            item_type=ItemType.FORWARD,
            title=_title_from_text(text, url),
            body=text,
            url=url,
            source_chat=_forward_source(message),
            telegram_message_id=message.message_id,
            hashtags=hashtags,
        )

    if url and (not text or text.strip() == url):
        parsed = urlparse(url)
        domain = parsed.netloc.removeprefix("www.")
        return SavePayload(
            item_type=ItemType.LINK,
            title=domain,
            body=None,
            url=url,
            telegram_message_id=message.message_id,
            hashtags=extract_hashtags(text),
        )

    if text:
        hashtags = extract_hashtags(text)
        item_type = ItemType.LINK if url else ItemType.TEXT
        return SavePayload(
            item_type=item_type,
            title=_title_from_text(text, url),
            body=text,
            url=url,
            telegram_message_id=message.message_id,
            hashtags=hashtags,
        )

    if message.photo or message.video or message.document:
        return SavePayload(
            item_type=ItemType.FORWARD,
            title="Медиа без подписи",
            body=None,
            source_chat=_forward_source(message),
            telegram_message_id=message.message_id,
        )

    return None


def build_search_text(
    title: str | None,
    body: str | None,
    url: str | None,
    transcription: str | None,
    tags: list[str],
    summary: str | None = None,
) -> str:
    parts = [title, body, url, transcription, summary, " ".join(tags)]
    return " ".join(p for p in parts if p)

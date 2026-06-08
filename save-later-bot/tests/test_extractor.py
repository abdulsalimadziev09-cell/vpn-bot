from unittest.mock import MagicMock

import pytest

from app.db.models import ItemType
from app.services.extractor import (
    SavePayload,
    build_search_text,
    extract_from_message,
    extract_hashtags,
)


def test_extract_hashtags_basic() -> None:
    assert extract_hashtags("Идея #работа и #Python") == ["работа", "python"]


def test_extract_hashtags_empty() -> None:
    assert extract_hashtags("") == []
    assert extract_hashtags(None) == []


def test_build_search_text_joins_parts() -> None:
    text = build_search_text(
        title="Заголовок",
        body="Текст заметки",
        url="https://example.com",
        transcription="расшифровка",
        tags=["работа", "идеи"],
    )
    assert "Заголовок" in text
    assert "example.com" in text
    assert "работа идеи" in text


def test_build_search_text_skips_empty() -> None:
    assert build_search_text(None, None, None, None, []) == ""


def _make_message(**kwargs):
    message = MagicMock()
    message.text = kwargs.get("text")
    message.caption = kwargs.get("caption")
    message.message_id = kwargs.get("message_id", 1)
    message.voice = kwargs.get("voice")
    message.audio = kwargs.get("audio")
    message.photo = kwargs.get("photo")
    message.video = kwargs.get("video")
    message.document = kwargs.get("document")
    message.forward_date = kwargs.get("forward_date")
    message.forward_origin = kwargs.get("forward_origin")
    message.forward_from_chat = kwargs.get("forward_from_chat")
    message.forward_from = kwargs.get("forward_from")
    return message


def test_extract_from_message_link_only() -> None:
    message = _make_message(text="https://github.com/org/repo")
    payload = extract_from_message(message)

    assert payload is not None
    assert payload.item_type == ItemType.LINK
    assert payload.url == "https://github.com/org/repo"
    assert payload.title == "github.com"


def test_extract_from_message_text_with_hashtags() -> None:
    message = _make_message(text="Заметка про Istio #istio #работа")
    payload = extract_from_message(message)

    assert payload is not None
    assert payload.item_type == ItemType.TEXT
    assert payload.title == "Заметка про Istio #istio #работа"
    assert payload.hashtags == ["istio", "работа"]


def test_extract_from_message_forward() -> None:
    forward_chat = MagicMock()
    forward_chat.title = "Tech Channel"
    forward_chat.username = None

    message = _make_message(
        text="Пост из канала",
        forward_date=True,
        forward_from_chat=forward_chat,
    )
    payload = extract_from_message(message)

    assert payload is not None
    assert payload.item_type == ItemType.FORWARD
    assert payload.source_chat == "Tech Channel"


def test_extract_from_message_voice_returns_none() -> None:
    message = _make_message(voice=MagicMock())
    assert extract_from_message(message) is None


def test_save_payload_defaults() -> None:
    payload = SavePayload(item_type=ItemType.TEXT)
    assert payload.hashtags == []
    assert payload.url is None

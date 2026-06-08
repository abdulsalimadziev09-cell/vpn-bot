import logging
import tempfile
from datetime import datetime
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.types import Message

from app.bot.formatters import format_item_card
from app.bot.keyboards import item_card_keyboard
from app.config import settings
from app.db.models import ItemType
from app.repositories.items import get_or_create_user
from app.services.extractor import SavePayload, extract_from_message, extract_hashtags
from app.services.reminders import format_remind_at, has_reminder_keyword, parse_reminder_intent
from app.services.save_orchestrator import SaveOrchestrator
from app.services.subscription import item_limit_for_user
from app.services.tag_suggester import merge_tags, suggest_from_title, suggest_from_url
from app.services.transcription import TranscriptionError, TranscriptionService

logger = logging.getLogger(__name__)

router = Router()
_transcription = TranscriptionService()
_save_orchestrator = SaveOrchestrator()


def _apply_reminder_intent(
    payload: SavePayload,
    source_text: str | None,
) -> tuple[SavePayload, datetime | None, bool]:
    if not source_text:
        return payload, None, False

    intent = parse_reminder_intent(source_text)
    if intent:
        if intent.cleaned_text:
            payload.body = intent.cleaned_text
            first_line = intent.cleaned_text.strip().splitlines()[0].strip()
            if first_line and first_line != payload.url:
                payload.title = first_line[:512]
            elif not payload.title:
                payload.title = intent.cleaned_text[:512]
        if payload.transcription and intent.cleaned_text:
            payload.transcription = intent.cleaned_text
        return payload, intent.remind_at, False

    return payload, None, has_reminder_keyword(source_text)


async def _save_and_reply(
    message: Message,
    payload: SavePayload,
    suggested_tags: list[str],
    remind_at: datetime | None = None,
    reminder_unparsed: bool = False,
) -> None:
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        limit = item_limit_for_user(user)
        result = await _save_orchestrator.save(
            session,
            user,
            payload,
            suggested_tags,
            remind_at=remind_at,
        )
        await session.commit()

    if result.limit_reached:
        await message.answer(
            f"Лимит {limit} сохранений. "
            "Удали старые (/delete <id>) или /buy для Pro."
        )
        return

    item = result.item
    if result.duplicate:
        await message.answer(
            format_item_card(item, header="Уже сохранено"),
            reply_markup=item_card_keyboard(item),
        )
        return

    reply = format_item_card(
        item,
        folder_name=result.folder_name,
        collection_name=result.collection_name,
    )
    if remind_at is not None:
        reply += f"\n\n⏰ Напомню {format_remind_at(remind_at)}"
    elif reminder_unparsed:
        reply += (
            "\n\n⚠️ Написал «напомни», но не понял когда. "
            "Примеры: «напомни через 2 дня», «напомни завтра»."
        )

    await message.answer(reply, reply_markup=item_card_keyboard(item))


async def _transcribe_voice(message: Message, bot: Bot, voice) -> str | None:
    if not _transcription.enabled:
        return None
    if voice.duration > settings.max_voice_duration_seconds:
        return None

    status = await message.answer("Слушаю…")
    text: str | None = None
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / f"{voice.file_id}.ogg"
            await bot.download(voice, destination=file_path)
            text = await _transcription.transcribe_file(file_path)
    except TranscriptionError as exc:
        logger.warning("Transcription failed: %s", exc)
    finally:
        await status.delete()
    return text


@router.message(F.voice, StateFilter(None))
async def handle_voice(message: Message, bot: Bot) -> None:
    voice = message.voice
    hashtags = extract_hashtags(message.caption)
    text = await _transcribe_voice(message, bot, voice)

    if text:
        title = text[:512]
        body = text
        transcription = text
    else:
        title = "Голосовое"
        body = None
        transcription = None

    source_text = text or message.caption
    payload = SavePayload(
        item_type=ItemType.VOICE,
        title=title,
        body=body,
        transcription=transcription,
        telegram_message_id=message.message_id,
        hashtags=hashtags,
    )
    payload, remind_at, reminder_unparsed = _apply_reminder_intent(payload, source_text)
    suggested = merge_tags(suggest_from_title(payload.body or payload.transcription), hashtags)
    await _save_and_reply(
        message,
        payload,
        suggested,
        remind_at=remind_at,
        reminder_unparsed=reminder_unparsed,
    )


@router.message(F.text | F.caption | F.photo | F.video | F.document, StateFilter(None))
async def handle_content(message: Message) -> None:
    if message.text and message.text.startswith("/"):
        return

    payload = extract_from_message(message)
    if not payload:
        return

    source_text = message.text or message.caption or payload.body
    payload, remind_at, reminder_unparsed = _apply_reminder_intent(payload, source_text)
    suggested = merge_tags(
        suggest_from_url(payload.url),
        suggest_from_title(payload.title),
    )
    await _save_and_reply(
        message,
        payload,
        suggested,
        remind_at=remind_at,
        reminder_unparsed=reminder_unparsed,
    )

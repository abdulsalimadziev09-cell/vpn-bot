from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.formatters import format_item_card
from app.bot.keyboards import daily_review_keyboard, item_card_keyboard
from app.db.session import async_session_factory
from app.repositories.analytics import track_event
from app.repositories.items import get_item_accessible, get_or_create_user
from app.services.daily_review import build_daily_review

router = Router()


async def _send_daily_review(message: Message, user_id: int) -> None:
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=user_id,
            username=getattr(message.from_user, "username", None),
        )
        if not user.daily_review_enabled:
            await message.answer("Утренний обзор отключён. Включить: /daily on")
            return

        content = await build_daily_review(session, user.telegram_id)
        if not content:
            await message.answer(
                "Пока нечего показать в обзоре.\n"
                "Сохрани пару материалов — завтра пришлю подборку."
            )
            return

        markup = daily_review_keyboard(content)
        await message.answer(content.text, reply_markup=markup)

        payload: dict = {"unread": content.unread_count}
        if content.spotlight_item:
            payload["spotlight_item_id"] = content.spotlight_item.id
            await track_event(
                session,
                user.telegram_id,
                "daily_review_spotlight",
                {"item_id": content.spotlight_item.id, "label": content.spotlight_label},
            )
        await track_event(session, user.telegram_id, "daily_review_sent", payload)
        await session.commit()


@router.message(Command("daily"))
async def cmd_daily(message: Message) -> None:
    parts = (message.text or "").strip().split()
    if len(parts) > 1 and parts[1].lower() in ("on", "off"):
        async with async_session_factory() as session:
            user = await get_or_create_user(
                session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )
            user.daily_review_enabled = parts[1].lower() == "on"
            await session.commit()
        state = "включён" if parts[1].lower() == "on" else "отключён"
        await message.answer(f"Утренний обзор {state}.")
        return

    await _send_daily_review(message, message.from_user.id)


@router.callback_query(F.data == "daily")
async def cb_daily(callback: CallbackQuery) -> None:
    if callback.message:
        await _send_daily_review(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("daily:show:"))
async def cb_daily_show_item(callback: CallbackQuery) -> None:
    item_id = int(callback.data.split(":")[2])
    async with async_session_factory() as session:
        item = await get_item_accessible(session, callback.from_user.id, item_id)
        if item:
            await track_event(
                session,
                callback.from_user.id,
                "daily_review_opened",
                {"item_id": item_id},
            )
        await session.commit()

    if not item:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    if callback.message:
        await callback.message.answer(
            format_item_card(item, header="Из обзора"),
            reply_markup=item_card_keyboard(item),
        )
    await callback.answer()

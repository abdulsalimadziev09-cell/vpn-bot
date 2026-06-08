import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.formatters import format_item_card
from app.bot.keyboards import remind_keyboard, reminder_sent_keyboard
from app.db.session import async_session_factory
from app.repositories.items import create_reminder, get_item, get_or_create_user, mark_reminder_sent
from app.services.reminders import ReminderParseError, format_remind_at, parse_remind_at

logger = logging.getLogger(__name__)

router = Router()


async def send_due_reminder(bot: Bot, reminder, session: AsyncSession) -> None:
    item = reminder.item
    text = format_item_card(item, header="Напоминание")
    await bot.send_message(
        chat_id=reminder.user_id,
        text=text,
        reply_markup=reminder_sent_keyboard(item),
    )
    await mark_reminder_sent(session, reminder)


async def _create_reminder(message: Message, item_id: int, expression: str) -> None:
    try:
        remind_at = parse_remind_at(expression)
    except ReminderParseError as exc:
        await message.answer(str(exc))
        return

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        item = await get_item(session, user.telegram_id, item_id)
        if not item:
            await message.answer(f"Запись #{item_id} не найдена.")
            return

        await create_reminder(session, user.telegram_id, item_id, remind_at)
        await session.commit()

    await message.answer(
        f"Напомню {format_remind_at(remind_at)} про #{item_id} · "
        f"{item.title or item.url or 'запись'}"
    )


@router.message(Command("remind"))
async def cmd_remind(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "Использование: /remind <id> <когда>\n"
            "Примеры: /remind 5 2d, /remind 12 завтра, /remind 3 1h"
        )
        return

    raw_id = parts[1].strip().lstrip("#")
    if not raw_id.isdigit():
        await message.answer("ID должен быть числом.")
        return

    await _create_reminder(message, int(raw_id), parts[2])


@router.callback_query(F.data.startswith("remind_menu:"))
async def cb_remind_menu(callback: CallbackQuery) -> None:
    item_id = int(callback.data.split(":", maxsplit=1)[1])

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )
        item = await get_item(session, user.telegram_id, item_id)

    if not item:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    await callback.message.answer(
        f"Когда напомнить про #{item_id}?",
        reply_markup=remind_keyboard(item_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remind:"))
async def cb_remind(callback: CallbackQuery) -> None:
    _, item_id_raw, expression = callback.data.split(":", maxsplit=2)
    item_id = int(item_id_raw)

    try:
        remind_at = parse_remind_at(expression)
    except ReminderParseError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )
        item = await get_item(session, user.telegram_id, item_id)
        if not item:
            await callback.answer("Запись не найдена", show_alert=True)
            return

        await create_reminder(session, user.telegram_id, item_id, remind_at)
        await session.commit()

    await callback.message.answer(
        f"Напомню {format_remind_at(remind_at)} про #{item_id} · "
        f"{item.title or item.url or 'запись'}"
    )
    await callback.answer("Напоминание создано")

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.formatters import format_item_card, format_item_list
from app.bot.keyboards import item_card_keyboard
from app.db.models import ItemStatus
from app.db.session import async_session_factory
from app.repositories.analytics import track_event
from app.repositories.items import get_or_create_user, list_items, update_item_status

router = Router()


async def _set_status(message: Message, item_id: int, status: str, label: str) -> None:
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        item = await update_item_status(session, user.telegram_id, item_id, status)
        if not item:
            await message.answer(f"Запись #{item_id} не найдена.")
            return
        await track_event(session, user.telegram_id, f"item_{status}", {"item_id": item_id})
        await session.commit()

    await message.answer(
        format_item_card(item, header=label),
        reply_markup=item_card_keyboard(item),
    )


@router.message(Command("inbox"))
async def cmd_inbox(message: Message) -> None:
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        items = await list_items(session, user.telegram_id, limit=10, status=ItemStatus.INBOX)
        await track_event(session, user.telegram_id, "inbox_viewed", {"count": len(items)})
        await session.commit()

    header = "Инбокс (разобрать)"
    if not items:
        await message.answer("Инбокс пуст 🎉\nВсе сохранения разобраны.")
        return
    await message.answer(header + "\n\n" + format_item_list(items))


@router.message(Command("done"))
async def cmd_done(message: Message) -> None:
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /done <id>")
        return
    await _set_status(message, int(parts[1]), ItemStatus.DONE, "Готово")


@router.message(Command("archive"))
async def cmd_archive(message: Message) -> None:
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /archive <id>")
        return
    await _set_status(message, int(parts[1]), ItemStatus.ARCHIVED, "В архиве")


@router.callback_query(F.data.startswith("status:"))
async def cb_status(callback: CallbackQuery) -> None:
    _, item_id_raw, status = callback.data.split(":", maxsplit=2)
    labels = {
        ItemStatus.READING: "Читаю",
        ItemStatus.DONE: "Готово",
        ItemStatus.ARCHIVED: "В архиве",
        ItemStatus.INBOX: "В инбокс",
    }
    if callback.message:
        await _set_status(callback.message, int(item_id_raw), status, labels.get(status, "Обновлено"))
    await callback.answer()

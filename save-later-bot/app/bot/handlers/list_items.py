from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.formatters import format_item_card, format_item_list, format_tags_list
from app.bot.keyboards import item_card_keyboard
from app.db.session import async_session_factory
from app.repositories.items import get_item, get_or_create_user, list_items, list_tags_with_counts

router = Router()


async def _reply_item(message: Message, item_id: int) -> None:
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

    await message.answer(
        format_item_card(item, header="Запись"),
        reply_markup=item_card_keyboard(item),
    )


@router.message(Command("list"))
async def cmd_list(message: Message) -> None:
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        items = await list_items(session, user.telegram_id)

    await message.answer(format_item_list(items))


@router.message(Command("delete"))
async def cmd_delete(message: Message) -> None:
    from app.repositories.analytics import track_event
    from app.repositories.items import delete_item

    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Использование: /delete <id>")
        return
    item_id = int(parts[1].lstrip("#"))
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        deleted = await delete_item(session, user.telegram_id, item_id)
        if deleted:
            await track_event(session, user.telegram_id, "item_deleted", {"item_id": item_id})
        await session.commit()
    if not deleted:
        await message.answer(f"Запись #{item_id} не найдена.")
        return
    await message.answer(f"Запись #{item_id} удалена.")


@router.callback_query(F.data == "inbox")
async def cb_inbox(callback: CallbackQuery) -> None:
    from app.db.models import ItemStatus
    from app.repositories.analytics import track_event

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )
        items = await list_items(session, user.telegram_id, limit=10, status=ItemStatus.INBOX)
        await track_event(session, user.telegram_id, "inbox_viewed", {"count": len(items)})
        await session.commit()

    text = "Инбокс пуст 🎉" if not items else "Инбокс (разобрать)\n\n" + format_item_list(items)
    if callback.message:
        await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data == "list")
async def cb_list(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )
        items = await list_items(session, user.telegram_id)

    await callback.message.answer(format_item_list(items))
    await callback.answer()


@router.message(Command("tags"))
async def cmd_tags(message: Message) -> None:
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        tag_counts = await list_tags_with_counts(session, user.telegram_id)

    await message.answer(format_tags_list(tag_counts))


@router.callback_query(F.data == "tags")
async def cb_tags(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )
        tag_counts = await list_tags_with_counts(session, user.telegram_id)

    await callback.message.answer(format_tags_list(tag_counts))
    await callback.answer()


@router.message(Command("item"))
async def cmd_item(message: Message) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /item <id>\nПример: /item 42")
        return

    raw_id = parts[1].strip().lstrip("#")
    if not raw_id.isdigit():
        await message.answer("ID должен быть числом. Пример: /item 42")
        return

    await _reply_item(message, int(raw_id))


@router.callback_query(F.data.startswith("item:"))
async def cb_item(callback: CallbackQuery) -> None:
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

    text = format_item_card(item, header="Запись")
    markup = item_card_keyboard(item)

    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)

    await callback.answer()

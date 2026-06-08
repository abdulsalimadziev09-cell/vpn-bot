import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.formatters import format_item_card
from app.bot.keyboards import item_card_keyboard
from app.bot.states import AddTags
from app.db.session import async_session_factory
from app.repositories.items import attach_tags, get_item, get_or_create_user

router = Router()

TAG_INPUT_RE = re.compile(r"[\s,;]+")


def parse_tag_input(text: str) -> list[str]:
    raw = text.replace("#", " ")
    return [part.strip().lower() for part in TAG_INPUT_RE.split(raw) if part.strip()]


@router.callback_query(F.data.startswith("tag:"))
async def start_add_tags(callback: CallbackQuery, state: FSMContext) -> None:
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

    await state.set_state(AddTags.waiting_for_tags)
    await state.update_data(item_id=item_id)
    await callback.message.answer(
        f"Добавь теги к #{item_id} — через пробел или запятую (можно с #):\n"
        "Пример: работа идеи"
    )
    await callback.answer()


@router.message(AddTags.waiting_for_tags)
async def process_tags(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    item_id = data.get("item_id")
    if not item_id:
        await state.clear()
        await message.answer("Сессия сброшена. Нажми «+ Тег» снова.")
        return

    tag_names = parse_tag_input(message.text or "")
    if not tag_names:
        await message.answer("Не нашёл тегов. Попробуй ещё раз или /start.")
        return

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        item = await get_item(session, user.telegram_id, item_id)
        if not item:
            await state.clear()
            await message.answer("Запись не найдена.")
            return

        await attach_tags(session, item, tag_names)
        await session.commit()

    await state.clear()
    await message.answer(
        format_item_card(item, header="Теги обновлены"),
        reply_markup=item_card_keyboard(item),
    )

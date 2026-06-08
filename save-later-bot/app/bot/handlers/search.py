from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.formatters import format_item_card, format_search_results
from app.bot.keyboards import item_card_keyboard
from app.bot.states import Search
from app.db.session import async_session_factory
from app.repositories.analytics import track_event
from app.repositories.items import get_or_create_user
from app.services.embeddings import EmbeddingService
from app.services.search import search_items
from app.services.subscription import is_pro_active, refresh_user_plan

router = Router()
_embeddings = EmbeddingService()


async def _ask_query(target: Message) -> None:
    await target.answer("Что ищем? Напиши слово, фразу или #тег.")


async def _run_search(message: Message, query: str) -> None:
    query = query.strip()
    if not query:
        await message.answer("Пустой запрос. Напиши текст для поиска.")
        return

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        await refresh_user_plan(session, user)
        use_semantic = is_pro_active(user)
        items = await search_items(
            session,
            user.telegram_id,
            query,
            use_semantic=use_semantic,
            embedding_service=_embeddings,
        )
        await track_event(
            session,
            user.telegram_id,
            "search",
            {"query_len": len(query), "results": len(items), "semantic": use_semantic},
        )
        await session.commit()

    header = "Найдено (умный поиск)" if use_semantic else "Найдено"
    await message.answer(format_search_results(items, query, smart=use_semantic))

    for item in items[:3]:
        await message.answer(
            format_item_card(item, header=header),
            reply_markup=item_card_keyboard(item),
        )


@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext) -> None:
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) > 1 and parts[1].strip():
        await state.clear()
        await _run_search(message, parts[1])
        return

    await state.set_state(Search.waiting_for_query)
    await _ask_query(message)


@router.callback_query(F.data == "search")
async def cb_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Search.waiting_for_query)
    await _ask_query(callback.message)
    await callback.answer()


@router.message(Search.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _run_search(message, message.text or "")

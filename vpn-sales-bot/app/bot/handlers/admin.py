from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.config import settings
from app.db.session import async_session_factory
from app.formatters import format_order_admin
from app.repositories.orders import get_order_by_id, list_orders_by_status
from app.services.payment import approve_manual_order

router = Router()


class AdminApproveStates(StatesGroup):
    waiting_config = State()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("admin_orders"))
async def cmd_admin_orders(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return

    async with async_session_factory() as session:
        paid_orders = await list_orders_by_status(session, "paid")

    if not paid_orders:
        await message.answer("Нет заказов, ожидающих выдачи.")
        return

    chunks = [format_order_admin(order) for order in paid_orders[:20]]
    await message.answer("Заказы, ожидающие выдачи:\n\n" + "\n\n".join(chunks))


@router.message(Command("admin_approve"))
async def cmd_admin_approve(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Использование: /admin_approve <order_id>")
        return

    try:
        order_id = int(parts[1])
    except ValueError:
        await message.answer("order_id должен быть числом.")
        return

    async with async_session_factory() as session:
        order = await get_order_by_id(session, order_id)

    if not order:
        await message.answer("Заказ не найден.")
        return
    if order.status != "paid":
        await message.answer(f"Заказ в статусе {order.status}, ожидается paid.")
        return

    await state.set_state(AdminApproveStates.waiting_config)
    await state.update_data(order_id=order_id)
    await message.answer(
        f"Заказ #{order_id} найден.\n"
        "Отправьте содержимое .conf одним сообщением (текстом или файлом)."
    )


@router.message(AdminApproveStates.waiting_config, F.document)
async def admin_approve_document(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await state.clear()
        return

    file = await message.bot.get_file(message.document.file_id)
    downloaded = await message.bot.download_file(file.file_path)
    config_text = downloaded.read().decode("utf-8")
    await _finalize_approve(message, state, order_id, config_text)


@router.message(AdminApproveStates.waiting_config, F.text)
async def admin_approve_text(message: Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await state.clear()
        return

    if message.text.startswith("/"):
        await message.answer("Ожидается конфиг, не команда. Отправьте .conf содержимое.")
        return

    await _finalize_approve(message, state, order_id, message.text)


async def _finalize_approve(
    message: Message,
    state: FSMContext,
    order_id: int,
    config_text: str,
) -> None:
    async with async_session_factory() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await message.answer("Заказ не найден.")
            await state.clear()
            return

        await approve_manual_order(session, message.bot, order, config_text)

    await state.clear()
    await message.answer(f"Заказ #{order_id} выдан пользователю.")

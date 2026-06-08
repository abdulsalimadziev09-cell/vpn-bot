from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import main_menu_keyboard
from app.config import settings
from app.db.models import OrderStatus
from app.db.session import async_session_factory
from app.formatters import format_admin_order, format_order_summary
from app.repositories.orders import get_order_by_id, list_orders_by_status
from app.services.fulfillment import admin_mark_fulfilled

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.callback_query(lambda c: c.data == "orders:list")
async def orders_list(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        from app.repositories.orders import list_orders_for_buyer

        buyer_orders = await list_orders_for_buyer(session, callback.from_user.id)

    if not buyer_orders:
        await callback.message.edit_text(
            "У вас пока нет заказов.",
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()
        return

    lines = [format_order_summary(o) + f"\nСтатус: {o.status}\n" for o in buyer_orders[:10]]
    await callback.message.edit_text(
        "📦 Ваши заказы:\n\n" + "\n".join(lines),
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.message(Command("admin"))
async def admin_help(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Админ-команды:\n"
        "/admin_orders — оплаченные, ждут выдачи\n"
        "/admin_fulfill <id> — отметить выданным"
    )


@router.message(Command("admin_orders"))
async def admin_orders(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    async with async_session_factory() as session:
        paid = await list_orders_by_status(session, OrderStatus.PAID)
        failed = await list_orders_by_status(session, OrderStatus.FAILED, limit=10)

    if not paid and not failed:
        await message.answer("Нет заказов, ожидающих выдачи.")
        return

    lines = [format_admin_order(o) for o in paid + failed]
    await message.answer("Заказы на выдачу:\n\n" + "\n\n".join(lines))


@router.message(Command("admin_fulfill"))
async def admin_fulfill(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /admin_fulfill <order_id>")
        return

    order_id = int(parts[1])
    async with async_session_factory() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await message.answer("Заказ не найден")
            return
        if order.status not in (OrderStatus.PAID, OrderStatus.FAILED):
            await message.answer(f"Заказ в статусе {order.status}, выдача невозможна")
            return
        await admin_mark_fulfilled(session, message.bot, order)

    await message.answer(f"Заказ #{order_id} отмечен как выданный.")

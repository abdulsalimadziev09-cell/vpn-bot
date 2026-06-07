from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.handlers.payments import send_stars_invoice
from app.bot.keyboards import plans_keyboard
from app.config import settings
from app.db.session import async_session_factory
from app.formatters import format_plan_line
from app.repositories.plans import get_plan_by_id, list_active_plans
from app.services.payment import create_pending_order

router = Router()


@router.callback_query(F.data == "menu:plans")
async def show_plans(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        plans = await list_active_plans(session)

    if not plans:
        await callback.answer("Тарифы временно недоступны.", show_alert=True)
        return

    lines = "\n".join(f"• {format_plan_line(plan)}" for plan in plans)
    await callback.message.edit_text(
        f"Выберите тариф (оплата Telegram Stars ⭐):\n\n{lines}",
        reply_markup=plans_keyboard(plans),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("plan:"))
async def select_plan(callback: CallbackQuery) -> None:
    plan_id = int(callback.data.split(":", 1)[1])
    async with async_session_factory() as session:
        plan = await get_plan_by_id(session, plan_id)
        if not plan:
            await callback.answer("Тариф не найден.", show_alert=True)
            return

        if not settings.payments_enabled:
            await callback.answer("Оплата временно недоступна.", show_alert=True)
            return

        order = await create_pending_order(
            session,
            callback.from_user.id,
            callback.from_user.username,
            plan,
        )

    await callback.message.edit_text(
        f"Заказ #{order.id}: {plan.title} — {plan.stars_price} ⭐\n"
        "Счёт на оплату Stars отправлен ниже."
    )
    await send_stars_invoice(callback.message, order, plan)
    await callback.answer()

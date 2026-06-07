import json
import logging

from aiogram import F, Router
from aiogram.types import Message

from app.bot.handlers.payments import send_stars_invoice
from app.bot.handlers.trial import ERRORS as TRIAL_ERRORS
from app.bot.keyboards import back_to_menu_keyboard, my_subscription_keyboard
from app.config import settings
from app.db.session import async_session_factory
from app.formatters import format_referral_info, format_subscription_status, format_vpn_delivery_hint
from app.repositories.plans import get_plan_by_code
from app.repositories.referrals import count_invited, count_paid_referrals
from app.repositories.subscriptions import get_active_subscription
from app.repositories.users import get_user
from app.services.payment import create_pending_order
from app.services.trial import activate_trial

router = Router()
logger = logging.getLogger(__name__)


async def _reminders_enabled(session, telegram_id: int) -> bool:
    user = await get_user(session, telegram_id)
    return True if user is None else user.expiry_reminders_enabled


@router.message(F.web_app_data)
async def handle_web_app_data(message: Message) -> None:
    try:
        data = json.loads(message.web_app_data.data)
    except (TypeError, json.JSONDecodeError):
        logger.warning("Invalid mini app payload from user %s", message.from_user.id)
        return

    action = data.get("action")
    if action == "select_plan":
        await _handle_select_plan(message, data.get("plan_code"))
    elif action == "trial":
        await _handle_trial(message)
    elif action == "my_subscription":
        await _handle_my_subscription(message)
    elif action == "referral":
        await _handle_referral(message)


async def _handle_select_plan(message: Message, plan_code: str | None) -> None:
    if not plan_code:
        await message.answer("Не удалось определить тариф. Выберите снова в приложении.")
        return

    if not settings.payments_enabled:
        await message.answer("Оплата временно недоступна.")
        return

    async with async_session_factory() as session:
        plan = await get_plan_by_code(session, plan_code)
        if not plan or not plan.is_active:
            await message.answer("Тариф не найден.")
            return

        order = await create_pending_order(
            session,
            message.from_user.id,
            message.from_user.username,
            plan,
        )

    await message.answer(
        f"Заказ #{order.id}: {plan.title} — {plan.stars_price} ⭐\n"
        "Счёт на оплату Stars отправлен ниже."
    )
    await send_stars_invoice(message, order, plan)


async def _handle_trial(message: Message) -> None:
    async with async_session_factory() as session:
        result = await activate_trial(
            session,
            message.bot,
            message.from_user.id,
            message.from_user.username,
        )

    if not result.ok:
        await message.answer(TRIAL_ERRORS.get(result.error or "", "Ошибка."))
        return

    if settings.vpn_provisioner == "manual":
        text = (
            f"Пробный период на {settings.trial_days} дн. активирован.\n"
            "Конфиг будет выдан в ближайшее время — обычно в течение нескольких минут.\n\n"
            f"{format_vpn_delivery_hint()}"
        )
    else:
        text = (
            f"Пробный период на {settings.trial_days} дн. активирован.\n"
            "Конфиг отправлен выше.\n\n"
            f"{format_vpn_delivery_hint()}"
        )

    await message.answer(text, reply_markup=back_to_menu_keyboard())


async def _handle_my_subscription(message: Message) -> None:
    async with async_session_factory() as session:
        subscription = await get_active_subscription(session, message.from_user.id)
        reminders = await _reminders_enabled(session, message.from_user.id)

    text = format_subscription_status(subscription)
    await message.answer(text, reply_markup=my_subscription_keyboard(reminders))


async def _handle_referral(message: Message) -> None:
    bot_user = await message.bot.get_me()
    async with async_session_factory() as session:
        invited = await count_invited(session, message.from_user.id)
        paid = await count_paid_referrals(session, message.from_user.id)

    text = format_referral_info(
        bot_user.username or "bot",
        message.from_user.id,
        invited,
        paid,
    )
    await message.answer(text, reply_markup=back_to_menu_keyboard())

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import my_subscription_keyboard
from app.db.session import async_session_factory
from app.formatters import format_subscription_status
from app.repositories.subscriptions import get_active_subscription, get_latest_vpn_account
from app.repositories.users import get_user
from app.services.vpn_delivery import deliver_vpn_config

router = Router()


async def _reminders_enabled(session, telegram_id: int) -> bool:
    user = await get_user(session, telegram_id)
    return True if user is None else user.expiry_reminders_enabled


@router.message(Command("my"))
async def cmd_my(message: Message) -> None:
    async with async_session_factory() as session:
        subscription = await get_active_subscription(session, message.from_user.id)
        reminders = await _reminders_enabled(session, message.from_user.id)

    text = format_subscription_status(subscription)
    await message.answer(text, reply_markup=my_subscription_keyboard(reminders))


@router.callback_query(F.data == "menu:my")
async def menu_my(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        subscription = await get_active_subscription(session, callback.from_user.id)
        reminders = await _reminders_enabled(session, callback.from_user.id)

    text = format_subscription_status(subscription)
    await callback.message.edit_text(text, reply_markup=my_subscription_keyboard(reminders))
    await callback.answer()


@router.callback_query(F.data == "my:config")
async def resend_config(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        subscription = await get_active_subscription(session, callback.from_user.id)
        if not subscription:
            await callback.answer("Активной подписки нет.", show_alert=True)
            return

        account = await get_latest_vpn_account(session, callback.from_user.id)
        if not account or not account.config_text:
            await callback.answer("Конфиг ещё не выдан. Напишите в поддержку.", show_alert=True)
            return

        await deliver_vpn_config(callback.bot, callback.from_user.id, account, subscription.plan)

    await callback.answer("Конфиг отправлен.")


@router.callback_query(F.data.in_({"my:reminders_on", "my:reminders_off"}))
async def toggle_reminders(callback: CallbackQuery) -> None:
    enabled = callback.data == "my:reminders_on"

    async with async_session_factory() as session:
        user = await get_user(session, callback.from_user.id)
        if user:
            user.expiry_reminders_enabled = enabled
        subscription = await get_active_subscription(session, callback.from_user.id)
        await session.commit()

    text = format_subscription_status(subscription)
    if enabled:
        text += "\n\nНапоминания включены: за 7, 3 и 1 день до окончания."
    else:
        text += "\n\nНапоминания отключены."

    await callback.message.edit_text(text, reply_markup=my_subscription_keyboard(enabled))
    await callback.answer("Сохранено")

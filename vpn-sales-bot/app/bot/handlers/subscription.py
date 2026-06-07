from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import my_subscription_keyboard
from app.db.session import async_session_factory
from app.formatters import format_subscription_status
from app.repositories.subscriptions import get_active_subscription, get_latest_vpn_account
from app.services.vpn_delivery import deliver_vpn_config

router = Router()


@router.message(Command("my"))
async def cmd_my(message: Message) -> None:
    async with async_session_factory() as session:
        subscription = await get_active_subscription(session, message.from_user.id)

    text = format_subscription_status(subscription)
    await message.answer(text, reply_markup=my_subscription_keyboard())


@router.callback_query(F.data == "menu:my")
async def menu_my(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        subscription = await get_active_subscription(session, callback.from_user.id)

    text = format_subscription_status(subscription)
    await callback.message.edit_text(text, reply_markup=my_subscription_keyboard())
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

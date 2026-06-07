from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard
from app.db.session import async_session_factory
from app.formatters import format_referral_info
from app.repositories.referrals import count_invited, count_paid_referrals

router = Router()


@router.callback_query(F.data == "menu:referral")
async def menu_referral(callback: CallbackQuery) -> None:
    bot_user = await callback.bot.get_me()
    username = bot_user.username or "bot"

    async with async_session_factory() as session:
        invited = await count_invited(session, callback.from_user.id)
        paid = await count_paid_referrals(session, callback.from_user.id)

    text = format_referral_info(username, callback.from_user.id, invited, paid)
    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard())
    await callback.answer()

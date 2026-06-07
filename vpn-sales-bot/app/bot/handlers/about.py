from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard
from app.formatters import format_about_service

router = Router()


@router.callback_query(F.data == "menu:about")
async def menu_about(callback: CallbackQuery) -> None:
    await callback.message.edit_text(format_about_service(), reply_markup=back_to_menu_keyboard())
    await callback.answer()

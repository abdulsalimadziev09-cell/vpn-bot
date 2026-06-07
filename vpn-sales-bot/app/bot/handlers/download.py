from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard
from app.formatters import format_download_app

router = Router()


@router.callback_query(F.data == "menu:download")
async def menu_download(callback: CallbackQuery) -> None:
    await callback.message.edit_text(format_download_app(), reply_markup=back_to_menu_keyboard())
    await callback.answer()

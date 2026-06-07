from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard
from app.services.split_tunnel_gift import format_split_tunnel_gift, send_split_tunnel_gift

router = Router()


@router.callback_query(F.data == "menu:split_tunnel")
async def menu_split_tunnel(callback: CallbackQuery) -> None:
    await callback.message.edit_text(format_split_tunnel_gift(), reply_markup=back_to_menu_keyboard())
    await send_split_tunnel_gift(callback.bot, callback.from_user.id, include_intro=False)
    await callback.answer()

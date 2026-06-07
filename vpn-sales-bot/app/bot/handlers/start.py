from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import main_menu_keyboard

router = Router()


WELCOME_TEXT = (
    "Добро пожаловать в VPN-магазин.\n\n"
    "Быстрый и стабильный VPN на базе AmneziaWG.\n"
    "Выберите тариф, оплатите и получите персональный конфиг в этом чате."
)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(lambda c: c.data == "menu:main")
async def menu_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()

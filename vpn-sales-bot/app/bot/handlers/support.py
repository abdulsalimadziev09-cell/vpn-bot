from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import main_menu_keyboard
from app.bot.keyboards import back_to_menu_keyboard
from app.formatters import format_vpn_delivery_hint

router = Router()

HELP_TEXT = (
    "FAQ\n\n"
    "1. Какое приложение нужно?\n"
    "   AmneziaVPN — https://amnezia.org\n\n"
    "2. Как получить доступ после оплаты?\n"
    "   Бот пришлёт файл .vpn в этот чат.\n\n"
    "3. Можно ли использовать на нескольких устройствах?\n"
    "   Один ключ = один пользователь. Для семьи — отдельные тарифы.\n\n"
    "4. Подписка не продлилась?\n"
    "   Напишите /my и нажмите «Продлить».\n\n"
    f"{format_vpn_delivery_hint()}"
)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery) -> None:
    await callback.message.edit_text(HELP_TEXT, reply_markup=back_to_menu_keyboard())
    await callback.answer()

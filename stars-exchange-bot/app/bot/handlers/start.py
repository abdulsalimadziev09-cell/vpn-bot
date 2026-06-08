from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import main_menu_keyboard
from app.config import settings
from app.db.session import async_session_factory
from app.repositories.users import get_or_create_user

router = Router()

WELCOME_TEXT = (
    "⭐ <b>Обменник Telegram Stars</b>\n\n"
    "Купите Stars за рубли через Robokassa и отправьте их себе или другу.\n\n"
    f"Курс: от {settings.stars_rub_rate:.2f} ₽ за 1 ⭐"
)

HELP_TEXT = (
    "<b>Как купить Stars</b>\n\n"
    "1. Нажмите «Купить Stars» и выберите пакет или свою сумму.\n"
    "2. Укажите @username получателя (можно себе).\n"
    "3. Оплатите счёт в Robokassa.\n"
    "4. Stars придут на указанный аккаунт Telegram.\n\n"
    "<b>Важно:</b> username должен быть публичным (@username в настройках Telegram)."
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with async_session_factory() as session:
        await get_or_create_user(session, message.from_user.id, message.from_user.username)
        await session.commit()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(Command("support"))
async def cmd_support(message: Message) -> None:
    await message.answer(
        "Напишите номер заказа и @username получателя — поддержка ответит в ближайшее время."
    )


@router.callback_query(lambda c: c.data == "menu:main")
async def menu_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data == "help:main")
async def help_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(HELP_TEXT, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    await callback.answer()

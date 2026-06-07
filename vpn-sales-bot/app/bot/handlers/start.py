from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import main_menu_keyboard
from app.db.session import async_session_factory
from app.repositories.referrals import attach_referrer, parse_referral_start_arg
from app.repositories.trial import can_start_trial
from app.repositories.users import get_or_create_user

router = Router()


WELCOME_TEXT = (
    "Добро пожаловать в VPN-магазин.\n\n"
    "Быстрый и стабильный VPN на базе AmneziaWG.\n"
    "Выберите тариф, оплатите Stars и получите персональный конфиг в этом чате.\n\n"
    "🎁 Новым пользователям — пробный период 1 день."
)


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    referrer_id = parse_referral_start_arg(command.args)
    attached = False

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.username,
        )
        if referrer_id:
            attached = await attach_referrer(session, user, referrer_id)
        show_trial = await can_start_trial(session, message.from_user.id)
        await session.commit()

    text = WELCOME_TEXT
    if attached:
        text += "\n\nВы перешли по реферальной ссылке. Спасибо!"

    await message.answer(text, reply_markup=main_menu_keyboard(show_trial=show_trial))


@router.callback_query(lambda c: c.data == "menu:main")
async def menu_main(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        show_trial = await can_start_trial(session, callback.from_user.id)
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu_keyboard(show_trial=show_trial))
    await callback.answer()

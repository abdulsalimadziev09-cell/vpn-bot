from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot.keyboards import back_to_menu_keyboard
from app.config import settings
from app.db.session import async_session_factory
from app.formatters import format_vpn_delivery_hint
from app.repositories.users import get_user
from app.services.trial import activate_trial

router = Router()

ERRORS = {
    "already_used": "Пробный период уже использован — доступен один раз.",
    "has_subscription": "У вас уже есть активная подписка.",
    "unavailable": "Пробный период временно недоступен.",
    "provision_failed": "Не удалось выдать пробный доступ. Попробуйте позже.",
}


@router.callback_query(F.data == "menu:trial")
async def start_trial(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        result = await activate_trial(
            session,
            callback.bot,
            callback.from_user.id,
            callback.from_user.username,
        )

    if not result.ok:
        await callback.answer(ERRORS.get(result.error or "", "Ошибка."), show_alert=True)
        return

    if settings.vpn_provisioner == "manual":
        text = (
            f"Пробный период на {settings.trial_days} дн. активирован.\n"
            "Конфиг будет выдан в ближайшее время — обычно в течение нескольких минут.\n\n"
            f"{format_vpn_delivery_hint()}"
        )
    else:
        text = (
            f"Пробный период на {settings.trial_days} дн. активирован.\n"
            "Конфиг отправлен выше.\n\n"
            f"{format_vpn_delivery_hint()}"
        )

    await callback.message.edit_text(text, reply_markup=back_to_menu_keyboard())
    await callback.answer("Пробный период активирован!")

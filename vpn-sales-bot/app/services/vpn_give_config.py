import logging
from dataclasses import dataclass

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.formatters import client_name_for_user, format_user_label, format_vpn_delivery_hint
from app.repositories.subscriptions import get_active_subscription
from app.repositories.users import get_user
from app.services.subscription import save_vpn_account
from app.services.vpn_delivery import build_amnezia_vpn_uri, send_vpn_config_files

logger = logging.getLogger(__name__)


@dataclass
class GiveConfigResult:
    ok: bool
    error: str | None = None
    user_label: str | None = None


async def give_user_vpn_config(
    session: AsyncSession,
    bot: Bot,
    telegram_id: int,
    config_text: str,
) -> GiveConfigResult:
    config_text = config_text.strip()
    if not config_text:
        return GiveConfigResult(ok=False, error="Пустой конфиг.")

    subscription = await get_active_subscription(session, telegram_id)
    if not subscription:
        return GiveConfigResult(ok=False, error="У пользователя нет активной подписки.")

    if build_amnezia_vpn_uri(config_text) is None:
        return GiveConfigResult(
            ok=False,
            error="Не удалось распознать конфиг. Ожидается vpn:// или .conf.",
        )

    user = await get_user(session, telegram_id)
    user_label = format_user_label(telegram_id, user.username if user else None)

    account = await save_vpn_account(
        session,
        user_id=telegram_id,
        subscription_id=subscription.id,
        client_name=client_name_for_user(telegram_id),
        config_text=config_text,
    )
    await session.commit()

    try:
        await send_vpn_config_files(
            bot,
            telegram_id,
            account.client_name,
            config_text,
            header=(
                "🔑 Администратор выдал вам новый VPN-ключ.\n"
                "Если старый уже был в AmneziaVPN — удалите его и импортируйте новый.\n\n"
                f"{format_vpn_delivery_hint()}"
            ),
        )
    except Exception:
        logger.exception("Failed to deliver config to user %s", telegram_id)
        return GiveConfigResult(
            ok=False,
            error="Конфиг сохранён, но не удалось отправить в Telegram.",
            user_label=user_label,
        )

    return GiveConfigResult(ok=True, user_label=user_label)

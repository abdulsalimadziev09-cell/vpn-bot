import io
import logging

import qrcode
from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.db.models import Plan, VpnAccount
from app.formatters import format_vpn_delivery_hint
from app.services.split_tunnel_gift import send_split_tunnel_gift

logger = logging.getLogger(__name__)


def _qr_bytes(config_text: str) -> bytes:
    image = qrcode.make(config_text)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


async def deliver_vpn_config(
    bot: Bot,
    telegram_id: int,
    account: VpnAccount,
    plan: Plan,
    *,
    with_split_tunnel_gift: bool = False,
) -> None:
    if not account.config_text:
        await bot.send_message(
            telegram_id,
            "Подписка активирована, но конфиг ещё не готов. Напишите в поддержку.",
        )
        return

    config_file = BufferedInputFile(
        account.config_text.encode("utf-8"),
        filename=f"{account.client_name}.conf",
    )
    qr_file = BufferedInputFile(_qr_bytes(account.config_text), filename=f"{account.client_name}.png")

    await bot.send_message(
        telegram_id,
        f"Оплата прошла успешно. Тариф: {plan.title}.\n\n{format_vpn_delivery_hint()}",
    )
    await bot.send_document(telegram_id, config_file, caption="Ваш VPN-конфиг")
    await bot.send_photo(telegram_id, qr_file, caption="QR для быстрого импорта")

    if with_split_tunnel_gift:
        await send_split_tunnel_gift(bot, telegram_id)

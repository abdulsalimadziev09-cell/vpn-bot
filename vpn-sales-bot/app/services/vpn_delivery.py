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


async def send_vpn_config_files(
    bot: Bot,
    chat_id: int,
    client_name: str,
    config_text: str,
    *,
    header: str = "",
) -> None:
    config_file = BufferedInputFile(
        config_text.encode("utf-8"),
        filename=f"{client_name}.conf",
    )
    qr_file = BufferedInputFile(_qr_bytes(config_text), filename=f"{client_name}.png")

    if header:
        await bot.send_message(chat_id, header)
    await bot.send_document(chat_id, config_file, caption="VPN-конфиг")
    await bot.send_photo(chat_id, qr_file, caption="QR для быстрого импорта")


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

    await send_vpn_config_files(
        bot,
        telegram_id,
        account.client_name,
        account.config_text,
        header=f"Оплата прошла успешно. Тариф: {plan.title}.\n\n{format_vpn_delivery_hint()}",
    )

    if with_split_tunnel_gift:
        await send_split_tunnel_gift(bot, telegram_id)

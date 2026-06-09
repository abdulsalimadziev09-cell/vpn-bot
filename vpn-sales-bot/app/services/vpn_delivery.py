import io
import logging

import qrcode
from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.config import settings
from app.db.models import Plan, VpnAccount
from app.formatters import format_vpn_delivery_hint
from app.services.amnezia_export import AmneziaExportError, conf_to_vpn_uri
from app.services.awg_conf import apply_awg_enrichment
from app.services.vpn_provisioner import is_vpn_uri

logger = logging.getLogger(__name__)


def _qr_bytes(payload: str) -> bytes:
    image = qrcode.make(payload)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _is_awg_conf(config_text: str) -> bool:
    return config_text.strip().startswith("[Interface]")


def _amnezia_export_kwargs() -> dict[str, str]:
    host_name = settings.amnezia_host or settings.ssh_host
    return {
        "host_name": host_name,
        "dns1": settings.amnezia_dns1,
        "dns2": settings.amnezia_dns2,
        "description": settings.amnezia_description,
        "mtu": settings.amnezia_mtu,
    }


def build_amnezia_vpn_uri(config_text: str) -> str | None:
    text = config_text.strip()
    if is_vpn_uri(text):
        return text

    if _is_awg_conf(text):
        source = text
        if not settings.vpn_skip_awg_enrichment:
            source = apply_awg_enrichment(text)
        try:
            return conf_to_vpn_uri(source, **_amnezia_export_kwargs())
        except AmneziaExportError:
            logger.exception("Failed to convert AWG .conf to AmneziaVPN vpn:// URI")
            return None

    return None


async def send_vpn_config_files(
    bot: Bot,
    chat_id: int,
    client_name: str,
    config_text: str,
    *,
    header: str = "",
) -> None:
    vpn_uri = build_amnezia_vpn_uri(config_text)

    if header:
        await bot.send_message(chat_id, header)

    if vpn_uri:
        vpn_file = BufferedInputFile(
            f"{vpn_uri}\n".encode("utf-8"),
            filename=f"{client_name}.vpn",
        )
        await bot.send_document(chat_id, vpn_file, caption="Конфиг AmneziaVPN (.vpn)")
        qr_file = BufferedInputFile(_qr_bytes(vpn_uri), filename=f"{client_name}.png")
        await bot.send_photo(chat_id, qr_file, caption="QR для импорта в AmneziaVPN")
        if len(vpn_uri) <= 3900:
            await bot.send_message(
                chat_id,
                "Или вставьте ключ в AmneziaVPN → «Добавить VPN» → «Вставить из буфера»:\n\n"
                f"<code>{vpn_uri}</code>",
                parse_mode="HTML",
            )
        return

    raw_file = BufferedInputFile(
        config_text.encode("utf-8"),
        filename=f"{client_name}.txt",
    )
    await bot.send_document(chat_id, raw_file, caption="Конфиг (неизвестный формат)")


async def deliver_vpn_config(
    bot: Bot,
    telegram_id: int,
    account: VpnAccount,
    plan: Plan,
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

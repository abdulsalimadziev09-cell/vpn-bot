import io
import logging

import qrcode
from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.config import settings
from app.db.models import Plan, VpnAccount
from app.formatters import format_vpn_delivery_hint
from app.services.amnezia_export import AmneziaExportError, vpn_uri_to_awg_conf
from app.services.awg_conf import apply_awg_enrichment, sanitize_awg_conf_for_import
from app.services.vpn_provisioner import is_vpn_uri

logger = logging.getLogger(__name__)


def _qr_bytes(payload: str) -> bytes:
    image = qrcode.make(payload)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _is_awg_conf(config_text: str) -> bool:
    return config_text.strip().startswith("[Interface]")


def _build_amneziawg_conf(config_text: str) -> str | None:
    if _is_awg_conf(config_text):
        source = config_text
        if not settings.vpn_skip_awg_enrichment:
            source = apply_awg_enrichment(config_text)
        return sanitize_awg_conf_for_import(source)

    if is_vpn_uri(config_text):
        try:
            return sanitize_awg_conf_for_import(vpn_uri_to_awg_conf(config_text.strip()))
        except Exception:
            logger.exception("Failed to extract AWG .conf from bivlked vpn:// URI")
            return None

    if not settings.vpn_skip_awg_enrichment:
        try:
            enriched = apply_awg_enrichment(config_text)
            return sanitize_awg_conf_for_import(enriched)
        except AmneziaExportError:
            logger.exception("Failed to enrich AWG .conf")
            return None

    return sanitize_awg_conf_for_import(config_text)


async def send_vpn_config_files(
    bot: Bot,
    chat_id: int,
    client_name: str,
    config_text: str,
    *,
    header: str = "",
) -> None:
    conf_text = _build_amneziawg_conf(config_text)

    if header:
        await bot.send_message(chat_id, header)

    if conf_text:
        conf_file = BufferedInputFile(
            conf_text.encode("utf-8"),
            filename=f"{client_name}.conf",
        )
        await bot.send_document(chat_id, conf_file, caption="Конфиг AmneziaWG (.conf)")
        qr_file = BufferedInputFile(_qr_bytes(conf_text), filename=f"{client_name}.png")
        await bot.send_photo(chat_id, qr_file, caption="QR для импорта в AmneziaWG")
        return

    fallback_conf = config_text
    if not settings.vpn_skip_awg_enrichment and not is_vpn_uri(config_text):
        fallback_conf = apply_awg_enrichment(config_text)
    config_file = BufferedInputFile(
        fallback_conf.encode("utf-8"),
        filename=f"{client_name}.conf",
    )
    qr_file = BufferedInputFile(_qr_bytes(fallback_conf), filename=f"{client_name}.png")
    await bot.send_document(chat_id, config_file, caption="VPN-конфиг (.conf)")
    await bot.send_photo(chat_id, qr_file, caption="QR для быстрого импорта")


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

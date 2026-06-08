import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from app.config import settings
from app.db.models import Subscription, VpnAccount
from app.db.session import async_session_factory
from app.formatters import format_config_resend_broadcast_header
from app.repositories.subscriptions import get_latest_vpn_account, list_active_subscriptions
from app.services.vpn_delivery import send_vpn_config_files
from app.services.vpn_provisioner import refresh_vpn_client_config

logger = logging.getLogger(__name__)


@dataclass
class ConfigBroadcastResult:
    total: int = 0
    sent: int = 0
    skipped_no_config: int = 0
    failed: list[str] = field(default_factory=list)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _collect_broadcast_targets(
    session,
) -> tuple[list[tuple[Subscription, VpnAccount]], int]:
    subscriptions = await list_active_subscriptions(session)
    seen_users: set[int] = set()
    targets: list[tuple[Subscription, VpnAccount]] = []
    skipped_no_config = 0

    for subscription in subscriptions:
        if subscription.user_id in seen_users:
            continue
        seen_users.add(subscription.user_id)

        account = await get_latest_vpn_account(session, subscription.user_id)
        if not account or not account.config_text:
            skipped_no_config += 1
            continue

        targets.append((subscription, account))

    return targets, skipped_no_config


async def _resolve_config_text(account: VpnAccount) -> str | None:
    if settings.vpn_provisioner != "ssh":
        return account.config_text

    try:
        fresh_config = await refresh_vpn_client_config(account.client_name)
    except Exception:
        logger.exception("Failed to refresh VPN config for %s", account.client_name)
        return account.config_text

    return fresh_config or account.config_text


async def count_resend_targets() -> tuple[int, int]:
    async with async_session_factory() as session:
        _, skipped_no_config = await _collect_broadcast_targets(session)
        subscriptions = await list_active_subscriptions(session)
        seen_users: set[int] = set()
        active_users = 0
        for subscription in subscriptions:
            if subscription.user_id in seen_users:
                continue
            seen_users.add(subscription.user_id)
            active_users += 1
    return active_users - skipped_no_config, skipped_no_config


async def broadcast_refreshed_configs(bot: Bot) -> ConfigBroadcastResult:
    result = ConfigBroadcastResult()
    header = format_config_resend_broadcast_header()

    async with async_session_factory() as session:
        targets, skipped_no_config = await _collect_broadcast_targets(session)
        result.total = len(targets)
        result.skipped_no_config = skipped_no_config

        for subscription, account in targets:
            config_text = await _resolve_config_text(account)
            if not config_text:
                result.skipped_no_config += 1
                continue

            account.config_text = config_text

            try:
                await send_vpn_config_files(
                    bot,
                    subscription.user_id,
                    account.client_name,
                    config_text,
                    header=header,
                )
            except TelegramRetryAfter as exc:
                await asyncio.sleep(exc.retry_after)
                try:
                    await send_vpn_config_files(
                        bot,
                        subscription.user_id,
                        account.client_name,
                        config_text,
                        header=header,
                    )
                except Exception as exc_inner:
                    logger.exception(
                        "Config broadcast failed for user %s after retry",
                        subscription.user_id,
                    )
                    result.failed.append(f"{subscription.user_id}: {exc_inner}")
                    continue
            except TelegramForbiddenError:
                result.failed.append(f"{subscription.user_id}: бот заблокирован")
                continue
            except Exception as exc:
                logger.exception("Config broadcast failed for user %s", subscription.user_id)
                result.failed.append(f"{subscription.user_id}: {exc}")
                continue

            account.config_sent_at = _utcnow()
            result.sent += 1
            await session.commit()
            await asyncio.sleep(0.1)

    return result


def format_config_broadcast_report(result: ConfigBroadcastResult) -> str:
    lines = [
        "✅ Рассылка конфигов завершена.",
        f"Активных подписок с конфигом: {result.total}",
        f"Отправлено: {result.sent}",
    ]
    if result.skipped_no_config:
        lines.append(f"Пропущено (нет конфига): {result.skipped_no_config}")
    if result.failed:
        lines.append(f"Ошибки ({len(result.failed)}):")
        lines.extend(f"• {item}" for item in result.failed[:20])
        if len(result.failed) > 20:
            lines.append(f"… и ещё {len(result.failed) - 20}")
    return "\n".join(lines)

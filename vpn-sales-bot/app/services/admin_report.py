import logging

from aiogram import Bot

from app.config import settings
from app.db.session import async_session_factory
from app.formatters import build_admin_subscriptions_report, format_admin_expiry_alert
from app.repositories.subscriptions import (
    list_active_subscriptions,
    list_subscriptions_for_admin_expiry_alert,
)

logger = logging.getLogger(__name__)


async def send_admin_subscriptions_report(
    bot: Bot,
    *,
    only_admin_id: int | None = None,
) -> None:
    if not settings.admin_ids:
        return
    if only_admin_id is None and not settings.admin_subscription_report_enabled:
        return

    async with async_session_factory() as session:
        subscriptions = await list_active_subscriptions(session)

    messages = build_admin_subscriptions_report(subscriptions)
    targets = [only_admin_id] if only_admin_id is not None else settings.admin_ids
    for admin_id in targets:
        for text in messages:
            try:
                await bot.send_message(admin_id, text)
            except Exception:
                logger.exception("Failed admin subscription report to %s", admin_id)


async def notify_admins_expiring_subscriptions(bot: Bot) -> None:
    if not settings.admin_ids:
        return

    async with async_session_factory() as session:
        subscriptions = await list_subscriptions_for_admin_expiry_alert(
            session,
            settings.admin_expiry_alert_hours,
        )
        for subscription in subscriptions:
            text = format_admin_expiry_alert(subscription)
            for admin_id in settings.admin_ids:
                try:
                    await bot.send_message(admin_id, text)
                except Exception:
                    logger.exception(
                        "Failed admin expiry alert for subscription %s to %s",
                        subscription.id,
                        admin_id,
                    )
            subscription.admin_reminded_1h = True
        await session.commit()

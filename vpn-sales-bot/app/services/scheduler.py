import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.db.session import async_session_factory
from app.repositories.orders import list_paid_unfulfilled
from app.repositories.subscriptions import (
    get_vpn_account_for_subscription,
    list_expired_active,
    list_expiring_subscriptions,
)
from app.services.payment import fulfill_paid_order
from app.services.subscription import expire_subscription
from app.services.vpn_provisioner import get_provisioner

logger = logging.getLogger(__name__)


async def check_expiring_subscriptions(bot: Bot) -> None:
    async with async_session_factory() as session:
        for field, days, text in (
            ("reminded_3d", 3, "Подписка VPN заканчивается через 3 дня. Продлите через /start."),
            ("reminded_1d", 1, "Подписка VPN заканчивается завтра. Продлите через /start."),
        ):
            subscriptions = await list_expiring_subscriptions(session, days, field)
            for subscription in subscriptions:
                try:
                    await bot.send_message(subscription.user_id, text)
                    setattr(subscription, field, True)
                except Exception:
                    logger.exception("Failed expiry reminder for user %s", subscription.user_id)
        await session.commit()


async def expire_subscriptions(bot: Bot) -> None:
    provisioner = get_provisioner()
    async with async_session_factory() as session:
        subscriptions = await list_expired_active(session)
        for subscription in subscriptions:
            account = await get_vpn_account_for_subscription(session, subscription.id)
            if account:
                try:
                    await provisioner.revoke(account.external_id, account.client_name)
                except Exception:
                    logger.exception("Failed revoke for subscription %s", subscription.id)
            await expire_subscription(session, subscription)
            try:
                await bot.send_message(
                    subscription.user_id,
                    "Срок VPN-подписки истёк. Продлите через /start, чтобы снова получить доступ.",
                )
            except Exception:
                logger.exception("Failed expire notice for user %s", subscription.user_id)
        await session.commit()


async def retry_fulfillment(bot: Bot) -> None:
    if settings.vpn_provisioner == "manual":
        return

    async with async_session_factory() as session:
        orders = await list_paid_unfulfilled(session)
        for order in orders:
            try:
                await fulfill_paid_order(session, bot, order)
            except Exception:
                logger.exception("Retry fulfillment failed for order %s", order.id)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        check_expiring_subscriptions,
        "interval",
        hours=settings.expiry_check_hours,
        args=[bot],
        id="check_expiring",
        replace_existing=True,
    )
    scheduler.add_job(
        expire_subscriptions,
        "interval",
        minutes=settings.expire_poll_minutes,
        args=[bot],
        id="expire_subscriptions",
        replace_existing=True,
    )
    scheduler.add_job(
        retry_fulfillment,
        "interval",
        minutes=settings.retry_fulfillment_minutes,
        args=[bot],
        id="retry_fulfillment",
        replace_existing=True,
    )
    return scheduler

import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.db.session import async_session_factory
from app.repositories.orders import list_paid_unfulfilled
from app.services.fulfillment import fulfill_order

logger = logging.getLogger(__name__)


async def retry_unfulfilled_orders(bot: Bot) -> None:
    async with async_session_factory() as session:
        orders = await list_paid_unfulfilled(session)

    for order in orders:
        async with async_session_factory() as session:
            from app.repositories.orders import get_order_by_id

            fresh = await get_order_by_id(session, order.id)
            if not fresh:
                continue
            await fulfill_order(session, bot, fresh)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        retry_unfulfilled_orders,
        "interval",
        minutes=settings.fulfillment_retry_minutes,
        args=[bot],
        id="retry_fulfillment",
        replace_existing=True,
    )
    return scheduler

import logging
from datetime import datetime, timezone

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot.handlers.reminders import send_due_reminder
from app.config import settings
from app.db.session import async_session_factory
from app.bot.keyboards import daily_review_keyboard
from app.repositories.analytics import (
    track_event,
    users_with_daily_review_enabled,
    users_with_digest_enabled,
)
from app.repositories.items import get_pending_reminders
from app.services.daily_review import build_daily_review
from app.services.digest import build_weekly_digest
from app.services.subscription import expire_outdated_plans

logger = logging.getLogger(__name__)


async def poll_reminders(bot: Bot) -> None:
    now = datetime.now(timezone.utc)
    async with async_session_factory() as session:
        reminders = await get_pending_reminders(session, now)
        if not reminders:
            return

        for reminder in reminders:
            try:
                await send_due_reminder(bot, reminder, session)
                await track_event(
                    session,
                    reminder.user_id,
                    "reminder_sent",
                    {"item_id": reminder.item_id, "reminder_id": reminder.id},
                )
            except Exception:
                logger.exception("Failed to send reminder id=%s", reminder.id)

        await session.commit()


async def poll_plan_expiry() -> None:
    async with async_session_factory() as session:
        count = await expire_outdated_plans(session)
        if count:
            logger.info("Expired %s pro subscriptions", count)
        await session.commit()


async def send_weekly_digests(bot: Bot) -> None:
    async with async_session_factory() as session:
        users = await users_with_digest_enabled(session)
        for user in users:
            try:
                text = await build_weekly_digest(session, user.telegram_id)
                if not text:
                    continue
                await bot.send_message(chat_id=user.telegram_id, text=text)
                await track_event(session, user.telegram_id, "digest_sent", {})
            except Exception:
                logger.exception("Digest failed for user %s", user.telegram_id)
        await session.commit()


async def send_daily_reviews(bot: Bot) -> None:
    async with async_session_factory() as session:
        users = await users_with_daily_review_enabled(session)
        for user in users:
            try:
                content = await build_daily_review(session, user.telegram_id)
                if not content:
                    continue
                markup = daily_review_keyboard(content)
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=content.text,
                    reply_markup=markup,
                )
                payload: dict = {"unread": content.unread_count}
                if content.spotlight_item:
                    payload["spotlight_item_id"] = content.spotlight_item.id
                    await track_event(
                        session,
                        user.telegram_id,
                        "daily_review_spotlight",
                        {
                            "item_id": content.spotlight_item.id,
                            "label": content.spotlight_label,
                        },
                    )
                await track_event(session, user.telegram_id, "daily_review_sent", payload)
            except Exception:
                logger.exception("Daily review failed for user %s", user.telegram_id)
        await session.commit()


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        poll_reminders,
        "interval",
        seconds=settings.reminder_poll_seconds,
        args=[bot],
        id="poll_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        poll_plan_expiry,
        "interval",
        seconds=3600,
        id="poll_plan_expiry",
        replace_existing=True,
    )
    scheduler.add_job(
        send_weekly_digests,
        "cron",
        day_of_week=settings.digest_day_of_week,
        hour=settings.digest_hour,
        minute=0,
        args=[bot],
        id="weekly_digest",
        replace_existing=True,
    )
    scheduler.add_job(
        send_daily_reviews,
        "cron",
        hour=settings.daily_review_hour,
        minute=0,
        args=[bot],
        id="daily_review",
        replace_existing=True,
    )
    return scheduler

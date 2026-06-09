import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.formatters import _days_word
from app.db.models import Plan, Referral, Subscription, SubscriptionStatus
from app.repositories.plans import get_plan_by_code
from app.repositories.referrals import count_paid_orders, get_pending_referral_for_user
from app.repositories.subscriptions import get_active_subscription

logger = logging.getLogger(__name__)


async def add_bonus_days(session: AsyncSession, user_id: int, days: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    subscription = await get_active_subscription(session, user_id)
    if subscription:
        subscription.expires_at = subscription.expires_at + timedelta(days=days)
        subscription.reminded_7d = False
        subscription.reminded_3d = False
        subscription.reminded_1d = False
        subscription.admin_reminded_1h = False
        return subscription

    plan = await get_plan_by_code(session, "month_1")
    if plan is None:
        return None

    subscription = Subscription(
        user_id=user_id,
        plan_id=plan.id,
        starts_at=now,
        expires_at=now + timedelta(days=days),
        status=SubscriptionStatus.ACTIVE,
    )
    session.add(subscription)
    await session.flush()
    return subscription


async def process_referral_bonus(session: AsyncSession, bot: Bot, referred_user_id: int) -> None:
    if await count_paid_orders(session, referred_user_id) != 1:
        return

    referral = await get_pending_referral_for_user(session, referred_user_id)
    if not referral:
        return

    subscription = await add_bonus_days(session, referral.referrer_id, settings.referral_bonus_days)
    if not subscription:
        return

    referral.bonus_granted = True
    await session.flush()

    try:
        await bot.send_message(
            referral.referrer_id,
            f"🎉 Ваш друг оплатил подписку! Вам начислено "
            f"+{settings.referral_bonus_days} {_days_word(settings.referral_bonus_days)}.",
        )
    except Exception:
        logger.exception("Failed to notify referrer %s", referral.referrer_id)

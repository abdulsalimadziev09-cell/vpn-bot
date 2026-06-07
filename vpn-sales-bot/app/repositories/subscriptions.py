from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Plan, Subscription, SubscriptionStatus, VpnAccount


async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Subscription)
        .options(joinedload(Subscription.plan))
        .where(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at > now,
        )
        .order_by(Subscription.expires_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_expiring_subscriptions(
    session: AsyncSession,
    within_days: int,
    reminded_field: str,
) -> list[Subscription]:
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(days=within_days)
    query = (
        select(Subscription)
        .options(joinedload(Subscription.plan), joinedload(Subscription.user))
        .where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at > now,
            Subscription.expires_at <= deadline,
        )
    )
    if reminded_field == "reminded_3d":
        query = query.where(Subscription.reminded_3d.is_(False))
    elif reminded_field == "reminded_1d":
        query = query.where(Subscription.reminded_1d.is_(False))

    result = await session.execute(query)
    return list(result.scalars().unique().all())


async def list_expired_active(session: AsyncSession) -> list[Subscription]:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Subscription)
        .options(joinedload(Subscription.plan), joinedload(Subscription.user))
        .where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.expires_at <= now,
        )
    )
    return list(result.scalars().unique().all())


async def get_latest_vpn_account(session: AsyncSession, user_id: int) -> VpnAccount | None:
    result = await session.execute(
        select(VpnAccount)
        .where(VpnAccount.user_id == user_id)
        .order_by(VpnAccount.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_vpn_account_for_subscription(
    session: AsyncSession,
    subscription_id: int,
) -> VpnAccount | None:
    result = await session.execute(
        select(VpnAccount)
        .where(VpnAccount.subscription_id == subscription_id)
        .order_by(VpnAccount.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()

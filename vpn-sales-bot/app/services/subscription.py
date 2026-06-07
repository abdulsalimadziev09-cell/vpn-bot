from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, Plan, Subscription, SubscriptionStatus, VpnAccount


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def activate_or_extend_subscription(
    session: AsyncSession,
    user_id: int,
    plan: Plan,
) -> Subscription:
    from app.repositories.subscriptions import get_active_subscription

    now = _utcnow()
    subscription = await get_active_subscription(session, user_id)

    if subscription:
        subscription.expires_at = subscription.expires_at + timedelta(days=plan.days)
        subscription.plan_id = plan.id
        subscription.reminded_7d = False
        subscription.reminded_3d = False
        subscription.reminded_1d = False
        return subscription

    subscription = Subscription(
        user_id=user_id,
        plan_id=plan.id,
        starts_at=now,
        expires_at=now + timedelta(days=plan.days),
        status=SubscriptionStatus.ACTIVE,
    )
    session.add(subscription)
    await session.flush()
    return subscription


async def expire_subscription(session: AsyncSession, subscription: Subscription) -> None:
    subscription.status = SubscriptionStatus.EXPIRED


async def save_vpn_account(
    session: AsyncSession,
    *,
    user_id: int,
    subscription_id: int,
    client_name: str,
    config_text: str,
    external_id: str | None = None,
    server_id: int | None = None,
) -> VpnAccount:
    account = VpnAccount(
        user_id=user_id,
        subscription_id=subscription_id,
        server_id=server_id,
        client_name=client_name,
        config_text=config_text,
        external_id=external_id,
        config_sent_at=_utcnow(),
    )
    session.add(account)
    await session.flush()
    return account


async def mark_order_fulfilled(session: AsyncSession, order: Order) -> None:
    from app.db.models import OrderStatus

    order.status = OrderStatus.FULFILLED
    order.fulfilled_at = _utcnow()

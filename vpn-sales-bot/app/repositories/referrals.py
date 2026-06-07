from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, OrderStatus, Referral, User


def parse_referral_start_arg(args: str | None) -> int | None:
    if not args or not args.startswith("ref"):
        return None
    try:
        referrer_id = int(args.removeprefix("ref"))
    except ValueError:
        return None
    return referrer_id if referrer_id > 0 else None


async def attach_referrer(
    session: AsyncSession,
    user: User,
    referrer_id: int,
) -> bool:
    if user.telegram_id == referrer_id or user.referred_by_id is not None:
        return False

    referrer = await session.get(User, referrer_id)
    if referrer is None:
        return False

    existing = await session.execute(select(Referral).where(Referral.referred_id == user.telegram_id))
    if existing.scalar_one_or_none():
        return False

    user.referred_by_id = referrer_id
    session.add(
        Referral(
            referrer_id=referrer_id,
            referred_id=user.telegram_id,
        )
    )
    await session.flush()
    return True


async def count_invited(session: AsyncSession, referrer_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(Referral).where(Referral.referrer_id == referrer_id)
    )
    return int(result.scalar_one())


async def count_paid_referrals(session: AsyncSession, referrer_id: int) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Referral)
        .where(Referral.referrer_id == referrer_id, Referral.bonus_granted.is_(True))
    )
    return int(result.scalar_one())


async def get_pending_referral_for_user(session: AsyncSession, referred_id: int) -> Referral | None:
    result = await session.execute(
        select(Referral).where(
            Referral.referred_id == referred_id,
            Referral.bonus_granted.is_(False),
        )
    )
    return result.scalar_one_or_none()


async def count_paid_orders(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Order)
        .where(
            Order.user_id == user_id,
            Order.status.in_([OrderStatus.PAID, OrderStatus.FULFILLED]),
        )
    )
    return int(result.scalar_one())

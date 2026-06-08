from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Item, User, UserPlan


def _now() -> datetime:
    return datetime.now(timezone.utc)


def is_pro_active(user: User, now: datetime | None = None) -> bool:
    current = now or _now()
    if user.plan != UserPlan.PRO:
        return False
    if user.plan_expires_at and user.plan_expires_at <= current:
        return False
    return True


def item_limit_for_user(user: User, now: datetime | None = None) -> int:
    if is_pro_active(user, now):
        return settings.pro_item_limit
    return settings.free_item_limit


async def refresh_user_plan(session: AsyncSession, user: User) -> User:
    if user.plan == UserPlan.PRO and user.plan_expires_at and user.plan_expires_at <= _now():
        user.plan = UserPlan.FREE
        user.plan_expires_at = None
        await session.flush()
    return user


async def activate_pro(session: AsyncSession, user: User, days: int | None = None) -> User:
    duration = days or settings.pro_days
    base = _now()
    if is_pro_active(user) and user.plan_expires_at:
        base = user.plan_expires_at
    user.plan = UserPlan.PRO
    user.plan_expires_at = base + timedelta(days=duration)
    await session.flush()
    return user


async def expire_outdated_plans(session: AsyncSession) -> int:
    now = _now()
    stmt = (
        update(User)
        .where(User.plan == UserPlan.PRO, User.plan_expires_at.is_not(None), User.plan_expires_at <= now)
        .values(plan=UserPlan.FREE, plan_expires_at=None)
    )
    result = await session.execute(stmt)
    return result.rowcount or 0


async def count_user_items(session: AsyncSession, user_id: int) -> int:
    from sqlalchemy import func

    stmt = select(func.count()).select_from(Item).where(Item.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one()


def format_plan_status(user: User) -> str:
    if is_pro_active(user):
        expires = user.plan_expires_at.astimezone(timezone.utc).strftime("%d.%m.%Y") if user.plan_expires_at else "—"
        return f"Pro до {expires}"
    return f"Free (лимит {settings.free_item_limit} сохранений)"

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, UserEvent


async def track_event(
    session: AsyncSession,
    user_id: int,
    event_type: str,
    payload: dict | None = None,
) -> None:
    session.add(UserEvent(user_id=user_id, event_type=event_type, payload=payload))
    user = await session.get(User, user_id)
    if user:
        user.last_active_at = datetime.now(timezone.utc)
    await session.flush()


async def count_events(
    session: AsyncSession,
    user_id: int,
    event_type: str,
    since: datetime,
) -> int:
    stmt = (
        select(func.count())
        .select_from(UserEvent)
        .where(
            UserEvent.user_id == user_id,
            UserEvent.event_type == event_type,
            UserEvent.created_at >= since,
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_active_user_ids(session: AsyncSession, since: datetime) -> list[int]:
    stmt = select(UserEvent.user_id).where(UserEvent.created_at >= since).distinct()
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def users_with_digest_enabled(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.digest_enabled.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def users_with_daily_review_enabled(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.daily_review_enabled.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def aggregate_retention_metrics(session: AsyncSession, days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    dau_stmt = (
        select(func.count(func.distinct(UserEvent.user_id)))
        .where(UserEvent.created_at >= now - timedelta(days=1))
    )
    wau_stmt = (
        select(func.count(func.distinct(UserEvent.user_id)))
        .where(UserEvent.created_at >= since)
    )
    dau = (await session.execute(dau_stmt)).scalar_one()
    wau = (await session.execute(wau_stmt)).scalar_one()
    return {"dau": dau, "wau": wau, "window_days": days}

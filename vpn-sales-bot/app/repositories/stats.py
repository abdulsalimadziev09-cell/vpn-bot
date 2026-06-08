from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, OrderStatus, Plan, User

MSK = ZoneInfo("Europe/Moscow")
_PAID_STATUSES = (OrderStatus.PAID, OrderStatus.FULFILLED)


@dataclass(frozen=True)
class AdminStats:
    total_users: int
    users_today: int
    purchases: int
    stars_sold: int
    revenue_rub: int


def start_of_today_msk() -> datetime:
    now_msk = datetime.now(MSK)
    start_msk = now_msk.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_msk.astimezone(timezone.utc)


async def get_admin_stats(session: AsyncSession) -> AdminStats:
    total_users = int(await session.scalar(select(func.count()).select_from(User)) or 0)
    users_today = int(
        await session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.created_at >= start_of_today_msk())
        )
        or 0
    )
    purchases = int(
        await session.scalar(
            select(func.count())
            .select_from(Order)
            .where(
                Order.status.in_(_PAID_STATUSES),
                Order.amount > 0,
            )
        )
        or 0
    )
    stars_sold = int(
        await session.scalar(
            select(func.coalesce(func.sum(Order.amount), 0)).where(
                Order.status.in_(_PAID_STATUSES),
                Order.amount > 0,
            )
        )
        or 0
    )
    revenue_rub = int(
        await session.scalar(
            select(func.coalesce(func.sum(Plan.price_rub), 0))
            .select_from(Order)
            .join(Plan, Order.plan_id == Plan.id)
            .where(
                Order.status.in_(_PAID_STATUSES),
                Order.amount > 0,
            )
        )
        or 0
    )
    return AdminStats(
        total_users=total_users,
        users_today=users_today,
        purchases=purchases,
        stars_sold=stars_sold,
        revenue_rub=revenue_rub,
    )

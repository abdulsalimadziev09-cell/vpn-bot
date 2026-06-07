from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Plan


async def list_active_plans(session: AsyncSession) -> list[Plan]:
    result = await session.execute(
        select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.price_rub)
    )
    return list(result.scalars().all())


async def get_plan_by_id(session: AsyncSession, plan_id: int) -> Plan | None:
    result = await session.execute(select(Plan).where(Plan.id == plan_id))
    return result.scalar_one_or_none()


async def get_plan_by_code(session: AsyncSession, code: str) -> Plan | None:
    result = await session.execute(select(Plan).where(Plan.code == code))
    return result.scalar_one_or_none()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import StarPackage


async def list_active_packages(session: AsyncSession) -> list[StarPackage]:
    result = await session.execute(
        select(StarPackage)
        .where(StarPackage.is_active.is_(True))
        .order_by(StarPackage.sort_order.asc(), StarPackage.stars_amount.asc())
    )
    return list(result.scalars().all())


async def get_package_by_id(session: AsyncSession, package_id: int) -> StarPackage | None:
    result = await session.execute(select(StarPackage).where(StarPackage.id == package_id))
    return result.scalar_one_or_none()

"""Seed default star packages."""

import asyncio

from sqlalchemy import select

from app.db.models import StarPackage
from app.db.session import async_session_factory

DEFAULT_PACKAGES = [
    ("stars_100", "100 Stars", 100, 165, 1),
    ("stars_250", "250 Stars", 250, 410, 2),
    ("stars_500", "500 Stars", 500, 800, 3),
    ("stars_1000", "1000 Stars", 1000, 1550, 4),
]


async def main() -> None:
    async with async_session_factory() as session:
        for code, title, stars, rub, sort_order in DEFAULT_PACKAGES:
            result = await session.execute(select(StarPackage).where(StarPackage.code == code))
            package = result.scalar_one_or_none()
            if package:
                package.title = title
                package.stars_amount = stars
                package.price_rub = rub
                package.sort_order = sort_order
                package.is_active = True
            else:
                session.add(
                    StarPackage(
                        code=code,
                        title=title,
                        stars_amount=stars,
                        price_rub=rub,
                        sort_order=sort_order,
                        is_active=True,
                    )
                )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())

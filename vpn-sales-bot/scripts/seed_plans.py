"""Re-seed default plans if needed."""

import asyncio

from sqlalchemy import select

from app.db.models import Plan
from app.db.session import async_session_factory

DEFAULT_PLANS = [
    ("month_1", "1 месяц", 30, 299, 100),
    ("month_3", "3 месяца", 90, 799, 250),
]

DEACTIVATED_PLAN_CODES = ("year_1",)


async def main() -> None:
    async with async_session_factory() as session:
        for code, title, days, price_rub, stars_price in DEFAULT_PLANS:
            result = await session.execute(select(Plan).where(Plan.code == code))
            plan = result.scalar_one_or_none()
            if plan:
                plan.title = title
                plan.days = days
                plan.price_rub = price_rub
                plan.stars_price = stars_price
                plan.is_active = True
                continue
            session.add(
                Plan(
                    code=code,
                    title=title,
                    days=days,
                    price_rub=price_rub,
                    stars_price=stars_price,
                    is_active=True,
                )
            )

        for code in DEACTIVATED_PLAN_CODES:
            result = await session.execute(select(Plan).where(Plan.code == code))
            plan = result.scalar_one_or_none()
            if plan:
                plan.is_active = False

        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())

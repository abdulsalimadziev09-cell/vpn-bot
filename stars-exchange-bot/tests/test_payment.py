from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, OrderStatus, StarPackage, User
from app.repositories.orders import create_order
from app.services.payment import mark_paid_from_robokassa


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        session.add(User(telegram_id=100, username="buyer"))
        session.add(
            StarPackage(
                code="test",
                title="Test",
                stars_amount=100,
                price_rub=165,
            )
        )
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_mark_paid_idempotent(session):
    pkg = (await session.execute(select(StarPackage))).scalar_one()
    order = await create_order(
        session,
        buyer_id=100,
        recipient_username="durov",
        stars_amount=100,
        amount_rub=165,
        package=pkg,
    )
    await session.commit()

    paid = await mark_paid_from_robokassa(session, inv_id=order.robokassa_inv_id, out_sum="165")
    assert paid is not None
    assert paid.status == OrderStatus.PAID

    again = await mark_paid_from_robokassa(session, inv_id=order.robokassa_inv_id, out_sum="165")
    assert again.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_mark_paid_wrong_amount(session):
    pkg = (await session.execute(select(StarPackage))).scalar_one()
    order = await create_order(
        session,
        buyer_id=100,
        recipient_username="durov",
        stars_amount=100,
        amount_rub=165,
        package=pkg,
    )
    await session.commit()

    result = await mark_paid_from_robokassa(session, inv_id=order.robokassa_inv_id, out_sum="999")
    assert result is None

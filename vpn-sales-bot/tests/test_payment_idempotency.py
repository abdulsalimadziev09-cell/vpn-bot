from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, Order, OrderStatus, Plan, User
from app.services.payment import mark_order_paid_from_stars


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(User(telegram_id=100, username="buyer"))
        session.add(
            Plan(
                id=1,
                code="month_1",
                title="1 месяц",
                days=30,
                price_rub=299,
                stars_price=50,
                is_active=True,
            )
        )
        session.add(
            Order(
                id=7,
                user_id=100,
                plan_id=1,
                amount=50,
                status=OrderStatus.PAID,
                robokassa_inv_id=7,
                paid_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_duplicate_stars_payment_is_idempotent(session):
    order = await mark_order_paid_from_stars(session, order_id=7, user_id=100)

    assert order is not None
    assert order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_stars_payment_rejects_wrong_user(session):
    order = await mark_order_paid_from_stars(session, order_id=7, user_id=999)

    assert order is None

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, Plan, Subscription, SubscriptionStatus, User
from app.services.subscription import activate_or_extend_subscription


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(User(telegram_id=100, username="tester"))
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
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_activate_creates_subscription(session):
    plan = await session.get(Plan, 1)
    subscription = await activate_or_extend_subscription(session, 100, plan)
    await session.commit()

    assert subscription.user_id == 100
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.expires_at > subscription.starts_at


@pytest.mark.asyncio
async def test_extend_adds_days(session):
    plan = await session.get(Plan, 1)
    now = datetime.now(timezone.utc)
    existing = Subscription(
        user_id=100,
        plan_id=1,
        starts_at=now,
        expires_at=now + timedelta(days=10),
        status=SubscriptionStatus.ACTIVE,
    )
    session.add(existing)
    await session.commit()

    previous_expires = existing.expires_at
    subscription = await activate_or_extend_subscription(session, 100, plan)
    await session.commit()

    assert subscription.id == existing.id
    assert subscription.expires_at == previous_expires + timedelta(days=30)

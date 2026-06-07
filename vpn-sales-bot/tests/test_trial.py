import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, Plan, User
from app.repositories.trial import can_start_trial


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        session.add(User(telegram_id=100, username="trial_user", trial_used=False))
        session.add(
            Plan(
                id=1,
                code="month_1",
                title="1 месяц",
                days=30,
                price_rub=299,
                stars_price=150,
                is_active=True,
            )
        )
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_can_start_trial_for_new_user(session):
    assert await can_start_trial(session, 100) is True


@pytest.mark.asyncio
async def test_cannot_start_trial_twice(session):
    user = await session.get(User, 100)
    user.trial_used = True
    await session.commit()
    assert await can_start_trial(session, 100) is False

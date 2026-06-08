from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, Order, OrderStatus, Plan, User
from app.formatters import format_admin_stats
from app.repositories.stats import AdminStats, get_admin_stats, start_of_today_msk


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        plan = Plan(
            id=1,
            code="month_1",
            title="1 месяц",
            days=30,
            price_rub=299,
            stars_price=100,
            is_active=True,
        )
        session.add(plan)
        await session.flush()

        now = datetime.now(timezone.utc)
        session.add(User(telegram_id=1, username="old", created_at=now - timedelta(days=2)))
        session.add(User(telegram_id=2, username="today", created_at=now))
        session.add(
            Order(
                user_id=1,
                plan_id=1,
                amount=100,
                status=OrderStatus.FULFILLED,
                paid_at=now,
            )
        )
        session.add(
            Order(
                user_id=2,
                plan_id=1,
                amount=100,
                status=OrderStatus.FULFILLED,
                paid_at=now,
            )
        )
        session.add(
            Order(
                user_id=2,
                plan_id=1,
                amount=0,
                status=OrderStatus.FULFILLED,
            )
        )
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_admin_stats(session):
    stats = await get_admin_stats(session)
    assert stats.total_users == 2
    assert stats.users_today == 1
    assert stats.purchases == 2
    assert stats.stars_sold == 200
    assert stats.revenue_rub == 598


def test_format_admin_stats():
    text = format_admin_stats(
        AdminStats(
            total_users=1254,
            users_today=87,
            purchases=341,
            stars_sold=57000,
            revenue_rub=184250,
        )
    )
    assert "👥 Всего пользователей: 1 254" in text
    assert "📈 За сегодня: 87" in text
    assert "💳 Покупок: 341" in text
    assert "⭐ Продано Stars: 57 000" in text
    assert "💰 Оборот: 184 250 ₽" in text


def test_start_of_today_msk_is_utc_aware():
    start = start_of_today_msk()
    assert start.tzinfo is not None

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Base, Plan, Subscription, SubscriptionStatus, User
from app.formatters import format_admin_expiry_alert
from app.repositories.subscriptions import list_subscriptions_for_admin_expiry_alert
from app.services.admin_report import notify_admins_expiring_subscriptions


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


def test_format_admin_expiry_alert():
    now = datetime.now(timezone.utc)
    user = User(telegram_id=100, username="tester")
    plan = Plan(id=1, code="month_1", title="1 месяц", days=30, price_rub=299, stars_price=100)
    subscription = Subscription(
        user_id=100,
        plan_id=1,
        starts_at=now,
        expires_at=now + timedelta(minutes=45),
        status=SubscriptionStatus.ACTIVE,
    )
    subscription.user = user
    subscription.plan = plan

    text = format_admin_expiry_alert(subscription)
    assert "⚠️" in text
    assert "@tester" in text
    assert "менее часа" in text
    assert "1 месяц" in text


@pytest.mark.asyncio
async def test_list_subscriptions_for_admin_expiry_alert(session):
    now = datetime.now(timezone.utc)
    soon = Subscription(
        user_id=100,
        plan_id=1,
        starts_at=now,
        expires_at=now + timedelta(minutes=30),
        status=SubscriptionStatus.ACTIVE,
    )
    later = Subscription(
        user_id=100,
        plan_id=1,
        starts_at=now,
        expires_at=now + timedelta(hours=5),
        status=SubscriptionStatus.ACTIVE,
    )
    already_notified = Subscription(
        user_id=100,
        plan_id=1,
        starts_at=now,
        expires_at=now + timedelta(minutes=20),
        status=SubscriptionStatus.ACTIVE,
        admin_reminded_1h=True,
    )
    session.add_all([soon, later, already_notified])
    await session.commit()

    result = await list_subscriptions_for_admin_expiry_alert(session, within_hours=1)
    assert len(result) == 1
    assert result[0].id == soon.id


@pytest.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        now = datetime.now(timezone.utc)
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
        session.add(
            Subscription(
                user_id=100,
                plan_id=1,
                starts_at=now,
                expires_at=now + timedelta(minutes=40),
                status=SubscriptionStatus.ACTIVE,
            )
        )
        await session.commit()

    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_notify_admins_expiring_subscriptions(session_factory, monkeypatch):
    monkeypatch.setattr(
        "app.services.admin_report.async_session_factory",
        session_factory,
    )
    monkeypatch.setattr(settings, "admin_ids", [999])
    monkeypatch.setattr(settings, "admin_expiry_alert_hours", 1)

    bot = AsyncMock()
    await notify_admins_expiring_subscriptions(bot)

    bot.send_message.assert_awaited_once()
    assert bot.send_message.await_args.args[0] == 999
    assert "@tester" in bot.send_message.await_args.args[1]

    async with session_factory() as session:
        subscription = (await session.execute(select(Subscription))).scalar_one()
        assert subscription.admin_reminded_1h is True

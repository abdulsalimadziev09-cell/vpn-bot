from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, Plan, Subscription, SubscriptionStatus, User, VpnAccount
from app.formatters import format_config_resend_broadcast_header
from app.services.vpn_config_broadcast import (
    broadcast_refreshed_configs,
    count_resend_targets,
    format_config_broadcast_report,
)


@pytest.fixture
async def session_factory():
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
        now = datetime.now(timezone.utc)
        session.add(User(telegram_id=101, username="with_config"))
        session.add(User(telegram_id=102, username="no_config"))
        session.add(
            Subscription(
                user_id=101,
                plan_id=1,
                starts_at=now,
                expires_at=now + timedelta(days=10),
                status=SubscriptionStatus.ACTIVE,
            )
        )
        session.add(
            Subscription(
                user_id=102,
                plan_id=1,
                starts_at=now,
                expires_at=now + timedelta(days=10),
                status=SubscriptionStatus.ACTIVE,
            )
        )
        await session.flush()
        session.add(
            VpnAccount(
                user_id=101,
                subscription_id=1,
                client_name="tg_101",
                config_text="vpn://TEST101",
            )
        )
        session.add(
            VpnAccount(
                user_id=102,
                subscription_id=2,
                client_name="tg_102",
                config_text=None,
            )
        )
        await session.commit()

    yield factory
    await engine.dispose()


def test_format_config_resend_broadcast_header():
    text = format_config_resend_broadcast_header()
    assert "извинения" in text.lower()
    assert "работает" in text.lower()
    assert "AmneziaWG" in text


def test_format_config_broadcast_report():
    text = format_config_broadcast_report(
        type(
            "Result",
            (),
            {
                "total": 3,
                "sent": 2,
                "skipped_no_config": 1,
                "failed": ["999: blocked"],
            },
        )()
    )
    assert "Отправлено: 2" in text
    assert "999: blocked" in text


@pytest.mark.asyncio
async def test_count_resend_targets(session_factory, monkeypatch):
    monkeypatch.setattr(
        "app.services.vpn_config_broadcast.async_session_factory",
        session_factory,
    )
    with_config, without_config = await count_resend_targets()
    assert with_config == 1
    assert without_config == 1


@pytest.mark.asyncio
async def test_broadcast_refreshed_configs(session_factory, monkeypatch):
    monkeypatch.setattr(
        "app.services.vpn_config_broadcast.async_session_factory",
        session_factory,
    )
    monkeypatch.setattr(
        "app.services.vpn_config_broadcast.settings.vpn_provisioner",
        "manual",
    )

    bot = AsyncMock()
    send_files = AsyncMock()
    with patch("app.services.vpn_config_broadcast.send_vpn_config_files", send_files):
        result = await broadcast_refreshed_configs(bot)

    assert result.total == 1
    assert result.sent == 1
    assert result.skipped_no_config == 1
    send_files.assert_awaited_once()
    assert send_files.await_args.kwargs["header"] == format_config_resend_broadcast_header()

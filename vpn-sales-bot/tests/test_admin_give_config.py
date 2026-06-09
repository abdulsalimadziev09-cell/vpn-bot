from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, Plan, Subscription, SubscriptionStatus, User
from app.services.amnezia_export import conf_to_vpn_uri
from app.services.vpn_give_config import give_user_vpn_config

SAMPLE_CONF = """[Interface]
PrivateKey = w+/FRUgl07Ozta/jjMu+lTYREpPxHaM+zpDGy6W4+wY=
Address = 10.8.1.3/32
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = bPojFUDaXFty60Y/5Y45ycvI4lFn4vRvTsM/bCVZ2T4=
AllowedIPs = 0.0.0.0/0
Endpoint = 89.169.53.7:47661
PersistentKeepalive = 25
"""


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
        session.add(User(telegram_id=101, username="active_user"))
        session.add(
            Subscription(
                user_id=101,
                plan_id=1,
                starts_at=now,
                expires_at=now + timedelta(days=10),
                status=SubscriptionStatus.ACTIVE,
            )
        )
        await session.commit()

    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_give_user_vpn_config_success(session_factory):
    vpn_uri = conf_to_vpn_uri(SAMPLE_CONF, host_name="89.169.53.7")
    bot = AsyncMock()
    send_files = AsyncMock()

    async with session_factory() as session:
        with patch("app.services.vpn_give_config.send_vpn_config_files", send_files):
            result = await give_user_vpn_config(session, bot, 101, vpn_uri)

    assert result.ok is True
    assert result.user_label == "@active_user"
    send_files.assert_awaited_once()
    assert send_files.await_args.args[1] == 101


@pytest.mark.asyncio
async def test_give_user_vpn_config_no_subscription(session_factory):
    bot = AsyncMock()
    vpn_uri = conf_to_vpn_uri(SAMPLE_CONF, host_name="89.169.53.7")

    async with session_factory() as session:
        result = await give_user_vpn_config(session, bot, 999, vpn_uri)

    assert result.ok is False
    assert "подписк" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_give_user_vpn_config_invalid_config(session_factory):
    bot = AsyncMock()

    async with session_factory() as session:
        result = await give_user_vpn_config(session, bot, 101, "not-a-config")

    assert result.ok is False
    assert "распознать" in (result.error or "").lower()

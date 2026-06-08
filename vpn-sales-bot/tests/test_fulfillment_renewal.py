from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Base, Order, OrderStatus, Plan, Subscription, SubscriptionStatus, User, VpnAccount
from app.repositories.orders import create_order
from app.services.payment import fulfill_paid_order


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
                stars_price=100,
                is_active=True,
            )
        )
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_fulfill_reuses_existing_config_on_renewal(session):
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=100,
        plan_id=1,
        starts_at=now - timedelta(days=5),
        expires_at=now + timedelta(days=25),
        status=SubscriptionStatus.ACTIVE,
    )
    session.add(subscription)
    await session.flush()

    session.add(
        VpnAccount(
            user_id=100,
            subscription_id=subscription.id,
            client_name="tg_100",
            config_text="[Interface]\nPrivateKey=test\n",
        )
    )
    plan = await session.get(Plan, 1)
    order = await create_order(session, 100, plan)
    order.status = OrderStatus.PAID
    await session.commit()

    bot = AsyncMock()
    with patch("app.services.payment.get_provisioner") as get_provisioner:
        result = await fulfill_paid_order(session, bot, order)

    get_provisioner.assert_not_called()
    assert result.ok is True
    assert result.reused_config is True
    assert order.status == OrderStatus.FULFILLED
    bot.send_message.assert_awaited_once()
    assert "не изменился" in bot.send_message.await_args.args[1]


@pytest.mark.asyncio
async def test_fulfill_provisions_when_no_existing_config(session):
    plan = await session.get(Plan, 1)
    order = await create_order(session, 100, plan)
    order.status = OrderStatus.PAID
    await session.commit()

    mock_provisioner = AsyncMock()
    mock_provisioner.provision.return_value = type(
        "Result",
        (),
        {
            "client_name": "tg_100",
            "config_text": "[Interface]\nPrivateKey=new\n",
            "external_id": None,
            "server_id": None,
            "requires_manual": False,
        },
    )()

    bot = AsyncMock()
    with patch("app.services.payment.get_provisioner", return_value=mock_provisioner):
        with patch("app.services.payment.deliver_vpn_config", new_callable=AsyncMock) as deliver:
            result = await fulfill_paid_order(session, bot, order)

    mock_provisioner.provision.assert_awaited_once()
    deliver.assert_awaited_once()
    assert result.ok is True
    assert result.reused_config is False

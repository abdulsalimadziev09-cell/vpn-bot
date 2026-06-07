import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Order, OrderStatus, Plan, Subscription, SubscriptionStatus
from app.repositories.plans import get_plan_by_code
from app.repositories.subscriptions import get_active_subscription
from app.repositories.users import get_or_create_user
from app.services.payment import notify_admins_manual_order
from app.services.subscription import save_vpn_account
from app.services.vpn_delivery import deliver_vpn_config
from app.services.vpn_provisioner import get_provisioner

logger = logging.getLogger(__name__)


@dataclass
class TrialResult:
    ok: bool
    error: str | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def activate_trial(
    session: AsyncSession,
    bot: Bot,
    telegram_id: int,
    username: str | None,
) -> TrialResult:
    user = await get_or_create_user(session, telegram_id, username)

    if user.trial_used:
        return TrialResult(ok=False, error="already_used")

    if await get_active_subscription(session, telegram_id):
        return TrialResult(ok=False, error="has_subscription")

    plan = await get_plan_by_code(session, "month_1")
    if plan is None:
        return TrialResult(ok=False, error="unavailable")

    now = _utcnow()
    user.trial_used = True
    subscription = Subscription(
        user_id=telegram_id,
        plan_id=plan.id,
        starts_at=now,
        expires_at=now + timedelta(days=settings.trial_days),
        status=SubscriptionStatus.ACTIVE,
    )
    session.add(subscription)
    await session.flush()

    trial_order = _TrialOrder(user=user, plan=plan)
    provisioner = get_provisioner()
    try:
        result = await provisioner.provision(trial_order)
    except Exception:
        logger.exception("Trial provision failed for user %s", telegram_id)
        user.trial_used = False
        await session.rollback()
        return TrialResult(ok=False, error="provision_failed")

    if result.requires_manual:
        order = Order(
            user_id=telegram_id,
            plan_id=plan.id,
            amount=0,
            status=OrderStatus.PAID,
            paid_at=now,
        )
        session.add(order)
        await session.flush()
        order.user = user
        order.plan = plan
        await notify_admins_manual_order(bot, order)
        await session.commit()
        return TrialResult(ok=True)

    account = await save_vpn_account(
        session,
        user_id=telegram_id,
        subscription_id=subscription.id,
        client_name=result.client_name,
        config_text=result.config_text,
        external_id=result.external_id,
        server_id=result.server_id,
    )
    await session.commit()

    trial_plan = _trial_plan(plan)
    await deliver_vpn_config(bot, telegram_id, account, trial_plan, with_split_tunnel_gift=True)
    return TrialResult(ok=True)


class _TrialOrder:
    def __init__(self, user, plan: Plan) -> None:
        self.id = 0
        self.user_id = user.telegram_id
        self.user = user
        self.plan = plan
        self.plan_id = plan.id
        self.amount = 0


def _trial_plan(plan: Plan) -> Plan:
    return Plan(
        id=plan.id,
        code="trial_1d",
        title=f"Пробный период ({settings.trial_days} дн.)",
        days=settings.trial_days,
        price_rub=0,
        stars_price=0,
        is_active=False,
    )


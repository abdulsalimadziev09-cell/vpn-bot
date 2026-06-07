import logging
from datetime import datetime, timezone

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Order, OrderStatus, Plan
from app.repositories.orders import create_order, get_order_by_id
from app.repositories.users import get_or_create_user
from app.services.subscription import activate_or_extend_subscription, mark_order_fulfilled, save_vpn_account
from app.services.vpn_delivery import deliver_vpn_config
from app.services.vpn_provisioner import get_provisioner

logger = logging.getLogger(__name__)


async def create_pending_order(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    plan: Plan,
) -> Order:
    user = await get_or_create_user(session, telegram_id, username)
    order = await create_order(session, user.telegram_id, plan)
    await session.commit()
    return order


async def mark_order_paid_from_stars(
    session: AsyncSession,
    order_id: int,
    user_id: int,
) -> Order | None:
    order = await get_order_by_id(session, order_id)
    if not order or order.user_id != user_id:
        return None

    if order.status in (OrderStatus.FULFILLED, OrderStatus.PAID):
        return order

    if order.status != OrderStatus.PENDING:
        return None

    order.status = OrderStatus.PAID
    order.paid_at = datetime.now(timezone.utc)
    await activate_or_extend_subscription(session, order.user_id, order.plan)
    await session.commit()

    return order


async def handle_paid_order_extras(session: AsyncSession, bot: Bot, order: Order) -> None:
    from app.services.referral import process_referral_bonus

    if order.status != OrderStatus.PAID:
        return
    await process_referral_bonus(session, bot, order.user_id)
    await session.commit()


async def fulfill_paid_order(session: AsyncSession, bot: Bot, order: Order) -> bool:
    if order.status != OrderStatus.PAID:
        return False

    order.provision_attempts += 1
    provisioner = get_provisioner()
    try:
        result = await provisioner.provision(order)
    except Exception:
        logger.exception("Provision failed for order %s", order.id)
        await session.commit()
        return False

    if result.requires_manual:
        await notify_admins_manual_order(bot, order)
        await session.commit()
        return False

    from app.repositories.subscriptions import get_active_subscription

    subscription = await get_active_subscription(session, order.user_id)
    if not subscription:
        subscription = await activate_or_extend_subscription(session, order.user_id, order.plan)
    account = await save_vpn_account(
        session,
        user_id=order.user_id,
        subscription_id=subscription.id,
        client_name=result.client_name,
        config_text=result.config_text,
        external_id=result.external_id,
        server_id=result.server_id,
    )
    await mark_order_fulfilled(session, order)
    await session.commit()
    await deliver_vpn_config(bot, order.user_id, account, order.plan, with_split_tunnel_gift=True)
    return True


async def approve_manual_order(
    session: AsyncSession,
    bot: Bot,
    order: Order,
    config_text: str,
) -> None:
    from app.repositories.subscriptions import get_active_subscription

    subscription = await get_active_subscription(session, order.user_id)
    if not subscription:
        subscription = await activate_or_extend_subscription(session, order.user_id, order.plan)
    from app.formatters import client_name_for_user

    account = await save_vpn_account(
        session,
        user_id=order.user_id,
        subscription_id=subscription.id,
        client_name=client_name_for_user(order.user_id),
        config_text=config_text,
    )
    await mark_order_fulfilled(session, order)
    await session.commit()
    await deliver_vpn_config(bot, order.user_id, account, order.plan, with_split_tunnel_gift=True)


async def notify_admins_manual_order(bot: Bot, order: Order) -> None:
    from app.formatters import format_order_admin

    kind = "Пробный период" if order.amount == 0 else "Оплата"
    text = (
        f"{kind}: требуется ручная выдача конфига.\n\n"
        f"{format_order_admin(order)}\n\n"
        f"Команда: /admin_approve {order.id}\n"
        "После создания клиента на VPS отправьте .conf ответом на эту команду."
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            logger.exception("Failed to notify admin %s", admin_id)

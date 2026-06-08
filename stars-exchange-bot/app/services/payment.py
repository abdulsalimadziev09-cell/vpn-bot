import logging
from decimal import Decimal

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Order, StarPackage
from app.integrations.robokassa_client import build_payment_url
from app.repositories.orders import create_order
from app.repositories.users import get_or_create_user
from app.services.pricing import normalize_username, rub_for_stars, validate_stars_amount

logger = logging.getLogger(__name__)


async def create_stars_order(
    session: AsyncSession,
    *,
    buyer_id: int,
    buyer_username: str | None,
    recipient_username: str,
    stars_amount: int,
    amount_rub: int | None = None,
    package: StarPackage | None = None,
) -> Order:
    error = validate_stars_amount(stars_amount)
    if error:
        raise ValueError(error)

    await get_or_create_user(session, buyer_id, buyer_username)
    recipient = normalize_username(recipient_username)
    rub = amount_rub if amount_rub is not None else rub_for_stars(stars_amount)

    order = await create_order(
        session,
        buyer_id=buyer_id,
        recipient_username=recipient,
        stars_amount=stars_amount,
        amount_rub=rub,
        package=package,
    )
    await session.commit()
    return order


def payment_link_for_order(order: Order) -> str:
    description = f"Telegram Stars: {order.stars_amount} ⭐ для @{order.recipient_username}"
    return build_payment_url(
        inv_id=order.robokassa_inv_id or order.id,
        amount_rub=order.amount_rub,
        description=description,
    )


async def mark_paid_from_robokassa(
    session: AsyncSession,
    *,
    inv_id: int,
    out_sum: str,
) -> Order | None:
    order = await _get_order_by_inv(session, inv_id)
    if not order:
        logger.warning("Robokassa payment for unknown InvId=%s", inv_id)
        return None

    expected = Decimal(order.amount_rub)
    received = Decimal(out_sum)
    if received != expected:
        logger.warning(
            "Robokassa amount mismatch for order %s: expected %s, got %s",
            order.id,
            expected,
            received,
        )
        return None

    from app.repositories.orders import mark_order_paid

    await mark_order_paid(session, order)
    await session.commit()
    return order


async def _get_order_by_inv(session: AsyncSession, inv_id: int) -> Order | None:
    from app.repositories.orders import get_order_by_inv_id

    return await get_order_by_inv_id(session, inv_id)


async def notify_payment_received(bot: Bot, order: Order) -> None:
    text = (
        f"✅ Оплата получена по заказу #{order.id}.\n"
        f"Отправляем {order.stars_amount} ⭐ на @{order.recipient_username}…"
    )
    try:
        await bot.send_message(order.buyer_id, text)
    except Exception:
        logger.exception("Failed to notify buyer %s about payment", order.buyer_id)

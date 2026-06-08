from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Order, OrderStatus, StarPackage


async def create_order(
    session: AsyncSession,
    *,
    buyer_id: int,
    recipient_username: str,
    stars_amount: int,
    amount_rub: int,
    package: StarPackage | None = None,
) -> Order:
    order = Order(
        buyer_id=buyer_id,
        package_id=package.id if package else None,
        recipient_username=recipient_username,
        stars_amount=stars_amount,
        amount_rub=amount_rub,
        status=OrderStatus.PENDING,
    )
    session.add(order)
    await session.flush()
    order.robokassa_inv_id = order.id
    await session.flush()
    return order


async def get_order_by_id(session: AsyncSession, order_id: int) -> Order | None:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.package), joinedload(Order.buyer))
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def get_order_by_inv_id(session: AsyncSession, inv_id: int) -> Order | None:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.package), joinedload(Order.buyer))
        .where(Order.robokassa_inv_id == inv_id)
    )
    return result.scalar_one_or_none()


async def mark_order_paid(session: AsyncSession, order: Order) -> Order:
    if order.status in (OrderStatus.PAID, OrderStatus.FULFILLED):
        return order
    if order.status != OrderStatus.PENDING:
        return order

    order.status = OrderStatus.PAID
    order.paid_at = datetime.now(timezone.utc)
    await session.flush()
    return order


async def mark_order_fulfilled(session: AsyncSession, order: Order) -> None:
    order.status = OrderStatus.FULFILLED
    order.fulfilled_at = datetime.now(timezone.utc)
    order.last_error = None
    await session.flush()


async def mark_order_failed(session: AsyncSession, order: Order, error: str) -> None:
    order.status = OrderStatus.FAILED
    order.last_error = error[:2000]
    await session.flush()


async def list_paid_unfulfilled(session: AsyncSession) -> list[Order]:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.package), joinedload(Order.buyer))
        .where(Order.status == OrderStatus.PAID)
        .order_by(Order.paid_at.asc())
    )
    return list(result.scalars().unique().all())


async def list_orders_by_status(session: AsyncSession, status: str, limit: int = 20) -> list[Order]:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.package), joinedload(Order.buyer))
        .where(Order.status == status)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().unique().all())


async def list_orders_for_buyer(session: AsyncSession, buyer_id: int, limit: int = 10) -> list[Order]:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.package), joinedload(Order.buyer))
        .where(Order.buyer_id == buyer_id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().unique().all())

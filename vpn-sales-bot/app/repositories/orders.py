from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models import Order, OrderStatus, Plan, User


async def create_order(session: AsyncSession, user_id: int, plan: Plan) -> Order:
    order = Order(
        user_id=user_id,
        plan_id=plan.id,
        amount=plan.stars_price,
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
        .options(joinedload(Order.plan), joinedload(Order.user))
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def list_orders_by_status(session: AsyncSession, status: str) -> list[Order]:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.plan), joinedload(Order.user))
        .where(Order.status == status)
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().unique().all())


async def list_paid_unfulfilled(session: AsyncSession) -> list[Order]:
    result = await session.execute(
        select(Order)
        .options(joinedload(Order.plan), joinedload(Order.user))
        .where(Order.status == OrderStatus.PAID)
        .order_by(Order.paid_at.asc())
    )
    return list(result.scalars().unique().all())

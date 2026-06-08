import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Order, OrderStatus
from app.repositories.orders import mark_order_failed, mark_order_fulfilled
from app.services.stars_delivery.base import DeliveryResult
from app.services.stars_delivery.manual import deliver_manual
from app.services.stars_delivery.telethon import deliver_via_telethon

logger = logging.getLogger(__name__)


async def fulfill_order(session: AsyncSession, bot: Bot, order: Order) -> DeliveryResult:
    if order.status != OrderStatus.PAID:
        return DeliveryResult(ok=False, error="Заказ не оплачен")

    order.delivery_attempts += 1
    await session.flush()

    if settings.stars_delivery_mode == "telethon":
        result = await deliver_via_telethon(order)
    else:
        result = await deliver_manual(bot, order)

    if result.ok:
        await mark_order_fulfilled(session, order)
        await session.commit()
        await _notify_buyer_success(bot, order, result)
        return result

    if result.requires_manual:
        await session.commit()
        return result

    order.last_error = (result.error or "unknown error")[:2000]
    if order.delivery_attempts >= 5:
        await mark_order_failed(session, order, order.last_error)
    await session.commit()
    await _notify_buyer_failure(bot, order, result.error)
    return result


async def admin_mark_fulfilled(session: AsyncSession, bot: Bot, order: Order) -> None:
    await mark_order_fulfilled(session, order)
    await session.commit()
    await _notify_buyer_success(bot, order, DeliveryResult(ok=True, delivered_stars=order.stars_amount))


async def _notify_buyer_success(bot: Bot, order: Order, result: DeliveryResult) -> None:
    stars = result.delivered_stars or order.stars_amount
    text = (
        f"🎉 Готово! {stars} ⭐ отправлены на @{order.recipient_username}.\n"
        "Проверьте баланс Stars в Telegram."
    )
    try:
        await bot.send_message(order.buyer_id, text)
    except Exception:
        logger.exception("Failed to notify buyer %s about fulfillment", order.buyer_id)


async def _notify_buyer_failure(bot: Bot, order: Order, error: str | None) -> None:
    text = (
        f"⚠️ Не удалось автоматически отправить Stars по заказу #{order.id}.\n"
        "Мы уже разбираемся — обычно это занимает до 30 минут.\n"
        f"Если долго нет ответа, напишите /support с номером заказа."
    )
    if error and settings.admin_ids:
        text += f"\n\n(тех.: {error[:200]})"
    try:
        await bot.send_message(order.buyer_id, text)
    except Exception:
        logger.exception("Failed to notify buyer %s about failure", order.buyer_id)

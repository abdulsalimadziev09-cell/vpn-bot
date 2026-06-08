import logging

from aiogram import Bot

from app.config import settings
from app.db.models import Order
from app.services.stars_delivery.base import DeliveryResult

logger = logging.getLogger(__name__)


async def deliver_manual(bot: Bot, order: Order) -> DeliveryResult:
    text = (
        "🛠 Требуется выдача Stars вручную.\n\n"
        f"Заказ #{order.id}\n"
        f"Покупатель: {order.buyer_id}\n"
        f"Получатель: @{order.recipient_username}\n"
        f"Stars: {order.stars_amount} ⭐\n"
        f"Сумма: {order.amount_rub} ₽\n\n"
        f"После выдачи: /admin_fulfill {order.id}"
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            logger.exception("Failed to notify admin %s", admin_id)
    return DeliveryResult(ok=False, requires_manual=True)

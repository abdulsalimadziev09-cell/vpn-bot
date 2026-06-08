from app.db.models import Order, StarPackage


def format_package_line(package: StarPackage) -> str:
    return f"{package.title} — {package.stars_amount} ⭐ / {package.price_rub} ₽"


def format_order_summary(order: Order) -> str:
    return (
        f"Заказ #{order.id}\n"
        f"Получатель: @{order.recipient_username}\n"
        f"Stars: {order.stars_amount} ⭐\n"
        f"К оплате: {order.amount_rub} ₽"
    )


def format_admin_order(order: Order) -> str:
    buyer_name = order.buyer.username or str(order.buyer_id)
    return (
        f"#{order.id} | {order.status}\n"
        f"Покупатель: @{buyer_name} ({order.buyer_id})\n"
        f"Получатель: @{order.recipient_username}\n"
        f"{order.stars_amount} ⭐ / {order.amount_rub} ₽"
    )

from datetime import datetime, timezone

from app.db.models import Order, Plan, Subscription, VpnAccount


def format_plan_line(plan: Plan) -> str:
    return f"{plan.title} — {plan.stars_price} ⭐ ({plan.days} дн.)"


def format_subscription_status(subscription: Subscription | None) -> str:
    if not subscription:
        return "У вас нет активной подписки."

    expires = subscription.expires_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    return (
        f"Тариф: {subscription.plan.title}\n"
        f"Статус: активна\n"
        f"Действует до: {expires}"
    )


def format_order_admin(order: Order) -> str:
    username = f"@{order.user.username}" if order.user.username else f"id {order.user.telegram_id}"
    return (
        f"Заказ #{order.id}\n"
        f"Пользователь: {username}\n"
        f"Тариф: {order.plan.title} ({order.plan.days} дн.)\n"
        f"Сумма: {order.amount} ⭐\n"
        f"Статус: {order.status}"
    )


def client_name_for_user(telegram_id: int) -> str:
    return f"tg_{telegram_id}"


def format_vpn_delivery_hint() -> str:
    return (
        "Как подключиться:\n"
        "1. Скачайте AmneziaVPN: https://amnezia.org\n"
        "2. Откройте приложение → «Импорт конфигурации»\n"
        "3. Выберите полученный .conf файл или отсканируйте QR\n"
        "4. Подключитесь к VPN"
    )

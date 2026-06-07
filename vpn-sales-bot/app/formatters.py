from datetime import datetime, timezone

from app.config import settings
from app.db.models import Order, Plan, Subscription, VpnAccount

AMNEZIA_IOS_URL = "https://apps.apple.com/by/app/amneziavpn/id1600529900"
AMNEZIA_ANDROID_URL = "https://play.google.com/store/apps/details?id=org.amnezia.vpn&hl=ru"


def subscription_days_remaining(subscription: Subscription) -> int:
    now = datetime.now(timezone.utc)
    expires = subscription.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    delta = expires - now
    return max(0, delta.days + (1 if delta.seconds > 0 else 0))


def format_plan_line(plan: Plan) -> str:
    return f"{plan.title} — {plan.stars_price} ⭐ ({plan.days} дн.)"


def format_subscription_status(subscription: Subscription | None) -> str:
    if not subscription:
        return "У вас нет активной подписки."

    days_left = subscription_days_remaining(subscription)
    expires = subscription.expires_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    days_word = _days_word(days_left)
    return (
        f"Тариф: {subscription.plan.title}\n"
        f"Статус: активна\n"
        f"Осталось: {days_left} {days_word}\n"
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


def format_download_app() -> str:
    return (
        "Скачайте AmneziaVPN:\n\n"
        f"📱 iOS: {AMNEZIA_IOS_URL}\n"
        f"🤖 Android: {AMNEZIA_ANDROID_URL}\n\n"
        "После установки импортируйте .conf или отсканируйте QR из этого бота."
    )


def format_about_service() -> str:
    return (
        "О сервисе\n\n"
        "Мы предоставляем персональный VPN на базе AmneziaWG — "
        "стабильный протокол с обфускацией для обхода блокировок.\n\n"
        "• Один ключ — один пользователь\n"
        "• Оплата через Telegram Stars\n"
        "• Конфиг и QR приходят сразу после оплаты\n"
        "• Напоминания перед окончанием подписки\n"
        f"• Бонус за друга: +{settings.referral_bonus_days} дней\n\n"
        "По вопросам — раздел «Приведи друга» или напишите администратору."
    )


def format_referral_info(bot_username: str, telegram_id: int, invited_count: int, paid_count: int) -> str:
    link = f"https://t.me/{bot_username}?start=ref{telegram_id}"
    return (
        "Приведи друга\n\n"
        f"Поделитесь ссылкой. Когда друг впервые оплатит подписку, "
        f"вы получите +{settings.referral_bonus_days} дней к своей подписке.\n\n"
        f"Ваша ссылка:\n{link}\n\n"
        f"Приглашено: {invited_count}\n"
        f"Оплатили: {paid_count}"
    )


def format_expiry_reminder(days_left: int) -> str:
    days_word = _days_word(days_left)
    return (
        f"⏳ Подписка VPN заканчивается через {days_left} {days_word}.\n"
        f"Осталось дней: {days_left}\n\n"
        "Продлите в боте: /start → Тарифы"
    )


def format_vpn_delivery_hint() -> str:
    return (
        "Как подключиться:\n"
        f"1. Скачайте AmneziaVPN на iOS: {AMNEZIA_IOS_URL}\n"
        f"2. Скачайте AmneziaVPN на Android: {AMNEZIA_ANDROID_URL}\n"
        "3. Откройте приложение → «Импорт конфигурации»\n"
        "4. Выберите полученный .conf файл или отсканируйте QR\n"
        "5. Подключитесь к VPN"
    )


def _days_word(days: int) -> str:
    if 11 <= days % 100 <= 14:
        return "дней"
    last = days % 10
    if last == 1:
        return "день"
    if 2 <= last <= 4:
        return "дня"
    return "дней"

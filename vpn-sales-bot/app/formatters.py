from datetime import datetime, timezone

from app.config import settings
from app.db.models import Order, Plan, Subscription, VpnAccount
from app.repositories.stats import AdminStats

AMNEZIAWG_IOS_URL = "https://apps.apple.com/app/amneziawg/id6478942365"
AMNEZIAWG_ANDROID_URL = "https://play.google.com/store/apps/details?id=org.amnezia.awg&hl=ru"
AMNEZIAWG_WINDOWS_URL = "https://github.com/amnezia-vpn/amneziawg-windows-client/releases"


def subscription_days_remaining(subscription: Subscription) -> int:
    now = datetime.now(timezone.utc)
    expires = subscription.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    delta = expires - now
    return max(0, delta.days + (1 if delta.seconds > 0 else 0))


def format_plan_line(plan: Plan) -> str:
    return f"{plan.title} — {plan.stars_price} ⭐ ({plan.days} дн.)"


def format_renewal_message(subscription: Subscription, plan: Plan) -> str:
    expires = subscription.expires_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    return (
        f"✅ Подписка продлена: {plan.title}.\n"
        f"Действует до: {expires}\n\n"
        "Ваш VPN-конфиг не изменился — используйте прежний .conf.\n"
        "Повторно получить конфиг: /my → «Получить конфиг»."
    )


def _stars_buy_bot_username() -> str:
    url = settings.stars_buy_bot_url.rstrip("/")
    if url.startswith("https://t.me/"):
        return "@" + url.removeprefix("https://t.me/")
    if url.startswith("@"):
        return url
    return url


def format_stars_buy_hint() -> str:
    bot = _stars_buy_bot_username()
    return (
        "Не хватает Stars на балансе?\n"
        f"Пополните в {bot} — оплата картой или СБП, Stars придут в Telegram."
    )


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
        "Скачайте клиент AmneziaWG:\n\n"
        f"📱 iOS: {AMNEZIAWG_IOS_URL}\n"
        f"🤖 Android: {AMNEZIAWG_ANDROID_URL}\n"
        f"💻 Windows: {AMNEZIAWG_WINDOWS_URL}\n\n"
        "После установки импортируйте файл .conf из этого бота "
        "(нативный формат AmneziaWG, генерирует bivlked на сервере)."
    )


def format_about_service() -> str:
    return (
        "О сервисе\n\n"
        "Мы предоставляем персональный VPN на базе AmneziaWG — "
        "стабильный протокол с обфускацией для обхода блокировок.\n\n"
        "• Один ключ — один пользователь\n"
        "• Оплата через Telegram Stars\n"
        "• Конфиг .conf (нативный AWG от сервера) приходит сразу после оплаты\n"
        "• Напоминания перед окончанием подписки\n"
        f"• Пробный период: {settings.trial_days} {_days_word(settings.trial_days)} (один раз)\n"
        f"• Бонус за друга: +{settings.referral_bonus_days} {_days_word(settings.referral_bonus_days)}\n\n"
        "По вопросам — раздел «Приведи друга» или напишите администратору."
    )


def format_referral_info(bot_username: str, telegram_id: int, invited_count: int, paid_count: int) -> str:
    link = f"https://t.me/{bot_username}?start=ref{telegram_id}"
    return (
        "Приведи друга\n\n"
        f"Поделитесь ссылкой. Когда друг впервые оплатит подписку, "
        f"вы получите +{settings.referral_bonus_days} {_days_word(settings.referral_bonus_days)} "
        "к своей подписке.\n\n"
        f"Ваша ссылка:\n{link}\n\n"
        f"Приглашено: {invited_count}\n"
        f"Оплатили: {paid_count}"
    )


def format_user_label(telegram_id: int, username: str | None) -> str:
    return f"@{username}" if username else f"id {telegram_id}"


def format_admin_subscription_line(subscription: Subscription) -> str:
    user = subscription.user
    days_left = subscription_days_remaining(subscription)
    days_word = _days_word(days_left)
    expires = subscription.expires_at.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M")
    label = format_user_label(user.telegram_id, user.username) if user else f"id {subscription.user_id}"
    trial_mark = " 🎁" if days_left <= settings.trial_days else ""
    return (
        f"{label}{trial_mark} — осталось {days_left} {days_word} — до {expires} UTC "
        f"({subscription.plan.title})"
    )


def build_admin_subscriptions_report(subscriptions: list[Subscription]) -> list[str]:
    if not subscriptions:
        return ["📊 Активных подписок нет."]

    lines = [f"📊 Активные подписки ({len(subscriptions)})\n"]
    for index, subscription in enumerate(subscriptions, start=1):
        lines.append(f"{index}. {format_admin_subscription_line(subscription)}")

    text = "\n".join(lines)
    return _split_telegram_message(text)


def _split_telegram_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}".strip() if current else line
        if len(candidate) > limit:
            if current:
                chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


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
        f"1. Скачайте AmneziaWG на iOS: {AMNEZIAWG_IOS_URL}\n"
        f"2. Скачайте AmneziaWG на Android: {AMNEZIAWG_ANDROID_URL}\n"
        f"3. Скачайте AmneziaWG на Windows: {AMNEZIAWG_WINDOWS_URL}\n"
        "4. Откройте AmneziaWG → «Импорт конфигурации»\n"
        "5. Выберите файл .conf из бота (или отсканируйте QR)\n"
        "6. Подключитесь к VPN\n\n"
        "При необходимости можно перейти по туннлю -> Править (справа сверху) -> Ниже включить АВТОПОДКЛЮЮЧЕНИЕ.\n"
        "Актуальный .conf: /my → «Получить конфиг»."
    )


def format_amneziawg_install_guide() -> str:
    return f"{format_download_app()}\n\n{format_vpn_delivery_hint()}"


def format_config_resend_broadcast_header() -> str:
    return (
        "🙏 Приносим извинения за перебои с VPN.\n\n"
        "Мы всё исправили — ниже актуальный конфиг, VPN снова работает.\n"
        "Если старый конфиг уже был в приложении — удалите его и импортируйте новый.\n" 
        "При необходимости можно перейти по туннлю -> Править (справа сверху) -> Ниже включить АВТОПОДКЛЮЮЧЕНИЕ.\n\n"
        f"{format_amneziawg_install_guide()}"
    )


def format_admin_stats(stats: AdminStats) -> str:
    return (
        "📊 Статистика\n\n"
        f"👥 Всего пользователей: {_format_int(stats.total_users)}\n"
        f"📈 За сегодня: {_format_int(stats.users_today)}\n"
        f"💳 Покупок: {_format_int(stats.purchases)}\n"
        f"⭐ Продано Stars: {_format_int(stats.stars_sold)}\n"
        f"💰 Оборот: {_format_int(stats.revenue_rub)} ₽"
    )


def _format_int(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def format_trial_period_short() -> str:
    days = settings.trial_days
    return f"{days} {_days_word(days)}"


def format_referral_bonus_short() -> str:
    days = settings.referral_bonus_days
    return f"+{days} {_days_word(days)}"


def format_welcome_trial_line() -> str:
    return f"🎁 Новым пользователям — пробный период {format_trial_period_short()}."


def format_trial_button_label() -> str:
    return f"🎁 Пробный период {format_trial_period_short()}"


def _days_word(days: int) -> str:
    if 11 <= days % 100 <= 14:
        return "дней"
    last = days % 10
    if last == 1:
        return "день"
    if 2 <= last <= 4:
        return "дня"
    return "дней"

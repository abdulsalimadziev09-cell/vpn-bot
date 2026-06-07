from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import Plan


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Заказы без конфига", callback_data="admin:orders")],
            [InlineKeyboardButton(text="Сводка подписок", callback_data="admin:subscriptions")],
            [InlineKeyboardButton(text="Назад в меню", callback_data="menu:main")],
        ]
    )


def main_menu_keyboard(*, show_trial: bool = True, is_admin: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="Тарифы", callback_data="menu:plans")],
        [InlineKeyboardButton(text="Моя подписка", callback_data="menu:my")],
    ]
    if show_trial:
        rows.append([InlineKeyboardButton(text="🎁 Пробный период 1 день", callback_data="menu:trial")])
    if is_admin:
        rows.append([InlineKeyboardButton(text="🔧 Админ", callback_data="menu:admin")])
    rows.extend(
        [
            [
                InlineKeyboardButton(text="Скачать AmneziaVPN", callback_data="menu:download"),
                InlineKeyboardButton(text="О сервисе", callback_data="menu:about"),
            ],
            [
                InlineKeyboardButton(text="Приведи друга", callback_data="menu:referral"),
                InlineKeyboardButton(text="Инструкция", callback_data="menu:help"),
            ],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def plans_keyboard(plans: list[Plan]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{plan.title} — {plan.stars_price} ⭐", callback_data=f"plan:{plan.id}")]
        for plan in plans
    ]
    rows.append([InlineKeyboardButton(text="Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_subscription_keyboard(reminders_enabled: bool = True) -> InlineKeyboardMarkup:
    reminder_label = "🔔 Напоминания: вкл" if reminders_enabled else "🔕 Напоминания: выкл"
    reminder_data = "my:reminders_off" if reminders_enabled else "my:reminders_on"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Получить конфиг", callback_data="my:config")],
            [InlineKeyboardButton(text="Продлить", callback_data="menu:plans")],
            [InlineKeyboardButton(text=reminder_label, callback_data=reminder_data)],
            [InlineKeyboardButton(text="Назад", callback_data="menu:main")],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Назад", callback_data="menu:main")]]
    )

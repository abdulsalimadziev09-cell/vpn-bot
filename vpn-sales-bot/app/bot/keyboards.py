from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import Plan


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Тарифы", callback_data="menu:plans")],
            [InlineKeyboardButton(text="Моя подписка", callback_data="menu:my")],
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

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import Plan


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Тарифы", callback_data="menu:plans")],
            [InlineKeyboardButton(text="Моя подписка", callback_data="menu:my")],
            [InlineKeyboardButton(text="Инструкция", callback_data="menu:help")],
        ]
    )


def plans_keyboard(plans: list[Plan]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{plan.title} — {plan.stars_price} ⭐", callback_data=f"plan:{plan.id}")]
        for plan in plans
    ]
    rows.append([InlineKeyboardButton(text="Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_subscription_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Получить конфиг", callback_data="my:config")],
            [InlineKeyboardButton(text="Продлить", callback_data="menu:plans")],
            [InlineKeyboardButton(text="Назад", callback_data="menu:main")],
        ]
    )

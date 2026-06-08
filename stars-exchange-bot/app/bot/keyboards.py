from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import StarPackage


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Купить Stars", callback_data="buy:menu")],
            [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders:list")],
            [InlineKeyboardButton(text="❓ Как это работает", callback_data="help:main")],
        ]
    )


def packages_keyboard(packages: list[StarPackage]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{p.stars_amount} ⭐ — {p.price_rub} ₽", callback_data=f"buy:pkg:{p.id}")]
        for p in packages
    ]
    rows.append([InlineKeyboardButton(text="✏️ Своя сумма", callback_data="buy:custom")])
    rows.append([InlineKeyboardButton(text="« Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def recipient_keyboard(buyer_username: str | None) -> InlineKeyboardMarkup:
    rows = []
    if buyer_username:
        rows.append(
            [InlineKeyboardButton(text="👤 Себе", callback_data=f"buy:recipient:self")]
        )
    rows.append([InlineKeyboardButton(text="« Отмена", callback_data="buy:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
            [InlineKeyboardButton(text="« В меню", callback_data="menu:main")],
        ]
    )

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.models import Item
from app.services.daily_review import DailyReviewContent


def item_card_keyboard(item: Item) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if item.url:
        builder.row(InlineKeyboardButton(text="Открыть", url=item.url))
    builder.row(
        InlineKeyboardButton(text="Читаю", callback_data=f"status:{item.id}:reading"),
        InlineKeyboardButton(text="Готово", callback_data=f"status:{item.id}:done"),
    )
    builder.row(
        InlineKeyboardButton(text="+ Тег", callback_data=f"tag:{item.id}"),
        InlineKeyboardButton(text="Напомнить", callback_data=f"remind_menu:{item.id}"),
    )
    builder.row(
        InlineKeyboardButton(text="В архив", callback_data=f"status:{item.id}:archived"),
        InlineKeyboardButton(text="Подробнее", callback_data=f"item:{item.id}"),
    )
    return builder.as_markup()


def daily_review_keyboard(content: DailyReviewContent) -> InlineKeyboardMarkup | None:
    builder = InlineKeyboardBuilder()
    has_button = False
    if content.spotlight_item:
        builder.row(
            InlineKeyboardButton(
                text="📚 Посмотреть из архива",
                callback_data=f"daily:show:{content.spotlight_item.id}",
            )
        )
        has_button = True
    if content.backlog_item:
        builder.row(
            InlineKeyboardButton(
                text="📥 Открыть из очереди",
                callback_data=f"daily:show:{content.backlog_item.id}",
            )
        )
        has_button = True
    if content.unread_count > 0:
        builder.row(InlineKeyboardButton(text="Инбокс", callback_data="inbox"))
        has_button = True
    return builder.as_markup() if has_button else None


def remind_keyboard(item_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Через 1ч", callback_data=f"remind:{item_id}:1h"),
        InlineKeyboardButton(text="Завтра", callback_data=f"remind:{item_id}:tomorrow"),
    )
    builder.row(
        InlineKeyboardButton(text="Через 3д", callback_data=f"remind:{item_id}:3d"),
        InlineKeyboardButton(text="Через неделю", callback_data=f"remind:{item_id}:1w"),
    )
    return builder.as_markup()


def reminder_sent_keyboard(item: Item) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if item.url:
        builder.row(InlineKeyboardButton(text="Открыть", url=item.url))
    builder.row(
        InlineKeyboardButton(text="Готово", callback_data=f"status:{item.id}:done"),
        InlineKeyboardButton(text="Отложить", callback_data=f"remind_menu:{item.id}"),
    )
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Инбокс", callback_data="inbox"),
        InlineKeyboardButton(text="Поиск", callback_data="search"),
    )
    builder.row(
        InlineKeyboardButton(text="Обзор", callback_data="daily"),
        InlineKeyboardButton(text="Теги", callback_data="tags"),
    )
    builder.row(InlineKeyboardButton(text="Список", callback_data="list"))
    return builder.as_markup()

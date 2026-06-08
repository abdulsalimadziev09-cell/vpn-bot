from app.config import settings


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids


def format_admin_help() -> str:
    return "🔧 Админ-панель"

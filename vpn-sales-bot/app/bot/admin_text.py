from app.config import settings


def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids


def format_admin_help() -> str:
    hours = settings.admin_subscription_report_hours
    return (
        "🔧 Панель администратора\n\n"
        "Команды:\n"
        "/admin — это сообщение\n"
        "/stats — пользователи, покупки, Stars и оборот\n"
        "/admin_orders — заказы без выдачи конфига (оплата и пробный период)\n"
        "/admin_approve <order_id> — выдать .conf пользователю\n"
        "/admin_subscriptions — сводка: у кого сколько дней осталось\n"
        "/admin_vpn_status — провижинер и SSH-настройки\n"
        "/admin_vpn_add [имя] — тест: создать клиента на VPS и получить .conf\n"
        "/admin_vpn_remove [имя] — тест: удалить клиента с VPS\n\n"
        "Тест VPN (кнопки в меню /admin):\n"
        "• «🧪 Тест: выдать конфиг» — клиент adm<ваш_id>, конфиг придёт сюда\n"
        "• «🧪 Тест: удалить» — удалить того же клиента\n"
        "• Своё имя: /admin_vpn_add test_bot\n\n"
        "Автоматически:\n"
        f"• каждые {hours} ч — сводка по активным подпискам\n"
        "• при новой оплате / пробном периоде — уведомление о выдаче конфига\n\n"
        "Выдача конфига (manual):\n"
        "1. Создайте клиента на VPS: tg_<telegram_id>\n"
        "2. /admin_approve <order_id>\n"
        "3. Отправьте .conf текстом или файлом"
    )

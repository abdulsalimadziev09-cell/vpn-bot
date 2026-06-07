import json
import logging
from functools import lru_cache
from pathlib import Path

from aiogram import Bot
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)

SITES_FILENAME = "amnezia_sites.json"


def _candidate_paths() -> list[Path]:
    app_dir = Path(__file__).resolve().parent.parent
    return [
        app_dir / "data" / SITES_FILENAME,
        app_dir.parent / SITES_FILENAME,
    ]


def split_tunnel_sites_path() -> Path:
    for path in _candidate_paths():
        if path.is_file():
            return path
    raise FileNotFoundError(f"{SITES_FILENAME} not found")


@lru_cache(maxsize=1)
def split_tunnel_sites_count() -> int:
    with split_tunnel_sites_path().open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"{SITES_FILENAME} must be a JSON array")
    return len(data)


def format_split_tunnel_gift() -> str:
    count = split_tunnel_sites_count()
    return (
        "🎁 Подарок: список сайтов для раздельного туннелирования\n\n"
        "После подключения VPN настройте маршрутизацию — VPN будет работать "
        "только для нужных ресурсов, остальной трафик пойдёт напрямую.\n\n"
        "В AmneziaVPN:\n"
        "1. Откройте подключение → ⚙️ настройки\n"
        "2. Раздельное туннелирование → По сайтам\n"
        "3. «Только перечисленные сайты доступны через VPN»\n"
        "4. Импорт → «Заменить список сайтов»\n"
        f"5. Выберите файл {SITES_FILENAME} из этого чата\n\n"
        f"В файле {count} адресов и подсетей (формат Amnezia)."
    )


async def send_split_tunnel_gift(bot: Bot, telegram_id: int, *, include_intro: bool = True) -> None:
    try:
        path = split_tunnel_sites_path()
        sites_count = split_tunnel_sites_count()
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        logger.exception("Split tunnel sites file is missing or invalid")
        await bot.send_message(
            telegram_id,
            "Список для туннелирования временно недоступен. Напишите администратору.",
        )
        return

    if include_intro:
        await bot.send_message(telegram_id, format_split_tunnel_gift())
    sites_file = BufferedInputFile(path.read_bytes(), filename=SITES_FILENAME)
    await bot.send_document(
        telegram_id,
        sites_file,
        caption=f"Список для раздельного туннелирования ({sites_count} записей)",
    )

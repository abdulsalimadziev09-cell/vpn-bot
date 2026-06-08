import math

from app.config import settings


def rub_for_stars(stars: int) -> int:
    return max(1, math.ceil(stars * settings.stars_rub_rate))


def validate_stars_amount(stars: int) -> str | None:
    if stars < settings.min_stars:
        return f"Минимум {settings.min_stars} ⭐"
    if stars > settings.max_stars:
        return f"Максимум {settings.max_stars} ⭐"
    return None


def normalize_username(value: str) -> str:
    username = value.strip().lstrip("@").lower()
    if not username:
        raise ValueError("empty username")
    if not username.replace("_", "").isalnum():
        raise ValueError("invalid username")
    return username

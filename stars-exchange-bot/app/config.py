from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = "test-token"
    database_url: str = "postgresql+asyncpg://starsbot:starsbot@localhost:5432/starsbot"
    admin_ids: list[int] = []

    http_host: str = "0.0.0.0"
    http_port: int = 8081
    public_base_url: str = "http://localhost:8081"

    robokassa_merchant_login: str = ""
    robokassa_password1: str = ""
    robokassa_password2: str = ""
    robokassa_test_mode: bool = True

    stars_rub_rate: float = 1.65
    min_stars: int = 50
    max_stars: int = 10000

    stars_delivery_mode: str = "manual"
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telethon_session_path: str = "./data/telethon.session"

    fulfillment_retry_minutes: int = 5

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: str | int | list[int] | None) -> list[int]:
        if value is None:
            return []
        if isinstance(value, int):
            return [value]
        if isinstance(value, str):
            if not value.strip():
                return []
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return list(value)


settings = Settings()

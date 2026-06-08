from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    database_url: str = "postgresql+asyncpg://savebot:savebot@localhost:5432/savebot"
    whisper_api_key: str = ""
    whisper_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    reminder_poll_seconds: int = 30
    free_item_limit: int = 100
    pro_item_limit: int = 5000
    pro_stars_price: int = 50
    pro_days: int = 30
    max_voice_duration_seconds: int = 120
    payments_enabled: bool = True
    digest_day_of_week: str = "sun"
    digest_hour: int = 7
    daily_review_hour: int = 5


settings = Settings()

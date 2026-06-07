from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = "test-token"
    database_url: str = "postgresql+asyncpg://vpnbot:vpnbot@localhost:5432/vpnbot"
    admin_ids: list[int] = []

    payments_enabled: bool = True
    http_host: str = "0.0.0.0"
    http_port: int = 8080

    vpn_provisioner: str = "manual"
    ssh_host: str = ""
    ssh_port: int = 22
    ssh_user: str = ""
    ssh_key_path: str = ""
    ssh_add_client_script: str = "/opt/awg/amneziawg-install.sh"
    ssh_config_dir: str = "/root"

    amnezia_api_url: str = ""
    amnezia_api_key: str = ""

    referral_bonus_days: int = 7
    trial_days: int = 1

    expiry_check_hours: int = 6
    expire_poll_minutes: int = 60
    retry_fulfillment_minutes: int = 15

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

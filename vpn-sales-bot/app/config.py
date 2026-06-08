from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = "test-token"
    database_url: str = "postgresql+asyncpg://vpnbot:vpnbot@localhost:5432/vpnbot"
    admin_ids: list[int] = []

    payments_enabled: bool = True
    mini_app_url: str = ""
    stars_buy_bot_url: str = "https://t.me/nexussstarsbot"
    http_host: str = "0.0.0.0"
    http_port: int = 8080

    vpn_provisioner: str = "manual"
    ssh_host: str = ""
    ssh_port: int = 22
    ssh_user: str = ""
    ssh_password: str = ""
    ssh_key_path: str = ""
    ssh_add_client_script: str = "/opt/awg/amneziawg-install.sh"
    ssh_add_client_args: str = "--add-client"
    ssh_remove_client_args: str = "--remove-client"
    ssh_config_dir: str = "/root"
    ssh_awg_server_conf: str = "/etc/amnezia/amneziawg/awg0.conf"
    ssh_merge_server_awg_params: bool = True

    amnezia_api_url: str = ""
    amnezia_api_key: str = ""
    amnezia_host: str = ""
    amnezia_dns1: str = "1.1.1.1"
    amnezia_dns2: str = "1.0.0.1"
    amnezia_description: str = "VPN"
    amnezia_mtu: str = "1280"
    amnezia_expected_port: int = 0
    amnezia_awg_i1: str = ""
    amnezia_awg_i2: str = ""
    amnezia_awg_i3: str = ""
    amnezia_awg_i4: str = ""
    amnezia_awg_i5: str = ""
    amnezia_awg_jc: str = ""
    amnezia_awg_jmin: str = ""
    amnezia_awg_jmax: str = ""
    amnezia_awg_s1: str = ""
    amnezia_awg_s2: str = ""
    amnezia_awg_s3: str = ""
    amnezia_awg_s4: str = ""
    amnezia_awg_h1: str = ""
    amnezia_awg_h2: str = ""
    amnezia_awg_h3: str = ""
    amnezia_awg_h4: str = ""

    referral_bonus_days: int = 3
    trial_days: int = 7

    expiry_check_hours: int = 6
    expire_poll_minutes: int = 60
    retry_fulfillment_minutes: int = 15

    admin_subscription_report_enabled: bool = True
    admin_subscription_report_hours: int = 12

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

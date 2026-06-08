import re

from app.config import settings
from app.services.awg_conf import format_awg_diagnostic
from app.services.vpn_provisioner import provision_vpn_client, revoke_vpn_client

_CLIENT_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")


def default_admin_test_client_name(admin_id: int) -> str:
    return f"adm{admin_id}"


def parse_admin_test_client_name(admin_id: int, raw_name: str | None) -> str | None:
    if not raw_name:
        return default_admin_test_client_name(admin_id)
    if not _CLIENT_NAME_RE.fullmatch(raw_name):
        return None
    return raw_name


def format_admin_vpn_status() -> str:
    expected_port = (
        f"{settings.amnezia_expected_port}"
        if settings.amnezia_expected_port
        else "не задан (AMNEZIA_EXPECTED_PORT)"
    )
    return (
        f"Провижинер: {settings.vpn_provisioner}\n"
        f"SSH: {settings.ssh_user}@{settings.ssh_host}:{settings.ssh_port}\n"
        f"Скрипт: {settings.ssh_add_client_script} {settings.ssh_add_client_args}\n"
        f"Каталог конфигов: {settings.ssh_config_dir}\n"
        f"Серверный AWG conf: {settings.ssh_awg_server_conf}\n"
        f"Ожидаемый порт рабочего VPN: {expected_port}"
    )


def format_provision_diagnostic(config_text: str) -> str:
    return format_awg_diagnostic(config_text, expected_port=settings.amnezia_expected_port)


async def admin_test_provision(client_name: str):
    return await provision_vpn_client(client_name)


async def admin_test_revoke(client_name: str) -> None:
    await revoke_vpn_client(client_name)

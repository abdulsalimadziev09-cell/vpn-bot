import re

from app.config import settings
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
    return (
        f"Провижинер: {settings.vpn_provisioner}\n"
        f"SSH: {settings.ssh_user}@{settings.ssh_host}:{settings.ssh_port}\n"
        f"Скрипт: {settings.ssh_add_client_script}\n"
        f"Каталог конфигов: {settings.ssh_config_dir}"
    )


async def admin_test_provision(client_name: str):
    return await provision_vpn_client(client_name)


async def admin_test_revoke(client_name: str) -> None:
    await revoke_vpn_client(client_name)

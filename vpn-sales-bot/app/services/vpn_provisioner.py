from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncssh

from app.config import settings
from app.db.models import Order
from app.formatters import client_name_for_user
from app.integrations.amnezia_api import AmneziaApiClient


@dataclass
class ProvisionResult:
    client_name: str
    config_text: str
    external_id: str | None = None
    server_id: int | None = None
    requires_manual: bool = False


class VpnProvisioner(ABC):
    @abstractmethod
    async def provision(self, order: Order) -> ProvisionResult:
        raise NotImplementedError

    @abstractmethod
    async def revoke(self, external_id: str | None, client_name: str) -> None:
        raise NotImplementedError


class ManualProvisioner(VpnProvisioner):
    async def provision(self, order: Order) -> ProvisionResult:
        client_name = client_name_for_user(order.user_id)
        return ProvisionResult(
            client_name=client_name,
            config_text="",
            requires_manual=True,
        )

    async def revoke(self, external_id: str | None, client_name: str) -> None:
        return None


class SshScriptProvisioner(VpnProvisioner):
    async def provision(self, order: Order) -> ProvisionResult:
        client_name = client_name_for_user(order.user_id)
        config_text = await self._run_add_client(client_name)
        return ProvisionResult(client_name=client_name, config_text=config_text)

    async def revoke(self, external_id: str | None, client_name: str) -> None:
        await self._run_remove_client(client_name)

    async def _connect(self) -> asyncssh.SSHClientConnection:
        return await asyncssh.connect(
            settings.ssh_host,
            port=settings.ssh_port,
            username=settings.ssh_user,
            client_keys=[settings.ssh_key_path] if settings.ssh_key_path else None,
            known_hosts=None,
        )

    async def _run_add_client(self, client_name: str) -> str:
        script = settings.ssh_add_client_script
        config_dir = settings.ssh_config_dir.rstrip("/")
        async with await self._connect() as conn:
            result = await conn.run(f"sudo {script} --add-client {client_name}", check=True)
            if result.stderr:
                pass
            config_path = f"{config_dir}/awg0-client-{client_name}.conf"
            read_result = await conn.run(f"sudo cat {config_path}", check=True)
        return read_result.stdout

    async def _run_remove_client(self, client_name: str) -> None:
        script = settings.ssh_add_client_script
        async with await self._connect() as conn:
            await conn.run(f"sudo {script} --remove-client {client_name}", check=False)


class AmneziaApiProvisioner(VpnProvisioner):
    def __init__(self) -> None:
        self.client = AmneziaApiClient()

    async def provision(self, order: Order) -> ProvisionResult:
        client_name = client_name_for_user(order.user_id)
        info = await self.client.create_user(client_name)
        return ProvisionResult(
            client_name=client_name,
            config_text=info.config_text,
            external_id=info.external_id,
        )

    async def revoke(self, external_id: str | None, client_name: str) -> None:
        if external_id:
            await self.client.delete_user(external_id)


def get_provisioner() -> VpnProvisioner:
    mapping: dict[str, type[VpnProvisioner]] = {
        "manual": ManualProvisioner,
        "ssh": SshScriptProvisioner,
        "amnezia_api": AmneziaApiProvisioner,
    }
    provisioner_cls = mapping.get(settings.vpn_provisioner, ManualProvisioner)
    return provisioner_cls()

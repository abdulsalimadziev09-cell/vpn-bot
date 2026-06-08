from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncssh

from app.config import settings
from app.db.models import Order
from app.formatters import client_name_for_user
from app.integrations.amnezia_api import AmneziaApiClient
from app.services.awg_conf import merge_interface_params, parse_interface_params


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
    async def provision_client(self, client_name: str) -> ProvisionResult:
        raise NotImplementedError

    @abstractmethod
    async def revoke(self, external_id: str | None, client_name: str) -> None:
        raise NotImplementedError


class ManualProvisioner(VpnProvisioner):
    async def provision(self, order: Order) -> ProvisionResult:
        return await self.provision_client(client_name_for_user(order.user_id))

    async def provision_client(self, client_name: str) -> ProvisionResult:
        return ProvisionResult(
            client_name=client_name,
            config_text="",
            requires_manual=True,
        )

    async def revoke(self, external_id: str | None, client_name: str) -> None:
        return None


class SshScriptProvisioner(VpnProvisioner):
    async def provision(self, order: Order) -> ProvisionResult:
        return await self.provision_client(client_name_for_user(order.user_id))

    async def provision_client(self, client_name: str) -> ProvisionResult:
        config_text = await self._run_add_client(client_name)
        config_text = await self._enrich_client_config(config_text)
        return ProvisionResult(client_name=client_name, config_text=config_text)

    async def revoke(self, external_id: str | None, client_name: str) -> None:
        await self._run_remove_client(client_name)

    async def _connect(self) -> asyncssh.SSHClientConnection:
        connect_kwargs: dict = {
            "host": settings.ssh_host,
            "port": settings.ssh_port,
            "username": settings.ssh_user,
            "known_hosts": None,
        }
        if settings.ssh_password:
            connect_kwargs["password"] = settings.ssh_password
        if settings.ssh_key_path:
            connect_kwargs["client_keys"] = [settings.ssh_key_path]
        return await asyncssh.connect(**connect_kwargs)

    async def _run_add_client(self, client_name: str) -> str:
        script = settings.ssh_add_client_script
        config_dir = settings.ssh_config_dir.rstrip("/")
        config_path = f"{config_dir}/awg0-client-{client_name}.conf"
        add_args = settings.ssh_add_client_args.strip()
        async with await self._connect() as conn:
            result = await conn.run(f"sudo {script} {add_args} {client_name}", check=True)
            config_path = _resolve_config_path(result.stdout, config_path, client_name, config_dir)
            read_result = await conn.run(f"sudo cat {config_path}", check=True)
        return read_result.stdout

    async def _run_remove_client(self, client_name: str) -> None:
        script = settings.ssh_add_client_script
        remove_args = settings.ssh_remove_client_args.strip()
        async with await self._connect() as conn:
            await conn.run(f"sudo {script} {remove_args} {client_name}", check=False)

    async def _enrich_client_config(self, config_text: str) -> str:
        template = _awg_template_from_settings()
        if settings.ssh_merge_server_awg_params:
            server_template = await self._fetch_server_template()
            template = {**server_template, **template}
        return merge_interface_params(config_text, template)

    async def _fetch_server_template(self) -> dict[str, str]:
        server_conf = settings.ssh_awg_server_conf.strip()
        if not server_conf:
            return {}
        try:
            async with await self._connect() as conn:
                result = await conn.run(f"sudo cat {server_conf}", check=False)
            if result.exit_status != 0 or not result.stdout:
                return {}
            return parse_interface_params(result.stdout)
        except Exception:
            return {}


class AmneziaApiProvisioner(VpnProvisioner):
    def __init__(self) -> None:
        self.client = AmneziaApiClient()

    async def provision(self, order: Order) -> ProvisionResult:
        return await self.provision_client(client_name_for_user(order.user_id))

    async def provision_client(self, client_name: str) -> ProvisionResult:
        info = await self.client.create_user(client_name)
        return ProvisionResult(
            client_name=client_name,
            config_text=info.config_text,
            external_id=info.external_id,
        )

    async def revoke(self, external_id: str | None, client_name: str) -> None:
        if external_id:
            await self.client.delete_user(external_id)


def _awg_template_from_settings() -> dict[str, str]:
    mapping = {
        "I1": settings.amnezia_awg_i1,
        "Jc": settings.amnezia_awg_jc,
        "Jmin": settings.amnezia_awg_jmin,
        "Jmax": settings.amnezia_awg_jmax,
        "S1": settings.amnezia_awg_s1,
        "S2": settings.amnezia_awg_s2,
        "S3": settings.amnezia_awg_s3,
        "S4": settings.amnezia_awg_s4,
        "H1": settings.amnezia_awg_h1,
        "H2": settings.amnezia_awg_h2,
        "H3": settings.amnezia_awg_h3,
        "H4": settings.amnezia_awg_h4,
    }
    return {key: value.strip() for key, value in mapping.items() if value.strip()}


def _resolve_config_path(
    stdout: str | None,
    fallback: str,
    client_name: str,
    config_dir: str,
) -> str:
    if stdout:
        for line in stdout.splitlines():
            candidate = line.strip()
            if candidate.endswith(".conf"):
                return candidate
    for candidate in (
        fallback,
        f"{config_dir}/awg0-client-{client_name}.conf",
        f"{config_dir}/{client_name}.conf",
    ):
        if candidate:
            return candidate
    return fallback


def get_provisioner() -> VpnProvisioner:
    mapping: dict[str, type[VpnProvisioner]] = {
        "manual": ManualProvisioner,
        "ssh": SshScriptProvisioner,
        "amnezia_api": AmneziaApiProvisioner,
    }
    provisioner_cls = mapping.get(settings.vpn_provisioner, ManualProvisioner)
    return provisioner_cls()


async def provision_vpn_client(client_name: str) -> ProvisionResult:
    return await get_provisioner().provision_client(client_name)


async def revoke_vpn_client(client_name: str) -> None:
    await get_provisioner().revoke(None, client_name)

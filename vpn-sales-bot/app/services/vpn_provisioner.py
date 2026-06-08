from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncssh

from app.config import settings
from app.db.models import Order
from app.formatters import client_name_for_user
from app.integrations.amnezia_api import AmneziaApiClient
from app.services.awg_conf import apply_awg_enrichment, parse_interface_params


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

    async def refresh_client_config(self, client_name: str) -> str:
        async with await self._connect() as conn:
            await self._apply_keepalive_and_regen(conn, client_name)
            return await self._read_client_config(conn, client_name)

    async def _run_add_client(self, client_name: str) -> str:
        config_dir = settings.ssh_config_dir.rstrip("/")
        command = _ssh_management_command(
            settings.ssh_add_client_script,
            settings.ssh_add_client_args,
            client_name,
        )
        async with await self._connect() as conn:
            result = await conn.run(command, check=True)
            await self._apply_keepalive_and_regen(conn, client_name)
            return await self._read_client_config(
                conn,
                client_name,
                stdout=result.stdout,
            )

    async def _apply_keepalive_and_regen(
        self,
        conn: asyncssh.SSHClientConnection,
        client_name: str,
    ) -> None:
        if settings.ssh_awg_persistent_keepalive <= 0:
            return
        keepalive = settings.ssh_awg_persistent_keepalive
        modify_command = _ssh_management_command(
            settings.ssh_add_client_script,
            f"modify PersistentKeepalive {keepalive}",
            client_name,
        )
        regen_command = _ssh_management_command(
            settings.ssh_add_client_script,
            "regen",
            client_name,
        )
        await conn.run(modify_command, check=False)
        await conn.run(regen_command, check=False)

    async def _read_client_config(
        self,
        conn: asyncssh.SSHClientConnection,
        client_name: str,
        *,
        stdout: str | None = None,
    ) -> str:
        config_dir = settings.ssh_config_dir.rstrip("/")
        for artifact_path in _client_artifact_paths(
            client_name,
            config_dir,
            stdout=stdout,
        ):
            read_result = await conn.run(f"sudo cat {artifact_path}", check=False)
            if read_result.exit_status == 0 and read_result.stdout.strip():
                return read_result.stdout.strip()
        raise RuntimeError(f"Client config not found for {client_name} in {config_dir}")

    async def _run_remove_client(self, client_name: str) -> None:
        command = _ssh_management_command(
            settings.ssh_add_client_script,
            settings.ssh_remove_client_args,
            client_name,
        )
        async with await self._connect() as conn:
            await conn.run(command, check=False)

    async def _enrich_client_config(self, config_text: str) -> str:
        if is_vpn_uri(config_text) or settings.vpn_skip_awg_enrichment:
            return config_text
        server_template: dict[str, str] = {}
        if settings.ssh_merge_server_awg_params:
            server_template = await self._fetch_server_template()
        return apply_awg_enrichment(config_text, server_template or None)

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


def is_vpn_uri(config_text: str) -> bool:
    return config_text.strip().startswith("vpn://")


def _ssh_management_command(script: str, args: str, client_name: str) -> str:
    args = args.strip()
    if settings.ssh_invoke_with_bash:
        return f"sudo bash {script} {args} {client_name}"
    return f"sudo {script} {args} {client_name}"


def _client_artifact_paths(
    client_name: str,
    config_dir: str,
    *,
    stdout: str | None = None,
) -> list[str]:
    paths: list[str] = []
    if stdout:
        for line in stdout.splitlines():
            candidate = line.strip()
            if candidate.endswith((".vpnuri", ".vpn", ".conf")):
                paths.append(candidate)

    paths.extend(
        [
            f"{config_dir}/{client_name}.vpnuri",
            f"{config_dir}/{client_name}.vpn",
            f"{config_dir}/awg0-client-{client_name}.conf",
            f"{config_dir}/{client_name}.conf",
        ]
    )

    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        if path and path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def _resolve_config_path(
    stdout: str | None,
    fallback: str,
    client_name: str,
    config_dir: str,
) -> str:
    paths = _client_artifact_paths(client_name, config_dir, stdout=stdout)
    if paths:
        return paths[0]
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


async def refresh_vpn_client_config(client_name: str) -> str | None:
    provisioner = get_provisioner()
    if not isinstance(provisioner, SshScriptProvisioner):
        return None
    return await provisioner.refresh_client_config(client_name)

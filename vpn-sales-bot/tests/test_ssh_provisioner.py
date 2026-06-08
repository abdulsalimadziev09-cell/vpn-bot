from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.services.vpn_provisioner import (
    SshScriptProvisioner,
    _client_artifact_paths,
    _ssh_management_command,
    is_vpn_uri,
)


@pytest.mark.asyncio
async def test_ssh_connect_uses_password(monkeypatch):
    monkeypatch.setattr(settings, "ssh_host", "10.0.0.1")
    monkeypatch.setattr(settings, "ssh_port", 22)
    monkeypatch.setattr(settings, "ssh_user", "root")
    monkeypatch.setattr(settings, "ssh_password", "secret")
    monkeypatch.setattr(settings, "ssh_key_path", "")

    provisioner = SshScriptProvisioner()
    with patch("app.services.vpn_provisioner.asyncssh.connect", new_callable=AsyncMock) as connect:
        await provisioner._connect()

    connect.assert_awaited_once_with(
        host="10.0.0.1",
        port=22,
        username="root",
        known_hosts=None,
        password="secret",
    )


def test_ssh_management_command_uses_bash(monkeypatch):
    monkeypatch.setattr(settings, "ssh_invoke_with_bash", True)
    command = _ssh_management_command("/root/awg/manage_amneziawg.sh", "add", "tg_1")
    assert command == "sudo bash /root/awg/manage_amneziawg.sh add tg_1"


def test_client_artifact_paths_prefers_vpnuri():
    paths = _client_artifact_paths(
        "tg_1",
        "/root/awg",
        stdout="/root/awg/tg_1.conf\n",
    )
    assert paths[0] == "/root/awg/tg_1.conf"
    assert "/root/awg/tg_1.vpnuri" in paths


@pytest.mark.asyncio
async def test_run_add_client_reads_vpnuri_first(monkeypatch):
    monkeypatch.setattr(settings, "ssh_config_dir", "/root/awg")
    monkeypatch.setattr(settings, "ssh_add_client_script", "/root/awg/manage_amneziawg.sh")
    monkeypatch.setattr(settings, "ssh_add_client_args", "add")
    monkeypatch.setattr(settings, "vpn_skip_awg_enrichment", True)

    provisioner = SshScriptProvisioner()

    conn = AsyncMock()
    conn.run = AsyncMock(
        side_effect=[
            MagicMock(exit_status=0, stdout="/root/awg/tg_1.vpnuri\n"),
            MagicMock(exit_status=0, stdout="vpn://AAATEST\n"),
        ]
    )
    connect_cm = MagicMock()
    connect_cm.__aenter__ = AsyncMock(return_value=conn)
    connect_cm.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "app.services.vpn_provisioner.asyncssh.connect",
        new_callable=AsyncMock,
        return_value=connect_cm,
    ):
        config_text = await provisioner._run_add_client("tg_1")

    assert config_text == "vpn://AAATEST"
    assert conn.run.await_args_list[0].args[0] == "sudo bash /root/awg/manage_amneziawg.sh add tg_1"
    assert conn.run.await_args_list[1].args[0] == "sudo cat /root/awg/tg_1.vpnuri"


def test_is_vpn_uri():
    assert is_vpn_uri("vpn://AAATEST")
    assert not is_vpn_uri("[Interface]\nPrivateKey = x")

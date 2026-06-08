from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings
from app.services.vpn_provisioner import SshScriptProvisioner


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

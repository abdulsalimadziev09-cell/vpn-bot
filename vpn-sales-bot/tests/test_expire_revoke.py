from unittest.mock import AsyncMock, patch

import pytest

from app.services.vpn_provisioner import AmneziaApiProvisioner, ManualProvisioner


@pytest.mark.asyncio
async def test_manual_revoke_is_noop():
    provisioner = ManualProvisioner()
    await provisioner.revoke("ext-1", "tg_100")


@pytest.mark.asyncio
async def test_amnezia_revoke_calls_api():
    provisioner = AmneziaApiProvisioner()
    provisioner.client = AsyncMock()
    await provisioner.revoke("user-42", "tg_100")
    provisioner.client.delete_user.assert_awaited_once_with("user-42")

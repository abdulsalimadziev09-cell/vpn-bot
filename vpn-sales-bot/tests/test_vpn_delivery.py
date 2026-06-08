import json
from unittest.mock import AsyncMock

import pytest

from app.services.amnezia_export import conf_to_vpn_uri
from app.services.vpn_delivery import _build_amneziawg_json, send_vpn_config_files

SAMPLE_CONF = """[Interface]
PrivateKey = w+/FRUgl07Ozta/jjMu+lTYREpPxHaM+zpDGy6W4+wY=
Address = 10.8.1.3/32
DNS = 1.1.1.1, 1.0.0.1

[Peer]
PublicKey = bPojFUDaXFty60Y/5Y45ycvI4lFn4vRvTsM/bCVZ2T4=
AllowedIPs = 0.0.0.0/0
Endpoint = 89.169.53.7:47661
PersistentKeepalive = 25
"""


def test_build_amneziawg_json_from_vpn_uri() -> None:
    vpn_uri = conf_to_vpn_uri(SAMPLE_CONF, host_name="89.169.53.7")
    json_text = _build_amneziawg_json(vpn_uri)
    assert json_text is not None
    profile = json.loads(json_text)
    assert profile["defaultContainer"] == "amnezia-awg2"


@pytest.mark.asyncio
async def test_send_vpn_config_files_sends_json_document() -> None:
    vpn_uri = conf_to_vpn_uri(SAMPLE_CONF, host_name="89.169.53.7")
    bot = AsyncMock()
    await send_vpn_config_files(bot, 101, "tg_101", vpn_uri)

    bot.send_document.assert_awaited_once()
    document = bot.send_document.await_args.args[1]
    assert document.filename == "tg_101.json"
    profile = json.loads(document.data.decode("utf-8"))
    assert profile["defaultContainer"] == "amnezia-awg2"

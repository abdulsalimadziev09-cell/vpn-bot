from unittest.mock import AsyncMock

import pytest

from app.services.amnezia_export import conf_to_vpn_uri
from app.services.vpn_delivery import _build_amneziawg_conf, send_vpn_config_files

SAMPLE_CONF = """[Interface]
PrivateKey = w+/FRUgl07Ozta/jjMu+lTYREpPxHaM+zpDGy6W4+wY=
Address = 10.8.1.3/32
DNS = 1.1.1.1, 1.0.0.1
Jc = 5
I2 = 
I3 = 

[Peer]
PublicKey = bPojFUDaXFty60Y/5Y45ycvI4lFn4vRvTsM/bCVZ2T4=
AllowedIPs = 0.0.0.0/0
Endpoint = 89.169.53.7:47661
PersistentKeepalive = 25
"""


def test_build_amneziawg_conf_from_vpn_uri() -> None:
    vpn_uri = conf_to_vpn_uri(SAMPLE_CONF, host_name="89.169.53.7")
    conf_text = _build_amneziawg_conf(vpn_uri)
    assert conf_text is not None
    assert conf_text.startswith("[Interface]")
    assert "Endpoint = 89.169.53.7:47661" in conf_text


def test_build_amneziawg_conf_sanitizes_empty_fields() -> None:
    conf_text = _build_amneziawg_conf(SAMPLE_CONF)
    assert conf_text is not None
    assert "I2 =" not in conf_text
    assert "I3 =" not in conf_text
    assert "[Interface]" in conf_text
    assert "Endpoint = 89.169.53.7:47661" in conf_text


@pytest.mark.asyncio
async def test_send_vpn_config_files_sends_conf_document() -> None:
    bot = AsyncMock()
    await send_vpn_config_files(bot, 101, "tg_101", SAMPLE_CONF)

    bot.send_document.assert_awaited_once()
    document = bot.send_document.await_args.args[1]
    assert document.filename == "tg_101.conf"
    assert document.data.decode("utf-8").startswith("[Interface]")
    bot.send_photo.assert_awaited_once()

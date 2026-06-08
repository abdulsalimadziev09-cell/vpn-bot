from app.services.vpn_admin_test import (
    default_admin_test_client_name,
    parse_admin_test_client_name,
)
from app.services.vpn_provisioner import _resolve_config_path


def test_default_admin_test_client_name():
    assert default_admin_test_client_name(5200738946) == "adm5200738946"


def test_parse_admin_test_client_name_default():
    assert parse_admin_test_client_name(42, None) == "adm42"


def test_parse_admin_test_client_name_custom():
    assert parse_admin_test_client_name(42, "test_bot") == "test_bot"


def test_parse_admin_test_client_name_invalid():
    assert parse_admin_test_client_name(42, "bad name!") is None


def test_resolve_config_path_from_stdout():
    stdout = "/root/awg/test_bot.vpnuri\n"
    fallback = "/root/awg/test_bot.conf"
    assert (
        _resolve_config_path(stdout, fallback, "test_bot", "/root/awg")
        == stdout.strip()
    )


def test_resolve_config_path_fallback():
    assert (
        _resolve_config_path("", "/root/awg0-client-x.conf", "x", "/root/awg")
        == "/root/awg/x.vpnuri"
    )

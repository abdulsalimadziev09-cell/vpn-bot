from app.services.awg_conf import diagnose_awg_conf, format_awg_diagnostic, merge_interface_params

SAMPLE_CONF = """[Interface]
PrivateKey = test-private-key-base64=
Address = 10.66.66.6/32
Jc = 8

[Peer]
PublicKey = test-server-pubkey-base64=
Endpoint = 89.169.53.7:62205
AllowedIPs = 0.0.0.0/0
"""


def test_merge_interface_params_adds_missing_i1() -> None:
    merged = merge_interface_params(SAMPLE_CONF, {"I1": "<r 2><b 0xabc>", "Jc": "5"})
    assert "I1 = <r 2><b 0xabc>" in merged
    assert "Jc = 8" in merged


def test_diagnose_awg_conf_detects_missing_i1() -> None:
    info = diagnose_awg_conf(SAMPLE_CONF)
    assert info["port"] == "62205"
    assert info["subnet"] == "10.66.66.0"
    assert info["has_i1"] is False


def test_format_awg_diagnostic_warns_on_port_mismatch() -> None:
    text = format_awg_diagnostic(SAMPLE_CONF, expected_port=47661)
    assert "62205" in text
    assert "47661" in text

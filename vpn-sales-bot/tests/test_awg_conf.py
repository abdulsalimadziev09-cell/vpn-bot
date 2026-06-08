from app.config import settings
from app.services.awg_conf import (
    apply_awg_enrichment,
    diagnose_awg_conf,
    format_awg_diagnostic,
    merge_interface_params,
    render_wireguard_conf,
)

SAMPLE_CONF = """[Interface]
PrivateKey = test-private-key-base64=
Address = 10.66.66.6/32
Jc = 8

[Peer]
PublicKey = test-server-pubkey-base64=
Endpoint = 89.169.53.7:62205
AllowedIPs = 0.0.0.0/0
"""


def test_apply_awg_enrichment_adds_default_i1() -> None:
    merged = apply_awg_enrichment(SAMPLE_CONF)
    assert "I1 = <r 2><b" in merged
    assert diagnose_awg_conf(SAMPLE_CONF)["has_i1"] is True


def test_apply_awg_enrichment_uses_env_i1(monkeypatch) -> None:
    monkeypatch.setattr(settings, "amnezia_awg_i1", "<r 2><b 0xcustom>")
    merged = apply_awg_enrichment(SAMPLE_CONF)
    assert "I1 = <r 2><b 0xcustom>" in merged


def test_merge_interface_params_preserves_peer() -> None:
    merged = merge_interface_params(SAMPLE_CONF, {"I1": "test-i1"})
    assert "Endpoint = 89.169.53.7:62205" in merged
    assert "I1 = test-i1" in merged


def test_render_wireguard_conf_order() -> None:
    text = render_wireguard_conf(
        {
            "PrivateKey": "pk",
            "Address": "10.0.0.2/32",
            "Jc": "5",
            "I1": "junk",
        },
        {"PublicKey": "spk", "Endpoint": "1.2.3.4:51820", "AllowedIPs": "0.0.0.0/0"},
    )
    assert text.index("PrivateKey") < text.index("I1") < text.index("[Peer]")


def test_format_awg_diagnostic_warns_on_port_mismatch() -> None:
    text = format_awg_diagnostic(SAMPLE_CONF, expected_port=47661)
    assert "62205" in text
    assert "47661" in text

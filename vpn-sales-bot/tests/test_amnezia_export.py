import json

from app.services.amnezia_export import (
    build_amnezia_profile,
    conf_to_amneziawg_json_text,
    conf_to_vpn_uri,
    decode_vpn_uri,
    parse_wireguard_conf,
    vpn_uri_to_json_text,
    vpn_uri_to_awg_conf,
    wireguard_public_key,
)

SAMPLE_CONF = """[Interface]
PrivateKey = w+/FRUgl07Ozta/jjMu+lTYREpPxHaM+zpDGy6W4+wY=
Address = 10.8.1.3/32
DNS = 1.1.1.1, 1.0.0.1
Jc = 5
Jmin = 10
Jmax = 50
S1 = 50
S2 = 55
S3 = 42
S4 = 18
H1 = 2133468884-2141255094
H2 = 2147055103-2147065588
H3 = 2147152881-2147198990
H4 = 2147482586-2147482655
I1 = <r 2><b 0x858000010001000000000669636c6f756403636f6d0000010001c00c000100010000105a00044d583737>

[Peer]
PublicKey = bPojFUDaXFty60Y/5Y45ycvI4lFn4vRvTsM/bCVZ2T4=
PresharedKey = uYy1xffR82eE5cB3p7rsouOzVVRymNVYkwJxESTTgBk=
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = 89.169.53.7:47661
PersistentKeepalive = 25
"""

WORKING_VPN_URI = (
    "vpn://AAALSnjatVbdbtpIFL7PUyDUuyTgsWdsEzWV0gCNSUkopmTZuEKDPaROjG3Z5i9RpL7KvsJK-x7ZN9r5McaI4SIr1YT48H3fzDlnfM54Xo4q9Kq6UZhhPyRJWj2r3HOMXS-FxVV4-UDpXZATV4DiVRVoGtRN04SnKoBARUhpwOqJRK4KOTQUhICinXJTR8g0pXJtIwdINU3A5aBhNhqKVA43cmiqyNRPc5POL5NbPPaPSUX99HFSUVYmMhV6gfwrLl1v6Jru6lMD6VDRqD3VPaXQuYrilscABWF6g9BDpmZoxiepY74KUkY7yMCDDDrEdFzGSHPvzPCKk4qc9UPGAilrg8MjbZ6afL1tnhxUpRxPD0irIMBpNqZ1OvVZEVZfnJDBDq09h_525NXnVE8KnbrRScqurNO2ur16K-vgVrdXaCWdlcf3myus7DHPtAxp-xDch9Ae1HEFVM6IVU2OKjuwHwoYlGEbSLR2HuLOStl5kFAtg3mYoPyMcBBES-KN_Thl7L3ABafU-Ke-dSfwszMGCeRHMZMb-CTMLE84GRmDpjdozb51R-3YQvokurS_XltA-TJR766MoUbInarEXxvLb-elcMQkNJpN-jWzBmraviJO_MX4iayFbnlcb_e_PwSKcfuc4frjY3d-HAxG_VbcW13h7vFz3Pyy1u_g8XIk8RbPJ9up_m_gvJ3EFPdWmJFkil3yw3HCC89LSJpWziubbOqaSvHmjU2xD72-1b3oj8b050nlg926vL1p5r-pqEfTxBm5JmuqfVeWTthx6RjEDFpO3D238YrBzLZBYanMYlpboxZk8dmQjTGpdcV08k2BkionZTsBJbWc3G9_SsKc3O95J7SYz9_d6NQNi57dtfwO8zsSd_p33yMkYQ-yN58EvisexaQXPba_N_Ef7WytK6M6GkG0dhcWDNohXPQXg7Rbn1wO_1QH8Jw_RpL-xAnxxOj5aA1W02nfVEkLuZ-12EjSaH77PBz217Ob4ehp2Vm17MHg4fMTG30hetTqsSIqmvKkwvvQCVuhF0d-mFHSbNSA3qghrWacQUPXAfNNjyJ-mtFCvyYkxoG_IGzd2SKX6vdnlGY3eEZEBZfmKWlm2TxvS9Usb0Fx4YG2EYnH3Ee-pZd3pThKMgbzyLZo-rTtvnetzHbmlCQLkuw28rseEd3NXp1Q9rJkQfPXLAtaKkiiLHKjYLxgyxDx97z0lZzOJyHJxljsB-I4wDcE6Ys_S3CYMudj7oDJ515c3RG-7o7bnj2ZGs9C8uzjU3rUVLfDXo_Eri0Oqx6Z4nmQXR4cV-hSN_HjLE_v7a-3f_799fY3-18BhShM-UEG1PinBKsCZoVbwJuCY1Sp3KpHr0f_AY1rvcM"
)


def test_parse_wireguard_conf() -> None:
    parsed = parse_wireguard_conf(SAMPLE_CONF)
    assert parsed.interface["Jc"] == "5"
    assert parsed.peer["Endpoint"] == "89.169.53.7:47661"


def test_wireguard_public_key_matches_sample() -> None:
    assert wireguard_public_key("w+/FRUgl07Ozta/jjMu+lTYREpPxHaM+zpDGy6W4+wY=") == (
        "Y7TDdTEmQMYFpI56boCSLKI10Gb2WH7V3eeW20pL9wQ="
    )


def test_conf_to_vpn_uri_roundtrip_structure() -> None:
    vpn_uri = conf_to_vpn_uri(
        SAMPLE_CONF,
        host_name="89.169.53.7",
        dns1="1.1.1.1",
        dns2="1.0.0.1",
        description="Сервер 1",
    )
    assert vpn_uri.startswith("vpn://")

    profile = decode_vpn_uri(vpn_uri)
    assert profile["defaultContainer"] == "amnezia-awg2"
    assert profile["hostName"] == "89.169.53.7"
    assert profile["dns1"] == "1.1.1.1"

    last_config = json.loads(profile["containers"][0]["awg"]["last_config"])
    assert last_config["client_ip"] == "10.8.1.3"
    assert last_config["port"] == 47661
    assert last_config["server_pub_key"] == "bPojFUDaXFty60Y/5Y45ycvI4lFn4vRvTsM/bCVZ2T4="
    assert "$PRIMARY_DNS" in last_config["config"]


def test_vpn_uri_to_json_text() -> None:
    vpn_uri = conf_to_vpn_uri(
        SAMPLE_CONF,
        host_name="89.169.53.7",
        dns1="1.1.1.1",
        dns2="1.0.0.1",
        description="Сервер 1",
    )
    json_text = vpn_uri_to_json_text(vpn_uri)
    assert json_text.startswith("{")
    assert json_text.endswith("\n")
    profile = json.loads(json_text)
    assert profile["defaultContainer"] == "amnezia-awg2"


def test_conf_to_amneziawg_json_text() -> None:
    json_text = conf_to_amneziawg_json_text(
        SAMPLE_CONF,
        host_name="89.169.53.7",
        dns1="1.1.1.1",
        dns2="1.0.0.1",
        description="Сервер 1",
    )
    profile = json.loads(json_text)
    assert profile["hostName"] == "89.169.53.7"


def test_vpn_uri_to_awg_conf() -> None:
    vpn_uri = conf_to_vpn_uri(
        SAMPLE_CONF,
        host_name="89.169.53.7",
        dns1="1.1.1.1",
        dns2="1.0.0.1",
        description="Сервер 1",
    )
    conf = vpn_uri_to_awg_conf(vpn_uri)
    assert conf.startswith("[Interface]")
    assert "Endpoint = 89.169.53.7:47661" in conf
    assert "1.1.1.1" in conf


def test_build_profile_from_working_vpn_conf() -> None:
    working = decode_vpn_uri(WORKING_VPN_URI)
    last_config = json.loads(working["containers"][0]["awg"]["last_config"])
    rebuilt = build_amnezia_profile(
        last_config["config"],
        host_name=working["hostName"],
        dns1=working["dns1"],
        dns2=working["dns2"],
        description=working["description"],
    )
    rebuilt_last = json.loads(rebuilt["containers"][0]["awg"]["last_config"])

    assert rebuilt_last["client_ip"] == last_config["client_ip"]
    assert rebuilt_last["client_pub_key"] == last_config["client_pub_key"]
    assert rebuilt_last["server_pub_key"] == last_config["server_pub_key"]
    assert rebuilt_last["port"] == last_config["port"]

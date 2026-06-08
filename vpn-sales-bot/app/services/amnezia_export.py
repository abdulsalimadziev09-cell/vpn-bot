"""Convert WireGuard/AWG .conf text to AmneziaWG vpn:// JSON URI."""

from __future__ import annotations

import base64
import json
import zlib
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

_AWG_KEYS = ("H1", "H2", "H3", "H4", "I1", "I2", "I3", "I4", "I5", "Jc", "Jmin", "Jmax", "S1", "S2", "S3", "S4")


@dataclass(frozen=True)
class WireGuardConf:
    interface: dict[str, str]
    peer: dict[str, str]


class AmneziaExportError(ValueError):
    pass


def parse_wireguard_conf(conf_text: str) -> WireGuardConf:
    interface: dict[str, str] = {}
    peer: dict[str, str] = {}
    section: str | None = None

    for raw_line in conf_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[Interface]":
            section = "interface"
            continue
        if line == "[Peer]":
            section = "peer"
            continue
        if section is None or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if section == "interface":
            interface[key] = value
        else:
            peer[key] = value

    if not interface.get("PrivateKey"):
        raise AmneziaExportError("Missing [Interface] PrivateKey")
    if not peer.get("PublicKey"):
        raise AmneziaExportError("Missing [Peer] PublicKey")
    if not peer.get("Endpoint"):
        raise AmneziaExportError("Missing [Peer] Endpoint")
    if not interface.get("Address"):
        raise AmneziaExportError("Missing [Interface] Address")

    return WireGuardConf(interface=interface, peer=peer)


def wireguard_public_key(private_key_b64: str) -> str:
    private_bytes = base64.b64decode(private_key_b64)
    private_key = X25519PrivateKey.from_private_bytes(private_bytes)
    public_bytes = private_key.public_key().public_bytes_raw()
    return base64.b64encode(public_bytes).decode("ascii")


def qt_compress(data: bytes, level: int = 8) -> bytes:
    compressed = zlib.compress(data, level)
    return len(data).to_bytes(4, "big") + compressed


def encode_vpn_uri(profile: dict) -> str:
    raw = json.dumps(profile, ensure_ascii=False).encode("utf-8")
    encoded = base64.urlsafe_b64encode(qt_compress(raw)).decode("ascii").rstrip("=")
    return f"vpn://{encoded}"


def profile_to_json_text(profile: dict, *, indent: int = 2) -> str:
    return json.dumps(profile, ensure_ascii=False, indent=indent) + "\n"


def vpn_uri_to_json_text(vpn_uri: str, *, indent: int = 2) -> str:
    return profile_to_json_text(decode_vpn_uri(vpn_uri.strip()), indent=indent)


def _client_ipv4(address: str) -> str:
    for part in address.split(","):
        part = part.strip()
        if "." in part and "/" in part:
            return part.split("/")[0]
    raise AmneziaExportError("Could not parse client IPv4 from Address")


def _subnet_address(client_ip: str) -> str:
    octets = client_ip.split(".")
    if len(octets) != 4:
        raise AmneziaExportError(f"Invalid client IPv4: {client_ip}")
    return ".".join(octets[:3]) + ".0"


def _split_endpoint(endpoint: str) -> tuple[str, str]:
    if endpoint.startswith("["):
        host, port = endpoint.rsplit("]:", 1)
        return host.lstrip("["), port
    host, port = endpoint.rsplit(":", 1)
    return host, port


def _amnezia_conf_text(conf_text: str, dns1: str, dns2: str) -> str:
    lines = conf_text.replace("\r", "").split("\n")
    result: list[str] = []
    dns_replaced = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("DNS ="):
            result.append(f"DNS = $PRIMARY_DNS, $SECONDARY_DNS")
            dns_replaced = True
            continue
        result.append(line)

    if not dns_replaced and dns1:
        insert_at = 0
        for index, line in enumerate(result):
            if line.strip().startswith("Address ="):
                insert_at = index + 1
                break
        result.insert(insert_at, "DNS = $PRIMARY_DNS, $SECONDARY_DNS")

    text = "\n".join(result)
    if not text.endswith("\n"):
        text += "\n"
    return text


def build_amnezia_profile(
    conf_text: str,
    *,
    host_name: str,
    dns1: str = "1.1.1.1",
    dns2: str = "1.0.0.1",
    description: str = "VPN",
    mtu: str = "1280",
) -> dict:
    parsed = parse_wireguard_conf(conf_text)
    iface, peer = parsed.interface, parsed.peer

    client_ip = _client_ipv4(iface["Address"])
    endpoint_host, endpoint_port = _split_endpoint(peer["Endpoint"])
    client_pub_key = wireguard_public_key(iface["PrivateKey"])
    allowed_ips = [part.strip() for part in peer.get("AllowedIPs", "0.0.0.0/0").split(",") if part.strip()]
    keepalive = peer.get("PersistentKeepalive", "25")

    awg = {key: iface.get(key, "") for key in _AWG_KEYS}
    amnezia_conf = _amnezia_conf_text(conf_text, dns1, dns2)

    last_config = {
        **awg,
        "allowed_ips": allowed_ips,
        "clientId": client_pub_key,
        "client_ip": client_ip,
        "client_priv_key": iface["PrivateKey"],
        "client_pub_key": client_pub_key,
        "config": amnezia_conf,
        "hostName": endpoint_host.strip("[]"),
        "mtu": mtu,
        "persistent_keep_alive": keepalive,
        "port": int(endpoint_port),
        "psk_key": peer.get("PresharedKey", ""),
        "server_pub_key": peer["PublicKey"],
    }

    awg_block = {
        **awg,
        "last_config": json.dumps(last_config, indent=4) + "\n",
        "port": endpoint_port,
        "protocol_version": "2",
        "subnet_address": _subnet_address(client_ip),
        "transport_proto": "udp",
    }

    return {
        "containers": [{"awg": awg_block, "container": "amnezia-awg2"}],
        "defaultContainer": "amnezia-awg2",
        "description": description,
        "dns1": dns1,
        "dns2": dns2,
        "hostName": host_name or endpoint_host.strip("[]"),
    }


def conf_to_vpn_uri(
    conf_text: str,
    *,
    host_name: str = "",
    dns1: str = "1.1.1.1",
    dns2: str = "1.0.0.1",
    description: str = "VPN",
    mtu: str = "1280",
) -> str:
    profile = build_amnezia_profile(
        conf_text,
        host_name=host_name,
        dns1=dns1,
        dns2=dns2,
        description=description,
        mtu=mtu,
    )
    return encode_vpn_uri(profile)


def conf_to_amneziawg_json_text(
    conf_text: str,
    *,
    host_name: str = "",
    dns1: str = "1.1.1.1",
    dns2: str = "1.0.0.1",
    description: str = "VPN",
    mtu: str = "1280",
) -> str:
    profile = build_amnezia_profile(
        conf_text,
        host_name=host_name,
        dns1=dns1,
        dns2=dns2,
        description=description,
        mtu=mtu,
    )
    return profile_to_json_text(profile)


def decode_vpn_uri(vpn_uri: str) -> dict:
    payload = vpn_uri.removeprefix("vpn://")
    pad = "=" * ((4 - len(payload) % 4) % 4)
    raw = base64.urlsafe_b64decode(payload + pad)
    decoded = zlib.decompress(raw[4:])
    return json.loads(decoded)

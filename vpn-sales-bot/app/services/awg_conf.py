"""Parse and enrich AmneziaWG client configs."""

from __future__ import annotations

from app.config import settings
from app.services.amnezia_export import parse_wireguard_conf

_AWG_INTERFACE_KEYS = (
    "Jc",
    "Jmin",
    "Jmax",
    "S1",
    "S2",
    "S3",
    "S4",
    "H1",
    "H2",
    "H3",
    "H4",
    "I1",
    "I2",
    "I3",
    "I4",
    "I5",
)

_INTERFACE_PREFIX_KEYS = ("PrivateKey", "Address", "DNS")
_PEER_KEYS = ("PublicKey", "PresharedKey", "Endpoint", "AllowedIPs", "PersistentKeepalive")

# I1 с рабочего Amnezia AWG2 (обход DPI). Переопределяется через AMNEZIA_AWG_I1 в .env
_DEFAULT_AWG_I1 = (
    "<r 2><b 0x858000010001000000000669636c6f756403636f6d0000010001"
    "c00c000100010000105a00044d583737>"
)


def awg_template_from_settings() -> dict[str, str]:
    mapping = {
        "I1": settings.amnezia_awg_i1 or _DEFAULT_AWG_I1,
        "I2": settings.amnezia_awg_i2,
        "I3": settings.amnezia_awg_i3,
        "I4": settings.amnezia_awg_i4,
        "I5": settings.amnezia_awg_i5,
        "Jc": settings.amnezia_awg_jc,
        "Jmin": settings.amnezia_awg_jmin,
        "Jmax": settings.amnezia_awg_jmax,
        "S1": settings.amnezia_awg_s1,
        "S2": settings.amnezia_awg_s2,
        "S3": settings.amnezia_awg_s3,
        "S4": settings.amnezia_awg_s4,
        "H1": settings.amnezia_awg_h1,
        "H2": settings.amnezia_awg_h2,
        "H3": settings.amnezia_awg_h3,
        "H4": settings.amnezia_awg_h4,
    }
    return {key: value.strip() for key, value in mapping.items() if value and value.strip()}


def apply_awg_enrichment(conf_text: str, extra_template: dict[str, str] | None = None) -> str:
    template = awg_template_from_settings()
    if extra_template:
        template = {**extra_template, **template}
    return merge_interface_params(conf_text, template)


def parse_interface_params(conf_text: str) -> dict[str, str]:
    parsed = parse_wireguard_conf(conf_text)
    return {key: parsed.interface[key] for key in _AWG_INTERFACE_KEYS if key in parsed.interface}


def merge_interface_params(conf_text: str, template: dict[str, str]) -> str:
    if not template:
        return conf_text

    parsed = parse_wireguard_conf(conf_text)
    interface = dict(parsed.interface)
    peer = dict(parsed.peer)

    for key, value in template.items():
        if key not in _AWG_INTERFACE_KEYS or not value:
            continue
        interface[key] = value

    return render_wireguard_conf(interface, peer)


def render_wireguard_conf(interface: dict[str, str], peer: dict[str, str]) -> str:
    lines = ["[Interface]"]

    for key in _INTERFACE_PREFIX_KEYS:
        if key in interface:
            lines.append(f"{key} = {interface[key]}")

    for key in _AWG_INTERFACE_KEYS:
        if key in interface:
            lines.append(f"{key} = {interface[key]}")

    for key, value in interface.items():
        if key in _INTERFACE_PREFIX_KEYS or key in _AWG_INTERFACE_KEYS:
            continue
        lines.append(f"{key} = {value}")

    lines.append("")
    lines.append("[Peer]")

    for key in _PEER_KEYS:
        if key in peer:
            lines.append(f"{key} = {peer[key]}")

    for key, value in peer.items():
        if key in _PEER_KEYS:
            continue
        lines.append(f"{key} = {value}")

    return "\n".join(lines) + "\n"


def diagnose_awg_conf(conf_text: str) -> dict[str, str | bool]:
    if conf_text.strip().startswith("vpn://"):
        return {
            "client_ip": "",
            "subnet": "",
            "endpoint": "",
            "port": "",
            "server_pubkey": "",
            "jc": "",
            "jmin": "",
            "jmax": "",
            "has_i1": True,
            "s1": "",
            "s2": "",
            "s3": "",
            "s4": "",
            "source": "vpnuri",
        }

    enriched = apply_awg_enrichment(conf_text)
    parsed = parse_wireguard_conf(enriched)
    iface, peer = parsed.interface, parsed.peer
    address = iface.get("Address", "")
    ipv4 = next((part.strip().split("/")[0] for part in address.split(",") if "." in part), "")
    subnet = ".".join(ipv4.split(".")[:3]) + ".0" if ipv4 else ""
    endpoint = peer.get("Endpoint", "")
    port = endpoint.rsplit(":", 1)[-1] if endpoint else ""

    return {
        "client_ip": ipv4,
        "subnet": subnet,
        "endpoint": endpoint,
        "port": port,
        "server_pubkey": peer.get("PublicKey", ""),
        "jc": iface.get("Jc", ""),
        "jmin": iface.get("Jmin", ""),
        "jmax": iface.get("Jmax", ""),
        "has_i1": bool(iface.get("I1", "").strip()),
        "s1": iface.get("S1", ""),
        "s2": iface.get("S2", ""),
        "s3": iface.get("S3", ""),
        "s4": iface.get("S4", ""),
    }


def format_awg_diagnostic(conf_text: str, *, expected_port: int = 0) -> str:
    info = diagnose_awg_conf(conf_text)
    if info.get("source") == "vpnuri":
        return (
            "Параметры выданного конфига:\n"
            "• Источник: .vpnuri (готовый vpn:// от AWG installer)\n"
            "• I1 (junk-пакет): встроен в vpn://"
        )

    lines = [
        "Параметры выданного конфига:",
        f"• IP: {info['client_ip'] or '—'} (подсеть {info['subnet'] or '—'})",
        f"• Endpoint: {info['endpoint'] or '—'}",
        f"• Jc/Jmin/Jmax: {info['jc'] or '—'}/{info['jmin'] or '—'}/{info['jmax'] or '—'}",
        f"• S1–S4: {info['s1'] or '—'}/{info['s2'] or '—'}/{info['s3'] or '—'}/{info['s4'] or '—'}",
        f"• I1 (junk-пакет): {'есть' if info['has_i1'] else 'НЕТ'}",
    ]

    if expected_port and info["port"] and str(info["port"]) != str(expected_port):
        lines.append(
            f"⚠️ Порт {info['port']} ≠ ожидаемого {expected_port}. "
            "Бот, вероятно, создаёт клиентов на другом AWG-сервере."
        )
    if not info["has_i1"]:
        lines.append("⚠️ Нет I1 — задайте AMNEZIA_AWG_I1 в .env (в кавычках).")

    return "\n".join(lines)

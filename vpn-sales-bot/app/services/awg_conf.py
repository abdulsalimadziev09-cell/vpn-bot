"""Parse and enrich AmneziaWG client configs."""

from __future__ import annotations

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


def parse_interface_params(conf_text: str) -> dict[str, str]:
    parsed = parse_wireguard_conf(conf_text)
    return {key: parsed.interface[key] for key in _AWG_INTERFACE_KEYS if key in parsed.interface}


def merge_interface_params(conf_text: str, template: dict[str, str]) -> str:
    if not template:
        return conf_text

    lines = conf_text.replace("\r", "").split("\n")
    present = {line.split("=", 1)[0].strip() for line in lines if "=" in line and not line.strip().startswith("#")}
    result: list[str] = []
    inserted = False

    for line in lines:
        result.append(line)
        if not inserted and line.strip() == "[Interface]":
            for key in _AWG_INTERFACE_KEYS:
                value = template.get(key)
                if not value or key in present:
                    continue
                result.append(f"{key} = {value}")
            inserted = True

    for key in _AWG_INTERFACE_KEYS:
        value = template.get(key)
        if not value or key in present:
            continue
        if not inserted:
            continue
        result.append(f"{key} = {value}")

    text = "\n".join(result)
    if not text.endswith("\n"):
        text += "\n"
    return text


def diagnose_awg_conf(conf_text: str) -> dict[str, str | bool]:
    parsed = parse_wireguard_conf(conf_text)
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
        lines.append("⚠️ Нет I1 — обфускация AWG2 неполная, DPI может блокировать.")

    return "\n".join(lines)

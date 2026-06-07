import json

from app.services.split_tunnel_gift import (
    SITES_FILENAME,
    format_split_tunnel_gift,
    split_tunnel_sites_count,
    split_tunnel_sites_path,
)


def test_split_tunnel_sites_file_is_valid_amnezia_format() -> None:
    path = split_tunnel_sites_path()
    assert path.name == SITES_FILENAME

    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    assert isinstance(data, list)
    assert len(data) > 0
    assert "hostname" in data[0]
    assert "ip" in data[0]


def test_format_split_tunnel_gift_mentions_entry_count() -> None:
    text = format_split_tunnel_gift()
    count = split_tunnel_sites_count()

    assert "🎁" in text
    assert str(count) in text
    assert SITES_FILENAME in text

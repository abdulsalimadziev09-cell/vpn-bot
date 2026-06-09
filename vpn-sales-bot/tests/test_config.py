from app.config import Settings


def test_admin_ids_empty_env(monkeypatch):
    monkeypatch.setenv("ADMIN_IDS", "")
    settings = Settings()
    assert settings.admin_ids == []


def test_admin_ids_comma_separated(monkeypatch):
    monkeypatch.setenv("ADMIN_IDS", "111, 222")
    settings = Settings()
    assert settings.admin_ids == [111, 222]


def test_admin_ids_single_value(monkeypatch):
    monkeypatch.setenv("ADMIN_IDS", "5200738946")
    settings = Settings()
    assert settings.admin_ids == [5200738946]

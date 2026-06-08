import os

import pytest

from app.config import Settings


def test_telegram_api_id_empty_string():
    settings = Settings(telegram_api_id="")
    assert settings.telegram_api_id == ""
    assert settings.telegram_api_id_int == 0


def test_telegram_api_id_from_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_API_ID", "")
    settings = Settings()
    assert settings.telegram_api_id_int == 0


def test_telegram_api_id_parses_int():
    settings = Settings(telegram_api_id="12345678")
    assert settings.telegram_api_id_int == 12345678

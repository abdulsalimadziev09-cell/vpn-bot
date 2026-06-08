import os

import pytest

from app.config import Settings


def test_telegram_api_id_empty_string():
    settings = Settings(telegram_api_id="")
    assert settings.telegram_api_id == 0


def test_telegram_api_id_missing():
    settings = Settings(_env_file=None)
    assert settings.telegram_api_id == 0

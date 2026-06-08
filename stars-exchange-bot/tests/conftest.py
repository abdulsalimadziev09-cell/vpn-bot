import os

import pytest

os.environ.setdefault("BOT_TOKEN", "test-token-for-pytest")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ROBOKASSA_MERCHANT_LOGIN", "demo")
os.environ.setdefault("ROBOKASSA_PASSWORD1", "password1")
os.environ.setdefault("ROBOKASSA_PASSWORD2", "password2")

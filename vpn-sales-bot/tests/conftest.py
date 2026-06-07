import os

import pytest

os.environ.setdefault("BOT_TOKEN", "test-token-for-pytest")


@pytest.fixture
def anyio_backend():
    return "asyncio"

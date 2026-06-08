from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.db.models import UserPlan
from app.services.subscription import (
    activate_pro,
    is_pro_active,
    item_limit_for_user,
    refresh_user_plan,
)


def _user(plan: str = UserPlan.FREE, expires: datetime | None = None) -> SimpleNamespace:
    return SimpleNamespace(telegram_id=1, plan=plan, plan_expires_at=expires)


def test_is_pro_active_with_valid_subscription() -> None:
    expires = datetime.now(timezone.utc) + timedelta(days=5)
    assert is_pro_active(_user(UserPlan.PRO, expires)) is True


def test_is_pro_active_expired() -> None:
    expires = datetime.now(timezone.utc) - timedelta(days=1)
    assert is_pro_active(_user(UserPlan.PRO, expires)) is False


def test_item_limit_free_vs_pro() -> None:
    free = _user(UserPlan.FREE)
    pro = _user(UserPlan.PRO, datetime.now(timezone.utc) + timedelta(days=1))
    assert item_limit_for_user(free) == 100
    assert item_limit_for_user(pro) == 5000


async def test_refresh_user_plan_downgrades_expired() -> None:
    class FakeSession:
        async def flush(self) -> None:
            return None

    user = _user(UserPlan.PRO, datetime.now(timezone.utc) - timedelta(hours=1))
    await refresh_user_plan(FakeSession(), user)
    assert user.plan == UserPlan.FREE
    assert user.plan_expires_at is None


async def test_activate_pro_sets_expiry() -> None:
    class FakeSession:
        async def flush(self) -> None:
            return None

    user = _user(UserPlan.FREE)
    now = datetime.now(timezone.utc)
    await activate_pro(FakeSession(), user, days=30)
    assert user.plan == UserPlan.PRO
    assert user.plan_expires_at is not None
    assert user.plan_expires_at > now

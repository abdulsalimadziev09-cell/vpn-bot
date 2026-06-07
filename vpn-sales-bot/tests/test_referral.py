from datetime import datetime, timedelta, timezone

import pytest

from app.formatters import format_expiry_reminder, subscription_days_remaining
from app.repositories.referrals import parse_referral_start_arg
from app.db.models import Plan, Subscription, SubscriptionStatus


def test_parse_referral_start_arg():
    assert parse_referral_start_arg("ref5200738946") == 5200738946
    assert parse_referral_start_arg("ref") is None
    assert parse_referral_start_arg(None) is None
    assert parse_referral_start_arg("other") is None


def test_subscription_days_remaining():
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=1,
        plan_id=1,
        starts_at=now,
        expires_at=now + timedelta(days=5, hours=2),
        status=SubscriptionStatus.ACTIVE,
    )
    assert subscription_days_remaining(subscription) == 6


def test_format_expiry_reminder_contains_days():
    text = format_expiry_reminder(3)
    assert "3" in text
    assert "Продлите" in text

from datetime import datetime, timedelta, timezone

from app.db.models import Plan, Subscription, SubscriptionStatus, User
from app.formatters import build_admin_subscriptions_report, subscription_days_remaining


def test_build_admin_subscriptions_report():
    now = datetime.now(timezone.utc)
    user = User(telegram_id=100, username="tester")
    plan = Plan(id=1, code="month_1", title="1 месяц", days=30, price_rub=299, stars_price=150)
    subscription = Subscription(
        user_id=100,
        plan_id=1,
        starts_at=now,
        expires_at=now + timedelta(days=2),
        status=SubscriptionStatus.ACTIVE,
    )
    subscription.user = user
    subscription.plan = plan

    messages = build_admin_subscriptions_report([subscription])
    assert len(messages) == 1
    assert "@tester" in messages[0]
    assert "осталось" in messages[0]
    assert subscription_days_remaining(subscription) == 2


def test_build_admin_subscriptions_report_empty():
    messages = build_admin_subscriptions_report([])
    assert messages == ["📊 Активных подписок нет."]

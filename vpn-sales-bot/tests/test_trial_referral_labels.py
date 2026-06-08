from app.formatters import (
    format_referral_bonus_short,
    format_trial_button_label,
    format_trial_period_short,
    format_welcome_trial_line,
)


def test_trial_period_labels(monkeypatch):
    monkeypatch.setattr("app.formatters.settings.trial_days", 7)
    assert format_trial_period_short() == "7 дней"
    assert "7 дней" in format_welcome_trial_line()
    assert "7 дней" in format_trial_button_label()


def test_referral_bonus_label(monkeypatch):
    monkeypatch.setattr("app.formatters.settings.referral_bonus_days", 3)
    assert format_referral_bonus_short() == "+3 дня"

import pytest

from app.services.pricing import normalize_username, rub_for_stars, validate_stars_amount


def test_rub_for_stars():
    assert rub_for_stars(100) == 165


def test_validate_stars_amount():
    assert validate_stars_amount(10) is not None
    assert validate_stars_amount(100) is None


def test_normalize_username():
    assert normalize_username("@Durov") == "durov"
    with pytest.raises(ValueError):
        normalize_username("bad name")

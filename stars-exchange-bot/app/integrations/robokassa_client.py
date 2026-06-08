from functools import lru_cache

from aiorobokassa import RoboKassaClient

from app.config import settings


@lru_cache
def get_robokassa_client() -> RoboKassaClient:
    return RoboKassaClient(
        merchant_login=settings.robokassa_merchant_login,
        password1=settings.robokassa_password1,
        password2=settings.robokassa_password2,
        test_mode=settings.robokassa_test_mode,
    )


def build_payment_url(*, inv_id: int, amount_rub: int, description: str) -> str:
    client = get_robokassa_client()
    return client.create_payment_url(
        out_sum=amount_rub,
        description=description,
        inv_id=inv_id,
        culture="ru",
    )


def verify_result_notification(params: dict[str, str]) -> tuple[str, str]:
    client = get_robokassa_client()
    parsed = client.parse_result_url_params(params)
    client.verify_result_url(
        out_sum=str(parsed["out_sum"]),
        inv_id=str(parsed["inv_id"]),
        signature_value=str(parsed["signature_value"]),
        shp_params=parsed.get("shp_params") or {},
    )
    return str(parsed["out_sum"]), str(parsed["inv_id"])

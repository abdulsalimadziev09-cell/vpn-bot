import logging

from telethon import TelegramClient
from telethon.tl.functions.payments import GetPaymentFormRequest, GetStarsGiftOptionsRequest, SendStarsFormRequest
from telethon.tl.types import InputInvoiceStars, InputStorePaymentStarsGift, InputUser

from app.config import settings
from app.db.models import Order
from app.services.stars_delivery.base import DeliveryResult

logger = logging.getLogger(__name__)


def _pick_gift_option(options: list, stars_needed: int):
    exact = [opt for opt in options if opt.stars == stars_needed]
    if exact:
        return exact[0]

    larger = sorted([opt for opt in options if opt.stars >= stars_needed], key=lambda o: o.stars)
    if larger:
        return larger[0]

    if not options:
        return None
    return max(options, key=lambda o: o.stars)


async def deliver_via_telethon(order: Order) -> DeliveryResult:
    if not settings.telegram_api_id_int or not settings.telegram_api_hash:
        return DeliveryResult(ok=False, error="Telethon не настроен (API_ID/API_HASH)")

    client = TelegramClient(
        settings.telethon_session_path,
        settings.telegram_api_id_int,
        settings.telegram_api_hash,
    )

    try:
        await client.connect()
        if not await client.is_user_authorized():
            return DeliveryResult(ok=False, error="Telethon-сессия не авторизована")

        recipient = await client.get_entity(order.recipient_username)
        input_user = InputUser(user_id=recipient.id, access_hash=recipient.access_hash)

        options = await client(GetStarsGiftOptionsRequest(user_id=input_user))
        if not options:
            return DeliveryResult(ok=False, error="Telegram не вернул пакеты Stars для получателя")

        option = _pick_gift_option(options, order.stars_amount)
        if option is None:
            return DeliveryResult(ok=False, error="Нет подходящего пакета Stars")

        invoice = InputInvoiceStars(
            purpose=InputStorePaymentStarsGift(
                user_id=input_user,
                stars=option.stars,
                currency=option.currency,
                amount=option.amount,
            )
        )
        form = await client(GetPaymentFormRequest(invoice=invoice))
        await client(SendStarsFormRequest(form_id=form.form_id, invoice=invoice))

        order.recipient_telegram_id = recipient.id
        return DeliveryResult(ok=True, delivered_stars=option.stars)
    except Exception as exc:
        logger.exception("Telethon delivery failed for order %s", order.id)
        return DeliveryResult(ok=False, error=str(exc))
    finally:
        await client.disconnect()

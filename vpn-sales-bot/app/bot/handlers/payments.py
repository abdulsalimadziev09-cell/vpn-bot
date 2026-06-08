from aiogram import F, Router
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery

from app.bot.keyboards import stars_buy_keyboard
from app.config import settings
from app.db.models import Order, OrderStatus, Plan
from app.db.session import async_session_factory
from app.formatters import format_stars_buy_hint
from app.repositories.orders import get_order_by_id
from app.services.payment import fulfill_paid_order, handle_paid_order_extras, mark_order_paid_from_stars

router = Router()

ORDER_PAYLOAD_PREFIX = "vpn_order:"


def order_payload(order_id: int) -> str:
    return f"{ORDER_PAYLOAD_PREFIX}{order_id}"


def parse_order_payload(payload: str) -> int | None:
    if not payload.startswith(ORDER_PAYLOAD_PREFIX):
        return None
    try:
        return int(payload.removeprefix(ORDER_PAYLOAD_PREFIX))
    except ValueError:
        return None


async def send_stars_invoice(message: Message, order: Order, plan: Plan) -> None:
    await message.answer_invoice(
        title=f"VPN — {plan.title}",
        description=f"Подписка на {plan.days} дней. Конфиг придёт в этот чат после оплаты.",
        payload=order_payload(order.id),
        currency="XTR",
        prices=[LabeledPrice(label=plan.title, amount=plan.stars_price)],
        provider_token="",
    )
    if settings.stars_buy_bot_url:
        await message.answer(
            format_stars_buy_hint(),
            reply_markup=stars_buy_keyboard(),
        )


@router.pre_checkout_query(F.invoice_payload.startswith(ORDER_PAYLOAD_PREFIX))
async def pre_checkout(query: PreCheckoutQuery) -> None:
    order_id = parse_order_payload(query.invoice_payload)
    if order_id is None:
        await query.answer(ok=False, error_message="Некорректный заказ.")
        return

    async with async_session_factory() as session:
        order = await get_order_by_id(session, order_id)

    if not order or order.user_id != query.from_user.id:
        await query.answer(ok=False, error_message="Заказ не найден.")
        return
    if order.status != OrderStatus.PENDING:
        await query.answer(ok=False, error_message="Заказ уже оплачен или отменён.")
        return

    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payment = message.successful_payment
    if not payment:
        return

    order_id = parse_order_payload(payment.invoice_payload)
    if order_id is None:
        return

    async with async_session_factory() as session:
        order = await mark_order_paid_from_stars(
            session,
            order_id=order_id,
            user_id=message.from_user.id,
        )
        if not order:
            return

        await handle_paid_order_extras(session, message.bot, order)
        fulfilled = await fulfill_paid_order(session, message.bot, order)
        if fulfilled:
            await message.answer("Спасибо! VPN-конфиг отправлен выше.")
        elif settings.vpn_provisioner == "manual":
            await message.answer(
                "Оплата получена. Конфиг будет выдан в ближайшее время — обычно в течение нескольких минут."
            )
        else:
            await message.answer(
                "Оплата получена. Выдаём конфиг — если не пришёл в течение 5 минут, напишите в поддержку."
            )

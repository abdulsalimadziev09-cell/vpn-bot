from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery

from app.config import settings
from app.db.session import async_session_factory
from app.repositories.items import get_or_create_user
from app.services.subscription import activate_pro, format_plan_status

router = Router()

PRO_PAYLOAD = "pro_subscription"


@router.message(Command("buy"))
async def cmd_buy(message: Message) -> None:
    if not settings.payments_enabled:
        await message.answer("Оплата временно недоступна.")
        return

    await message.answer_invoice(
        title="Save Later Pro",
        description=(
            f"Pro на {settings.pro_days} дней: "
            f"{settings.pro_item_limit} сохранений, умный поиск, shared-папки"
        ),
        payload=PRO_PAYLOAD,
        currency="XTR",
        prices=[LabeledPrice(label=f"Pro {settings.pro_days} дн.", amount=settings.pro_stars_price)],
        provider_token="",
    )


@router.pre_checkout_query(F.invoice_payload == PRO_PAYLOAD)
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payment = message.successful_payment
    if not payment or payment.invoice_payload != PRO_PAYLOAD:
        return

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        await activate_pro(session, user)
        status = format_plan_status(user)
        await session.commit()

    await message.answer(
        f"Спасибо! Pro активирован.\n{status}\n"
        "Умный поиск и shared-папки уже доступны."
    )

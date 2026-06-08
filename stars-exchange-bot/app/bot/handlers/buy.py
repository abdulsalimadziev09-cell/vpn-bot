from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import packages_keyboard, payment_keyboard, recipient_keyboard
from app.db.session import async_session_factory
from app.formatters import format_order_summary, format_package_line
from app.repositories.packages import get_package_by_id, list_active_packages
from app.services.payment import create_stars_order, payment_link_for_order
from app.services.pricing import normalize_username, rub_for_stars, validate_stars_amount

router = Router()


class BuyStates(StatesGroup):
    waiting_recipient = State()
    waiting_custom_stars = State()


@router.callback_query(F.data == "buy:menu")
async def buy_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    async with async_session_factory() as session:
        packages = await list_active_packages(session)

    if not packages:
        await callback.answer("Пакеты временно недоступны", show_alert=True)
        return

    lines = "\n".join(format_package_line(p) for p in packages)
    await callback.message.edit_text(
        f"Выберите пакет Stars:\n\n{lines}",
        reply_markup=packages_keyboard(packages),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:pkg:"))
async def buy_package(callback: CallbackQuery, state: FSMContext) -> None:
    package_id = int(callback.data.split(":")[-1])
    async with async_session_factory() as session:
        package = await get_package_by_id(session, package_id)

    if not package or not package.is_active:
        await callback.answer("Пакет недоступен", show_alert=True)
        return

    await state.update_data(
        package_id=package.id,
        stars_amount=package.stars_amount,
        amount_rub=package.price_rub,
    )
    await state.set_state(BuyStates.waiting_recipient)
    await callback.message.edit_text(
        f"Пакет: {package.stars_amount} ⭐ за {package.price_rub} ₽\n\n"
        "Кому отправить Stars?\n"
        "Введите @username или нажмите «Себе».",
        reply_markup=recipient_keyboard(callback.from_user.username),
    )
    await callback.answer()


@router.callback_query(F.data == "buy:custom")
async def buy_custom(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BuyStates.waiting_custom_stars)
    await callback.message.edit_text(
        "Введите количество Stars (целое число).\n"
        "Мы посчитаем сумму в рублях автоматически."
    )
    await callback.answer()


@router.message(BuyStates.waiting_custom_stars)
async def custom_stars_entered(message: Message, state: FSMContext) -> None:
    try:
        stars = int(message.text.strip())
    except (TypeError, ValueError):
        await message.answer("Введите целое число, например: 250")
        return

    error = validate_stars_amount(stars)
    if error:
        await message.answer(error)
        return

    rub = rub_for_stars(stars)
    await state.update_data(package_id=None, stars_amount=stars, amount_rub=rub)
    await state.set_state(BuyStates.waiting_recipient)
    await message.answer(
        f"{stars} ⭐ ≈ {rub} ₽\n\n"
        "Кому отправить Stars?\n"
        "Введите @username или нажмите «Себе».",
        reply_markup=recipient_keyboard(message.from_user.username),
    )


@router.callback_query(F.data == "buy:recipient:self")
async def recipient_self(callback: CallbackQuery, state: FSMContext) -> None:
    username = callback.from_user.username
    if not username:
        await callback.answer("У вас нет @username в Telegram", show_alert=True)
        return
    await _create_order_and_send_link(callback.message, state, callback.from_user.id, callback.from_user.username, username)
    await callback.answer()


@router.message(BuyStates.waiting_recipient)
async def recipient_entered(message: Message, state: FSMContext) -> None:
    try:
        username = normalize_username(message.text)
    except ValueError:
        await message.answer("Некорректный @username. Пример: @durov")
        return

    await _create_order_and_send_link(message, state, message.from_user.id, message.from_user.username, username)


async def _create_order_and_send_link(
    message: Message,
    state: FSMContext,
    buyer_id: int,
    buyer_username: str | None,
    recipient_username: str,
) -> None:
    data = await state.get_data()
    stars_amount = data.get("stars_amount")
    amount_rub = data.get("amount_rub")
    package_id = data.get("package_id")

    if not stars_amount or not amount_rub:
        await message.answer("Сессия устарела. Начните с /start")
        await state.clear()
        return

    package = None
    async with async_session_factory() as session:
        if package_id:
            package = await get_package_by_id(session, package_id)
        try:
            order = await create_stars_order(
                session,
                buyer_id=buyer_id,
                buyer_username=buyer_username,
                recipient_username=recipient_username,
                stars_amount=stars_amount,
                amount_rub=amount_rub,
                package=package,
            )
        except ValueError as exc:
            await message.answer(str(exc))
            return

    await state.clear()
    payment_url = payment_link_for_order(order)
    await message.answer(
        format_order_summary(order) + "\n\nНажмите «Оплатить» для перехода в Robokassa.",
        reply_markup=payment_keyboard(payment_url),
    )

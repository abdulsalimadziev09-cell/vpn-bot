import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)

from app.bot.admin_text import format_admin_help, is_admin
from app.bot.keyboards import admin_menu_keyboard
from app.config import settings
from app.db.session import async_session_factory
from app.formatters import format_admin_stats, format_order_admin
from app.repositories.stats import get_admin_stats
from app.repositories.orders import get_order_by_id, list_orders_by_status
from app.services.admin_report import send_admin_subscriptions_report
from app.services.payment import approve_manual_order
from app.services.vpn_admin_test import (
    admin_test_provision,
    admin_test_revoke,
    format_admin_vpn_status,
    format_provision_diagnostic,
    parse_admin_test_client_name,
)
from app.services.vpn_delivery import send_vpn_config_files

router = Router()


class AdminApproveStates(StatesGroup):
    waiting_config = State()


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    await message.answer(format_admin_help(), reply_markup=admin_menu_keyboard())


@router.callback_query(lambda c: c.data == "menu:admin")
async def menu_admin(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    await callback.message.edit_text(format_admin_help(), reply_markup=admin_menu_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:orders")
async def admin_orders_button(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    async with async_session_factory() as session:
        paid_orders = await list_orders_by_status(session, "paid")

    if not paid_orders:
        await callback.message.answer("Нет заказов, ожидающих выдачи.")
        await callback.answer()
        return

    chunks = [format_order_admin(order) for order in paid_orders[:20]]
    await callback.message.answer("Заказы, ожидающие выдачи:\n\n" + "\n\n".join(chunks))
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:subscriptions")
async def admin_subscriptions_button(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    await send_admin_subscriptions_report(callback.bot, only_admin_id=callback.from_user.id)
    await callback.answer()


@router.message(Command("admin_subscriptions"))
async def cmd_admin_subscriptions(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    await send_admin_subscriptions_report(message.bot, only_admin_id=message.from_user.id)


@router.message(Command("admin_orders"))
async def cmd_admin_orders(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    async with async_session_factory() as session:
        paid_orders = await list_orders_by_status(session, "paid")

    if not paid_orders:
        await message.answer("Нет заказов, ожидающих выдачи.")
        return

    chunks = [format_order_admin(order) for order in paid_orders[:20]]
    await message.answer("Заказы, ожидающие выдачи:\n\n" + "\n\n".join(chunks))


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    async with async_session_factory() as session:
        stats = await get_admin_stats(session)
    await message.answer(format_admin_stats(stats))


@router.callback_query(lambda c: c.data == "admin:stats")
async def admin_stats_button(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    async with async_session_factory() as session:
        stats = await get_admin_stats(session)
    await callback.message.answer(format_admin_stats(stats))
    await callback.answer()


@router.message(Command("admin_vpn_status"))
async def cmd_admin_vpn_status(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    await message.answer(format_admin_vpn_status())


@router.message(Command("admin_vpn_add"))
async def cmd_admin_vpn_add(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split(maxsplit=1)
    client_name = parse_admin_test_client_name(
        message.from_user.id,
        parts[1].strip() if len(parts) > 1 else None,
    )
    if not client_name:
        await message.answer(
            "Некорректное имя клиента. Допустимо: латиница, цифры, _ и -, до 32 символов.\n"
            "Пример: /admin_vpn_add test_bot"
        )
        return

    await _admin_vpn_add(message, client_name)


@router.message(Command("admin_vpn_remove"))
async def cmd_admin_vpn_remove(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split(maxsplit=1)
    client_name = parse_admin_test_client_name(
        message.from_user.id,
        parts[1].strip() if len(parts) > 1 else None,
    )
    if not client_name:
        await message.answer(
            "Некорректное имя клиента.\n"
            "Пример: /admin_vpn_remove test_bot"
        )
        return

    await _admin_vpn_remove(message, client_name)


@router.callback_query(lambda c: c.data == "admin:vpn_status")
async def admin_vpn_status_button(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    await callback.message.answer(format_admin_vpn_status())
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:vpn_add")
async def admin_vpn_add_button(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    client_name = parse_admin_test_client_name(callback.from_user.id, None)
    assert client_name is not None
    await _admin_vpn_add(callback.message, client_name)
    await callback.answer()


@router.callback_query(lambda c: c.data == "admin:vpn_remove")
async def admin_vpn_remove_button(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    client_name = parse_admin_test_client_name(callback.from_user.id, None)
    assert client_name is not None
    await _admin_vpn_remove(callback.message, client_name)
    await callback.answer()


async def _admin_vpn_add(message: Message, client_name: str) -> None:
    if settings.vpn_provisioner == "manual":
        await message.answer(
            "VPN_PROVISIONER=manual — автовыдача недоступна.\n"
            "Переключите на ssh или amnezia_api для теста."
        )
        return

    await message.answer(f"Создаю клиента {client_name} на VPS…")
    try:
        result = await admin_test_provision(client_name)
    except Exception:
        logger.exception("Admin VPN test provision failed for %s", client_name)
        await message.answer(
            f"Ошибка при создании клиента {client_name}.\n"
            "Проверьте SSH, скрипт и каталог конфигов (/admin_vpn_status)."
        )
        return

    if result.requires_manual or not result.config_text:
        await message.answer("Провижинер вернул пустой конфиг или требует ручной выдачи.")
        return

    await send_vpn_config_files(
        message.bot,
        message.chat.id,
        result.client_name,
        result.config_text,
        header=(
            f"✅ Тест: клиент {result.client_name} создан на VPS.\n\n"
            f"{format_provision_diagnostic(result.config_text)}"
        ),
    )


async def _admin_vpn_remove(message: Message, client_name: str) -> None:
    if settings.vpn_provisioner == "manual":
        await message.answer("VPN_PROVISIONER=manual — удаление через SSH недоступно.")
        return

    await message.answer(f"Удаляю клиента {client_name} с VPS…")
    try:
        await admin_test_revoke(client_name)
    except Exception:
        logger.exception("Admin VPN test revoke failed for %s", client_name)
        await message.answer(f"Ошибка при удалении клиента {client_name}.")
        return

    await message.answer(f"✅ Клиент {client_name} удалён с VPS.")


@router.message(Command("admin_approve"))
async def cmd_admin_approve(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("Использование: /admin_approve <order_id>")
        return

    try:
        order_id = int(parts[1])
    except ValueError:
        await message.answer("order_id должен быть числом.")
        return

    async with async_session_factory() as session:
        order = await get_order_by_id(session, order_id)

    if not order:
        await message.answer("Заказ не найден.")
        return
    if order.status != "paid":
        await message.answer(f"Заказ в статусе {order.status}, ожидается paid.")
        return

    await state.set_state(AdminApproveStates.waiting_config)
    await state.update_data(order_id=order_id)
    await message.answer(
        f"Заказ #{order_id} найден.\n"
        "Отправьте содержимое .conf одним сообщением (текстом или файлом)."
    )


@router.message(AdminApproveStates.waiting_config, F.document)
async def admin_approve_document(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await state.clear()
        return

    file = await message.bot.get_file(message.document.file_id)
    downloaded = await message.bot.download_file(file.file_path)
    config_text = downloaded.read().decode("utf-8")
    await _finalize_approve(message, state, order_id, config_text)


@router.message(AdminApproveStates.waiting_config, F.text)
async def admin_approve_text(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await state.clear()
        return

    if message.text.startswith("/"):
        await message.answer("Ожидается конфиг, не команда. Отправьте .conf содержимое.")
        return

    await _finalize_approve(message, state, order_id, message.text)


async def _finalize_approve(
    message: Message,
    state: FSMContext,
    order_id: int,
    config_text: str,
) -> None:
    async with async_session_factory() as session:
        order = await get_order_by_id(session, order_id)
        if not order:
            await message.answer("Заказ не найден.")
            await state.clear()
            return

        await approve_manual_order(session, message.bot, order, config_text)

    await state.clear()
    await message.answer(f"Заказ #{order_id} выдан пользователю.")

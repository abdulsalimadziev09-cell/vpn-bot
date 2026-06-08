from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from app.bot.formatters import format_item_list
from app.db.session import async_session_factory
from app.repositories.folders import (
    create_folder,
    get_folder_by_id,
    list_folder_items,
    list_user_folders,
    regenerate_invite_token,
    set_active_folder,
    user_can_write_folder,
)
from app.repositories.items import get_or_create_user
from app.services.subscription import is_pro_active, refresh_user_plan

router = Router()


def _folder_required_pro_message() -> str:
    return "Shared-папки доступны на Pro. Подробности: /pro, оформить: /buy"


async def _bot_invite_link(bot: Bot, token: str) -> str:
    me = await bot.get_me()
    username = me.username or "bot"
    return f"https://t.me/{username}?start=folder_{token}"


@router.message(Command("folder"))
async def cmd_folder(message: Message, command: CommandObject, bot: Bot) -> None:
    args = (command.args or "").strip().split()
    if not args:
        await message.answer(
            "Команды папок:\n"
            "/folder create <название>\n"
            "/folder list\n"
            "/folder invite <id>\n"
            "/folder items <id>\n"
            "/folder use <id> — сохранять в папку\n"
            "/folder use off — только личные сохранения"
        )
        return

    action = args[0].lower()

    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        await refresh_user_plan(session, user)

        if action == "create":
            if not is_pro_active(user):
                await message.answer(_folder_required_pro_message())
                return
            if len(args) < 2:
                await message.answer("Использование: /folder create <название>")
                return
            name = " ".join(args[1:])
            folder = await create_folder(session, user.telegram_id, name)
            await session.commit()
            link = await _bot_invite_link(bot, folder.invite_token)
            await message.answer(
                f"Папка «{folder.name}» создана (#{folder.id}).\n"
                f"Пригласить: {link}"
            )
            return

        if action == "list":
            folders = await list_user_folders(session, user.telegram_id)
            if not folders:
                await message.answer("Папок нет. Создай: /folder create Семья")
                return
            active = user.active_folder_id
            lines = ["Твои папки:"]
            for folder in folders:
                mark = " ✓" if folder.id == active else ""
                lines.append(f"#{folder.id} · {folder.name}{mark}")
            await message.answer("\n".join(lines))
            return

        if action == "invite":
            if len(args) < 2 or not args[1].isdigit():
                await message.answer("Использование: /folder invite <id>")
                return
            folder = await get_folder_by_id(session, int(args[1]))
            if not folder or not await user_can_write_folder(session, folder.id, user.telegram_id):
                await message.answer("Папка не найдена или нет доступа.")
                return
            token = await regenerate_invite_token(session, folder)
            await session.commit()
            link = await _bot_invite_link(bot, token)
            await message.answer(f"Ссылка-приглашение в «{folder.name}»:\n{link}")
            return

        if action == "items":
            if len(args) < 2 or not args[1].isdigit():
                await message.answer("Использование: /folder items <id>")
                return
            folder_id = int(args[1])
            folder = await get_folder_by_id(session, folder_id)
            if not folder:
                await message.answer("Папка не найдена.")
                return
            items = await list_folder_items(session, folder_id)
            await message.answer(f"Папка «{folder.name}»:\n" + format_item_list(items))
            return

        if action == "use":
            if len(args) < 2:
                await message.answer("Использование: /folder use <id> | /folder use off")
                return
            if args[1].lower() == "off":
                await set_active_folder(session, user, None)
                await session.commit()
                await message.answer("Сохранения снова только личные.")
                return
            if not args[1].isdigit():
                await message.answer("ID папки должен быть числом.")
                return
            folder_id = int(args[1])
            if not is_pro_active(user):
                await message.answer(_folder_required_pro_message())
                return
            try:
                await set_active_folder(session, user, folder_id)
            except PermissionError:
                await message.answer("Нет доступа к этой папке.")
                return
            folder = await get_folder_by_id(session, folder_id)
            await session.commit()
            await message.answer(f"Новые сохранения пойдут в папку «{folder.name}» (#{folder.id}).")
            return

        await message.answer("Неизвестная подкоманда. /folder — справка.")


@router.callback_query(F.data.startswith("folder_save:"))
async def cb_folder_save(callback: CallbackQuery) -> None:
    folder_id = int(callback.data.split(":", maxsplit=1)[1])
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
        )
        await refresh_user_plan(session, user)
        if not is_pro_active(user):
            await callback.answer("Нужен Pro", show_alert=True)
            return
        try:
            await set_active_folder(session, user, folder_id)
        except PermissionError:
            await callback.answer("Нет доступа", show_alert=True)
            return
        folder = await get_folder_by_id(session, folder_id)
        await session.commit()

    await callback.answer(f"Папка: {folder.name}")
    if callback.message:
        await callback.message.answer(f"Сохранения пойдут в «{folder.name}» (#{folder.id}).")

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from app.bot.keyboards import main_menu_keyboard
from app.db.session import async_session_factory
from app.repositories.folders import join_folder_by_token
from app.repositories.items import get_or_create_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject) -> None:
    payload = (command.args or "").strip()
    if payload.startswith("folder_"):
        token = payload.removeprefix("folder_")
        async with async_session_factory() as session:
            user = await get_or_create_user(
                session,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )
            folder = await join_folder_by_token(session, user.telegram_id, token)
            await session.commit()

        if not folder:
            await message.answer("Ссылка-приглашение недействительна или устарела.")
            return
        await message.answer(
            f"Ты в папке «{folder.name}» (#{folder.id}).\n"
            "Смотреть записи: /folder items {id}\n"
            "Сохранять сюда (Pro): /folder use {id}".format(id=folder.id)
        )
        return

    await message.answer(
        "Привет! Я сохраняю ссылки, посты и голосовые — чтобы ничего не потерять.\n\n"
        "Просто перешли мне сообщение или отправь ссылку/текст.\n"
        "Теги: #работа в тексте или кнопка «+ Тег».\n"
        "Напоминания: «напомни через 2 дня» в тексте или голосовом.\n"
        "Инбокс: /inbox · Утренний обзор: /daily (каждое утро автоматически)\n"
        "Статусы: кнопки под карточкой или /done /archive\n"
        "Pro: /pro · Папки: /folder · Оплата: /buy\n"
        "Команды: /list, /search, /tags, /item <id>, /remind <id> 2d, /delete <id>",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, command: CommandObject) -> None:
    await cmd_start(message, command)

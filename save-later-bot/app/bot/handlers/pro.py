from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import settings
from app.db.session import async_session_factory
from app.repositories.items import get_or_create_user
from app.services.subscription import count_user_items, format_plan_status, item_limit_for_user, refresh_user_plan

router = Router()


@router.message(Command("pro"))
async def cmd_pro(message: Message) -> None:
    async with async_session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )
        await refresh_user_plan(session, user)
        count = await count_user_items(session, user.telegram_id)
        await session.commit()

    limit = item_limit_for_user(user)
    lines = [
        f"Тариф: {format_plan_status(user)}",
        f"Сохранений: {count} / {limit}",
        "",
        "Pro даёт:",
        f"• до {settings.pro_item_limit} сохранений",
        "• умный поиск (семантика + FTS)",
        "• shared-папки для пары/семьи",
        "",
    ]
    if settings.payments_enabled:
        lines.append(f"Оформить: /buy ({settings.pro_stars_price}⭐ на {settings.pro_days} дн.)")
    else:
        lines.append("Оплата отключена (payments_enabled=false).")

    await message.answer("\n".join(lines))

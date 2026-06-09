from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import User


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        if username and user.username != username:
            user.username = username
        return user

    user = User(
        telegram_id=telegram_id,
        username=username,
        is_admin=telegram_id in settings.admin_ids,
    )
    session.add(user)
    await session.flush()
    return user


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    normalized = username.strip().removeprefix("@").lower()
    if not normalized:
        return None
    result = await session.execute(select(User))
    for user in result.scalars().all():
        if user.username and user.username.lower() == normalized:
            return user
    return None

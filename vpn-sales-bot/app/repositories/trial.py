from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.subscriptions import get_active_subscription
from app.repositories.users import get_user


async def can_start_trial(session: AsyncSession, telegram_id: int) -> bool:
    user = await get_user(session, telegram_id)
    if user is None or user.trial_used:
        return False
    if await get_active_subscription(session, telegram_id):
        return False
    return True

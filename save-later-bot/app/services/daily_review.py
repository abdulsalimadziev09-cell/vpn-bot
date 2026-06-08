from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Item, ItemStatus, UserEvent

# Readwise-style resurface windows: (days_ago, label)
SPOTLIGHT_WINDOWS: list[tuple[int, str]] = [
    (365, "Год назад"),
    (180, "Полгода назад"),
    (90, "3 месяца назад"),
    (30, "Месяц назад"),
    (7, "Неделю назад"),
]

SPOTLIGHT_COOLDOWN_DAYS = 60


@dataclass
class DailyReviewContent:
    text: str
    spotlight_item: Item | None = None
    spotlight_label: str | None = None
    backlog_item: Item | None = None
    unread_count: int = 0


def _item_title(item: Item, max_len: int = 80) -> str:
    title = item.title or item.url or item.transcription or "без названия"
    if len(title) > max_len:
        return title[: max_len - 1] + "…"
    return title


async def _recently_spotlighted_ids(
    session: AsyncSession,
    user_id: int,
    now: datetime,
) -> set[int]:
    since = now - timedelta(days=SPOTLIGHT_COOLDOWN_DAYS)
    stmt = (
        select(UserEvent)
        .where(
            UserEvent.user_id == user_id,
            UserEvent.event_type == "daily_review_spotlight",
            UserEvent.created_at >= since,
        )
    )
    result = await session.execute(stmt)
    ids: set[int] = set()
    for event in result.scalars().all():
        if event.payload and "item_id" in event.payload:
            ids.add(int(event.payload["item_id"]))
    return ids


async def _find_spotlight_item(
    session: AsyncSession,
    user_id: int,
    now: datetime,
    excluded_ids: set[int],
) -> tuple[Item | None, str | None]:
    for days_ago, label in SPOTLIGHT_WINDOWS:
        center = now - timedelta(days=days_ago)
        window_start = center - timedelta(days=2)
        window_end = center + timedelta(days=2)
        stmt = (
            select(Item)
            .options(selectinload(Item.tags))
            .where(
                Item.user_id == user_id,
                Item.created_at >= window_start,
                Item.created_at <= window_end,
            )
            .order_by(Item.created_at.asc())
            .limit(10)
        )
        result = await session.execute(stmt)
        candidates = [i for i in result.scalars().all() if i.id not in excluded_ids]
        if candidates:
            return candidates[0], label
    return None, None


async def _find_backlog_item(session: AsyncSession, user_id: int) -> tuple[Item | None, int]:
    unread_statuses = [ItemStatus.INBOX, ItemStatus.READING]
    count_stmt = (
        select(func.count())
        .select_from(Item)
        .where(Item.user_id == user_id, Item.status.in_(unread_statuses))
    )
    unread_count = (await session.execute(count_stmt)).scalar_one()
    if unread_count == 0:
        return None, 0

    stmt = (
        select(Item)
        .options(selectinload(Item.tags))
        .where(Item.user_id == user_id, Item.status == ItemStatus.INBOX)
        .order_by(Item.created_at.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()
    if item:
        return item, unread_count

    stmt = (
        select(Item)
        .options(selectinload(Item.tags))
        .where(Item.user_id == user_id, Item.status == ItemStatus.READING)
        .order_by(Item.created_at.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none(), unread_count


async def build_daily_review(session: AsyncSession, user_id: int) -> DailyReviewContent | None:
    now = datetime.now(timezone.utc)

    total_stmt = select(func.count()).select_from(Item).where(Item.user_id == user_id)
    total_items = (await session.execute(total_stmt)).scalar_one()
    if total_items == 0:
        return None

    excluded = await _recently_spotlighted_ids(session, user_id, now)
    spotlight, spotlight_label = await _find_spotlight_item(session, user_id, now, excluded)
    backlog, unread_count = await _find_backlog_item(session, user_id)

    if not spotlight and unread_count == 0:
        return None

    lines = ["☀️ Утренний обзор", ""]

    if spotlight and spotlight_label:
        lines.append("📚 Из архива")
        lines.append(f"{spotlight_label} вы сохранили:")
        lines.append(f"«{_item_title(spotlight)}»")
        lines.append("")

    if unread_count > 0 and backlog:
        lines.append(f"📥 Ещё не прочитано: {unread_count}")
        lines.append("Дольше всего ждёт:")
        lines.append(f"«{_item_title(backlog)}»")
        lines.append("")
        lines.append("/inbox — разобрать всё")

    return DailyReviewContent(
        text="\n".join(lines).strip(),
        spotlight_item=spotlight,
        spotlight_label=spotlight_label,
        backlog_item=backlog,
        unread_count=unread_count,
    )

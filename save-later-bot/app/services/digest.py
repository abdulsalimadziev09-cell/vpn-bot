from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Item, ItemStatus, Tag
from app.repositories.analytics import count_events


async def build_weekly_digest(session: AsyncSession, user_id: int) -> str | None:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    saves_count = await count_events(session, user_id, "item_saved", week_ago)
    if saves_count == 0:
        return None

    inbox_stmt = (
        select(func.count())
        .select_from(Item)
        .where(Item.user_id == user_id, Item.status == ItemStatus.INBOX)
    )
    inbox_count = (await session.execute(inbox_stmt)).scalar_one()

    top_tags_stmt = (
        select(Tag.name, func.count(Item.id))
        .join(Tag.items)
        .join(Item)
        .where(Item.user_id == user_id, Item.created_at >= week_ago)
        .group_by(Tag.name)
        .order_by(func.count(Item.id).desc())
        .limit(3)
    )
    top_tags = (await session.execute(top_tags_stmt)).all()

    revisit_stmt = (
        select(Item)
        .options(selectinload(Item.tags))
        .where(
            Item.user_id == user_id,
            Item.status.in_([ItemStatus.INBOX, ItemStatus.READING]),
            Item.created_at < week_ago,
        )
        .order_by(Item.created_at.asc())
        .limit(3)
    )
    revisit_items = list((await session.execute(revisit_stmt)).scalars().all())

    lines = [
        "📬 Еженедельный дайджест",
        f"За неделю сохранено: {saves_count}",
        f"В инбоксе сейчас: {inbox_count}",
    ]
    if top_tags:
        tags_str = ", ".join(f"#{name} ({cnt})" for name, cnt in top_tags)
        lines.append(f"Топ-темы: {tags_str}")
    if revisit_items:
        lines.append("\nСтоит перечитать:")
        for item in revisit_items:
            title = item.title or item.url or "без названия"
            if len(title) > 50:
                title = title[:47] + "…"
            lines.append(f"• #{item.id} {title}")
    lines.append("\n/inbox — разобрать инбокс")
    return "\n".join(lines)

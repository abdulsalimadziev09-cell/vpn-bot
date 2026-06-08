from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Item, ItemStatus, Reminder, Tag, User
from app.repositories.folders import get_membership
from app.services.extractor import SavePayload
from app.services.search import update_item_search_vector
from app.services.tag_suggester import merge_tags


async def get_or_create_user(session: AsyncSession, telegram_id: int, username: str | None) -> User:
    user = await session.get(User, telegram_id)
    if user:
        if username and user.username != username:
            user.username = username
        return user
    user = User(telegram_id=telegram_id, username=username)
    session.add(user)
    await session.flush()
    return user


async def find_duplicate_by_url(
    session: AsyncSession,
    user_id: int,
    url: str,
    within_hours: int = 24,
) -> Item | None:
    since = datetime.now(timezone.utc) - timedelta(hours=within_hours)
    stmt = (
        select(Item)
        .options(selectinload(Item.tags))
        .where(Item.user_id == user_id, Item.url == url, Item.created_at >= since)
        .order_by(Item.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_tag(session: AsyncSession, user_id: int, name: str) -> Tag:
    normalized = name.lower().strip()
    stmt = select(Tag).where(Tag.user_id == user_id, Tag.name == normalized)
    result = await session.execute(stmt)
    tag = result.scalar_one_or_none()
    if tag:
        return tag
    tag = Tag(user_id=user_id, name=normalized)
    session.add(tag)
    await session.flush()
    return tag


async def attach_tags(session: AsyncSession, item: Item, tag_names: list[str]) -> Item:
    for name in tag_names:
        tag = await get_or_create_tag(session, user_id=item.user_id, name=name)
        if tag not in item.tags:
            item.tags.append(tag)
    await session.flush()
    await update_item_search_vector(session, item)
    return item


async def create_item(
    session: AsyncSession,
    user_id: int,
    payload: SavePayload,
    suggested_tags: list[str] | None = None,
    folder_id: int | None = None,
    collection_id: int | None = None,
) -> Item:
    all_tags = merge_tags(payload.hashtags, suggested_tags or [])
    item = Item(
        user_id=user_id,
        folder_id=folder_id,
        collection_id=collection_id,
        status=ItemStatus.INBOX,
        type=payload.item_type,
        title=payload.title,
        body=payload.body,
        url=payload.url,
        source_chat=payload.source_chat,
        telegram_message_id=payload.telegram_message_id,
        transcription=payload.transcription,
    )
    session.add(item)
    await session.flush()
    if all_tags:
        await attach_tags(session, item, all_tags)
    else:
        await update_item_search_vector(session, item)
    return item


async def get_item(session: AsyncSession, user_id: int, item_id: int) -> Item | None:
    item = await get_item_accessible(session, user_id, item_id)
    return item


async def get_item_accessible(session: AsyncSession, user_id: int, item_id: int) -> Item | None:
    stmt = (
        select(Item)
        .options(selectinload(Item.tags), selectinload(Item.collection))
        .where(Item.id == item_id)
    )
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        return None
    if item.user_id == user_id:
        return item
    if item.folder_id and await get_membership(session, item.folder_id, user_id):
        return item
    return None


async def list_items(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
    status: str | None = None,
) -> list[Item]:
    stmt = (
        select(Item)
        .options(selectinload(Item.tags), selectinload(Item.collection))
        .where(Item.user_id == user_id)
        .order_by(Item.created_at.desc())
        .limit(limit)
    )
    if status:
        stmt = stmt.where(Item.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_item_status(
    session: AsyncSession,
    user_id: int,
    item_id: int,
    status: str,
) -> Item | None:
    item = await get_item_accessible(session, user_id, item_id)
    if not item:
        return None
    item.status = status
    item.status_changed_at = datetime.now(timezone.utc)
    await session.flush()
    return item


async def delete_item(session: AsyncSession, user_id: int, item_id: int) -> bool:
    item = await get_item(session, user_id, item_id)
    if not item:
        return False
    await session.delete(item)
    await session.flush()
    return True


async def list_tags_with_counts(session: AsyncSession, user_id: int) -> list[tuple[str, int]]:
    stmt = (
        select(Tag.name, func.count(Item.id))
        .join(Tag.items)
        .where(Tag.user_id == user_id)
        .group_by(Tag.name)
        .order_by(func.count(Item.id).desc(), Tag.name)
    )
    result = await session.execute(stmt)
    return [(name, count) for name, count in result.all()]


async def create_reminder(
    session: AsyncSession,
    user_id: int,
    item_id: int,
    remind_at: datetime,
) -> Reminder:
    reminder = Reminder(item_id=item_id, user_id=user_id, remind_at=remind_at)
    session.add(reminder)
    await session.flush()
    return reminder


async def get_pending_reminders(session: AsyncSession, now: datetime) -> list[Reminder]:
    stmt = (
        select(Reminder)
        .options(selectinload(Reminder.item).selectinload(Item.tags))
        .where(Reminder.sent_at.is_(None), Reminder.remind_at <= now)
        .order_by(Reminder.remind_at)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def mark_reminder_sent(session: AsyncSession, reminder: Reminder) -> None:
    reminder.sent_at = datetime.now(timezone.utc)

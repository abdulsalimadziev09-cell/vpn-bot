from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Item, Tag
from app.services.embeddings import EmbeddingService, semantic_search_items
from app.services.extractor import build_search_text


async def update_item_search_vector(session: AsyncSession, item: Item) -> None:
    tag_names = [t.name for t in item.tags]
    search_text = build_search_text(
        item.title,
        item.body,
        item.url,
        item.transcription,
        tag_names,
        item.summary,
    )
    if not search_text.strip():
        item.search_vector = None
        return
    result = await session.execute(
        text("SELECT to_tsvector('russian', :txt)"),
        {"txt": search_text},
    )
    item.search_vector = result.scalar_one()


async def search_items_fts(
    session: AsyncSession,
    user_id: int,
    query: str,
    limit: int = 10,
) -> list[Item]:
    query = query.strip()
    if not query:
        return []

    stmt = (
        select(Item)
        .options(selectinload(Item.tags))
        .where(Item.user_id == user_id)
        .order_by(Item.created_at.desc())
        .limit(limit)
    )

    fts_stmt = (
        select(Item)
        .options(selectinload(Item.tags))
        .where(Item.user_id == user_id)
        .where(
            Item.search_vector.op("@@")(func.plainto_tsquery("russian", query))
        )
        .order_by(func.ts_rank(Item.search_vector, func.plainto_tsquery("russian", query)).desc())
        .limit(limit)
    )
    result = await session.execute(fts_stmt)
    items = list(result.scalars().all())

    if items:
        return items

    like_pattern = f"%{query}%"
    fallback_stmt = stmt.where(
        or_(
            Item.title.ilike(like_pattern),
            Item.body.ilike(like_pattern),
            Item.url.ilike(like_pattern),
            Item.transcription.ilike(like_pattern),
            Item.tags.any(Tag.name.ilike(like_pattern)),
        )
    )
    result = await session.execute(fallback_stmt)
    return list(result.scalars().unique().all())


def _merge_results(primary: list[Item], secondary: list[Item], limit: int) -> list[Item]:
    seen: set[int] = set()
    merged: list[Item] = []
    for item in primary + secondary:
        if item.id in seen:
            continue
        seen.add(item.id)
        merged.append(item)
        if len(merged) >= limit:
            break
    return merged


async def search_items(
    session: AsyncSession,
    user_id: int,
    query: str,
    limit: int = 10,
    *,
    use_semantic: bool = False,
    embedding_service: EmbeddingService | None = None,
) -> list[Item]:
    fts_items = await search_items_fts(session, user_id, query, limit=limit)
    if not use_semantic or not embedding_service or not embedding_service.enabled:
        return fts_items

    try:
        semantic_items = await semantic_search_items(
            session,
            user_id,
            query,
            embedding_service,
            limit=limit,
        )
    except Exception:
        return fts_items

    return _merge_results(semantic_items, fts_items, limit)

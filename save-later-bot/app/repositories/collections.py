from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Collection

PRESET_COLLECTIONS: list[tuple[str, str]] = [
    ("read-later", "Read Later"),
    ("startup-ideas", "Startup Ideas"),
    ("books", "Books"),
    ("travel", "Travel"),
    ("buy-later", "Buy Later"),
    ("research", "Research"),
]

PRESET_KEYWORDS: dict[str, list[str]] = {
    "read-later": [],
    "startup-ideas": ["startup", "идея", "бизнес", "saas", "mvp"],
    "books": ["book", "книга", "reading", "author", "автор"],
    "travel": ["travel", "путешеств", "отель", "рейс", "flight", "hotel"],
    "buy-later": ["купить", "buy", "price", "shop", "amazon", "ozon"],
    "research": ["research", "paper", "study", "исследован", "arxiv", "habr"],
}

PRESET_DOMAINS: dict[str, list[str]] = {
    "read-later": ["medium.com", "substack.com", "habr.com"],
    "startup-ideas": ["ycombinator.com", "producthunt.com"],
    "books": ["goodreads.com"],
    "travel": ["booking.com", "airbnb.com"],
    "buy-later": ["amazon.", "ozon.ru", "wildberries"],
    "research": ["arxiv.org", "scholar.google", "researchgate.net"],
}


async def ensure_preset_collections(session: AsyncSession, user_id: int) -> list[Collection]:
    stmt = select(Collection).where(Collection.user_id == user_id, Collection.is_preset.is_(True))
    result = await session.execute(stmt)
    existing = {c.slug: c for c in result.scalars().all()}
    created: list[Collection] = []
    for slug, name in PRESET_COLLECTIONS:
        if slug in existing:
            created.append(existing[slug])
            continue
        col = Collection(user_id=user_id, slug=slug, name=name, is_preset=True)
        session.add(col)
        created.append(col)
    await session.flush()
    return created


async def get_collection_by_slug(session: AsyncSession, user_id: int, slug: str) -> Collection | None:
    stmt = select(Collection).where(Collection.user_id == user_id, Collection.slug == slug)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_collections(session: AsyncSession, user_id: int) -> list[Collection]:
    await ensure_preset_collections(session, user_id)
    stmt = select(Collection).where(Collection.user_id == user_id).order_by(Collection.is_preset.desc(), Collection.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())

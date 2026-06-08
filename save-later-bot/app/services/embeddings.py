import logging

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Item, ItemEmbedding
from app.services.extractor import build_search_text

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    pass


class EmbeddingService:
    def __init__(self) -> None:
        self._api_key = settings.openai_api_key or settings.whisper_api_key
        self._base_url = settings.openai_base_url.rstrip("/")
        self._model = settings.embedding_model

    @property
    def enabled(self) -> bool:
        return bool(self._api_key)

    async def embed_text(self, text: str) -> list[float]:
        if not self.enabled:
            raise EmbeddingError("OpenAI API key not configured")
        text = text.strip()
        if not text:
            raise EmbeddingError("Empty text for embedding")

        url = f"{self._base_url}/embeddings"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {"model": self._model, "input": text[:8000]}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            logger.error("Embeddings API error: %s %s", response.status_code, response.text)
            raise EmbeddingError(f"Embeddings API returned {response.status_code}")

        data = response.json()
        return data["data"][0]["embedding"]

    async def upsert_item_embedding(self, session: AsyncSession, item: Item) -> None:
        tag_names = [t.name for t in item.tags]
        text = build_search_text(
        item.title,
        item.body,
        item.url,
        item.transcription,
        tag_names,
        item.summary,
    )
        if not text.strip():
            return
        vector = await self.embed_text(text)
        existing = await session.get(ItemEmbedding, item.id)
        if existing:
            existing.embedding = vector
        else:
            session.add(ItemEmbedding(item_id=item.id, embedding=vector))
        await session.flush()


async def semantic_search_items(
    session: AsyncSession,
    user_id: int,
    query: str,
    embedding_service: EmbeddingService,
    limit: int = 10,
) -> list[Item]:
    if not embedding_service.enabled:
        return []
    query_vector = await embedding_service.embed_text(query)

    stmt = (
        select(Item)
        .options(selectinload(Item.tags))
        .join(ItemEmbedding, ItemEmbedding.item_id == Item.id)
        .where(Item.user_id == user_id)
        .order_by(ItemEmbedding.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().unique().all())


async def delete_item_embedding(session: AsyncSession, item_id: int) -> None:
    await session.execute(delete(ItemEmbedding).where(ItemEmbedding.item_id == item_id))

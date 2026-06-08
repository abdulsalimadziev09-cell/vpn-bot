from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Item, User
from app.repositories.analytics import track_event
from app.repositories.collections import ensure_preset_collections, get_collection_by_slug
from app.repositories.folders import get_folder_by_id
from app.repositories.items import (
    attach_tags,
    create_item,
    create_reminder,
    find_duplicate_by_url,
)
from app.services.collections import suggest_collection_slug
from app.services.embeddings import EmbeddingService
from app.services.extractor import SavePayload
from app.services.search import update_item_search_vector
from app.services.subscription import count_user_items, is_pro_active, item_limit_for_user, refresh_user_plan
from app.services.url_summary import fetch_url_metadata, generate_llm_summary


@dataclass
class SaveResult:
    item: Item | None = None
    duplicate: bool = False
    limit_reached: bool = False
    folder_name: str | None = None
    collection_name: str | None = None


class SaveOrchestrator:
    def __init__(self, embeddings: EmbeddingService | None = None) -> None:
        self._embeddings = embeddings or EmbeddingService()

    async def save(
        self,
        session: AsyncSession,
        user: User,
        payload: SavePayload,
        suggested_tags: list[str],
        remind_at: datetime | None = None,
    ) -> SaveResult:
        await refresh_user_plan(session, user)
        count = await count_user_items(session, user.telegram_id)
        if count >= item_limit_for_user(user):
            return SaveResult(limit_reached=True)

        if payload.url:
            duplicate = await find_duplicate_by_url(session, user.telegram_id, payload.url)
            if duplicate:
                await track_event(session, user.telegram_id, "duplicate_url", {"item_id": duplicate.id})
                return SaveResult(item=duplicate, duplicate=True)

        folder_id = user.active_folder_id if is_pro_active(user) else None
        folder_name = None
        if folder_id:
            folder = await get_folder_by_id(session, folder_id)
            folder_name = folder.name if folder else None

        collection_id = None
        collection_name = None
        slug = suggest_collection_slug(payload.title, payload.body, payload.url, payload.transcription)
        if slug:
            await ensure_preset_collections(session, user.telegram_id)
            collection = await get_collection_by_slug(session, user.telegram_id, slug)
            if collection:
                collection_id = collection.id
                collection_name = collection.name

        if payload.url:
            meta = await fetch_url_metadata(payload.url)
            if meta.title and not payload.title:
                payload.title = meta.title[:512]
            if meta.description and not payload.body:
                payload.body = meta.description
            summary = meta.description
            if is_pro_active(user):
                llm = await generate_llm_summary(meta.title, meta.description, payload.url)
                if llm:
                    summary = llm
        else:
            meta = None
            summary = None

        item = await create_item(
            session,
            user.telegram_id,
            payload,
            suggested_tags,
            folder_id=folder_id,
            collection_id=collection_id,
        )
        if payload.url and meta:
            item.summary = summary
            item.reading_time_minutes = meta.reading_time_minutes
            await update_item_search_vector(session, item)

        if remind_at is not None:
            await create_reminder(session, user.telegram_id, item.id, remind_at)

        if is_pro_active(user) and self._embeddings.enabled:
            try:
                await self._embeddings.upsert_item_embedding(session, item)
            except Exception:
                pass

        await track_event(
            session,
            user.telegram_id,
            "item_saved",
            {"item_id": item.id, "type": payload.item_type, "collection": collection_name},
        )
        return SaveResult(
            item=item,
            folder_name=folder_name,
            collection_name=collection_name,
        )

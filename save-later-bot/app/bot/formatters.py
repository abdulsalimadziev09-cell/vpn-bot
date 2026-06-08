from app.db.models import Item

TYPE_LABELS = {
    "link": "ссылка",
    "text": "текст",
    "forward": "пересланное",
    "voice": "голосовое",
}

STATUS_LABELS = {
    "inbox": "инбокс",
    "reading": "читаю",
    "done": "готово",
    "archived": "архив",
}


def format_tags(item: Item) -> str:
    if not item.tags:
        return "—"
    return " ".join(f"#{t.name}" for t in item.tags)


def format_item_card(
    item: Item,
    *,
    header: str = "Сохранено",
    folder_name: str | None = None,
    collection_name: str | None = None,
) -> str:
    type_label = TYPE_LABELS.get(item.type, item.type)
    status_label = STATUS_LABELS.get(item.status, item.status)
    lines = [f"{header} #{item.id} · {type_label} · {status_label}"]

    if collection_name or (item.collection and item.collection.name):
        col = collection_name or item.collection.name
        lines.append(f"📂 {col}")
    if folder_name:
        lines.append(f"📁 папка: {folder_name}")
    if item.title:
        lines.append(f"📌 {item.title}")
    if item.source_chat:
        lines.append(f"↪️ из: {item.source_chat}")
    if item.url:
        lines.append(f"🔗 {item.url}")
    if item.reading_time_minutes:
        lines.append(f"⏱ ~{item.reading_time_minutes} мин")
    if item.summary:
        preview = item.summary[:300]
        if len(item.summary) > 300:
            preview += "…"
        lines.append(f"📝 {preview}")
    if item.body and item.body != item.title and item.body != item.summary:
        preview = item.body[:300]
        if len(item.body) > 300:
            preview += "…"
        lines.append(preview)
    if item.transcription:
        preview = item.transcription[:300]
        if len(item.transcription) > 300:
            preview += "…"
        lines.append(f"🎙 {preview}")

    lines.append(f"🏷 {format_tags(item)}")
    return "\n".join(lines)


def format_item_list(items: list[Item]) -> str:
    if not items:
        return "Пока ничего не сохранено. Перешли мне ссылку, пост или голосовое."
    lines = ["Последние сохранения:"]
    for item in items:
        title = item.title or item.url or item.transcription or "без названия"
        if len(title) > 60:
            title = title[:57] + "…"
        tags = format_tags(item)
        status = STATUS_LABELS.get(item.status, item.status)
        lines.append(f"#{item.id} · [{status}] {title}\n   {tags}")
    return "\n".join(lines)


def format_tags_list(tag_counts: list[tuple[str, int]]) -> str:
    if not tag_counts:
        return "Тегов пока нет. Добавь через #тег в сообщении или кнопку «+ Тег»."
    lines = ["Твои теги:"]
    for name, count in tag_counts:
        lines.append(f"#{name} — {count}")
    return "\n".join(lines)


def format_search_results(items: list[Item], query: str, *, smart: bool = False) -> str:
    if not items:
        hint = " (Pro: умный поиск — /pro)" if not smart else ""
        return f"По запросу «{query}» ничего не нашёл.{hint}"
    mode = "умный поиск" if smart else "поиск"
    lines = [f"Найдено ({mode}) по «{query}»:"]
    for item in items:
        title = item.title or item.url or item.transcription or "без названия"
        if len(title) > 60:
            title = title[:57] + "…"
        lines.append(f"#{item.id} · {title}")
    return "\n".join(lines)

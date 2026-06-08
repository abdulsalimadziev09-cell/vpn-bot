from urllib.parse import urlparse

from app.repositories.collections import PRESET_DOMAINS, PRESET_KEYWORDS


def suggest_collection_slug(
    title: str | None,
    body: str | None,
    url: str | None,
    transcription: str | None,
) -> str | None:
    text = " ".join(p for p in [title, body, transcription] if p).lower()
    domain = ""
    if url:
        domain = urlparse(url).netloc.lower()

    best_slug: str | None = None
    best_score = 0

    for slug, keywords in PRESET_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in text:
                score += 2
        for d in PRESET_DOMAINS.get(slug, []):
            if d in domain:
                score += 3
        if score > best_score:
            best_score = score
            best_slug = slug

    if best_score == 0 and url:
        return "read-later"
    return best_slug if best_score > 0 else None

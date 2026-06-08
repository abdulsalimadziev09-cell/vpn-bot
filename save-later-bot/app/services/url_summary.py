import logging
import re
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OG_TITLE_RE = re.compile(
    r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
OG_DESC_RE = re.compile(
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
TITLE_RE = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE)


@dataclass
class UrlMetadata:
    title: str | None = None
    description: str | None = None
    summary: str | None = None
    reading_time_minutes: int | None = None


def estimate_reading_time(text: str) -> int:
    words = len(re.findall(r"\w+", text))
    return max(1, round(words / 200))


async def fetch_url_metadata(url: str) -> UrlMetadata:
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "SaveLaterBot/1.0"})
        if response.status_code >= 400:
            return UrlMetadata()
        html = response.text[:50_000]
    except Exception as exc:
        logger.warning("URL fetch failed for %s: %s", url, exc)
        return UrlMetadata()

    og_title = OG_TITLE_RE.search(html)
    og_desc = OG_DESC_RE.search(html)
    title_tag = TITLE_RE.search(html)

    title = (og_title.group(1) if og_title else None) or (title_tag.group(1).strip() if title_tag else None)
    description = og_desc.group(1).strip() if og_desc else None
    reading_time = estimate_reading_time(description or title or "")

    return UrlMetadata(title=title, description=description, reading_time_minutes=reading_time)


async def generate_llm_summary(title: str | None, description: str | None, url: str) -> str | None:
    api_key = settings.openai_api_key or settings.whisper_api_key
    if not api_key:
        return None

    prompt = (
        f"URL: {url}\nTitle: {title or 'N/A'}\nDescription: {description or 'N/A'}\n\n"
        "Дай краткое резюме на русском (3 пункта), зачем сохранить эту ссылку."
    )
    endpoint = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
        if response.status_code != 200:
            return description
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.exception("LLM summary failed")
        return description

import re
from urllib.parse import urlparse

DOMAIN_TAG_MAP = {
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "github.com": "github",
    "habr.com": "habr",
    "medium.com": "medium",
    "t.me": "telegram",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "reddit.com": "reddit",
}

STOP_WORDS = {
    "и", "в", "на", "с", "по", "для", "как", "что", "это", "the", "a", "an", "to", "of", "in",
}


def suggest_from_url(url: str | None) -> list[str]:
    if not url:
        return []
    parsed = urlparse(url)
    domain = parsed.netloc.removeprefix("www.").lower()
    tags: list[str] = []
    if domain in DOMAIN_TAG_MAP:
        tags.append(DOMAIN_TAG_MAP[domain])
    else:
        root = domain.split(".")[0]
        if root and len(root) >= 3:
            tags.append(root)
    return tags


def suggest_from_title(title: str | None, limit: int = 3) -> list[str]:
    if not title:
        return []
    words = re.findall(r"[\w\u0400-\u04FF]+", title.lower())
    tags: list[str] = []
    for word in words:
        if len(word) < 4 or word in STOP_WORDS:
            continue
        if word not in tags:
            tags.append(word)
        if len(tags) >= limit:
            break
    return tags


def merge_tags(*tag_lists: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for lst in tag_lists:
        for tag in lst:
            normalized = tag.lower().strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
    return result

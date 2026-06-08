from app.services.collections import suggest_collection_slug


def test_suggest_read_later_for_medium() -> None:
    slug = suggest_collection_slug(
        title="Article",
        body=None,
        url="https://medium.com/post",
        transcription=None,
    )
    assert slug == "read-later"


def test_suggest_startup_ideas() -> None:
    slug = suggest_collection_slug(
        title="New startup idea for SaaS",
        body=None,
        url=None,
        transcription=None,
    )
    assert slug == "startup-ideas"


def test_suggest_none_for_plain_text() -> None:
    slug = suggest_collection_slug(
        title="привет",
        body="как дела",
        url=None,
        transcription=None,
    )
    assert slug is None
